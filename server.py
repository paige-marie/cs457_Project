import socket
import argparse
import selectors
import types
import random
import rsa
import traceback

is_server = True 
import protocols
protocols.IS_SERVER = is_server
from Player import Player
from Board import Board
from simulate_certificate_authority import CertificateAuthority

ca = CertificateAuthority(is_server)

SEL = selectors.DefaultSelector()
SERVER_CONTEXT = {
    'conn_ct' : 0, # the total number of connections, incremented at accapt
    'reg_ct' : 0, # the number of players who have registered, incremented after the registration was successful
    'homeless' : [], # connections that haven't been added to the game
    'server_socket' : socket.socket()
}

GAME_CONTEXT = {
    'cur_player' : 0, # the index (in connections) of the player whom the server is waiting for a move from
    'connections' : [], # a list of the selector keys associated with client sockets
    'board' : None # the board, which represents the gameplay state
}

DEFAULT_PORT = 55668

def main():
    """THE MAIN EVENT"""
    try:
        check_sockets()
    except KeyboardInterrupt:
        protocols.print_and_log("caught keyboard interrupt, exiting")
    except Exception as e:
        protocols.print_and_log("Server encountered an error. Exiting")
        # protocols.print_and_log(e)
        traceback.print_exc()
    finally:
        protocols.print_and_log("Server shutting down")
        print("closing socket")
        SERVER_CONTEXT['server_socket'].close()
        SEL.close()

def handle_events(message, key):
    """based on the proto number, route incoming client messages to the correct handling"""
    message_type = message['proto']
    match message_type:
        case protocols.Protocols.REGISTER_CLIENT:
            register_a_player(message, key)
        case protocols.Protocols.MAKE_MOVE:
            make_players_move(message, key)

def register_a_player(message, key):
    """register a player with the server as waiting for a game, including associating their socket to their public key for decryption"""
    #TODO add signature verification
    verified = ca.verify_signature(message['pub_key'], message['signature'])
    protocols.print_and_log(f'Key verified: {verified}')
    if not verified: 
        # close connection to client who we can't verify
        protocols.print_and_log("Close connection to client with unverified key")
        error_bytes = protocols.make_json_bytes(protocols.error_response(protocols.Errors.PUBLIC_KEY_NOT_VERIFIED))
        protocols.send_bytes(error_bytes, key.sock, None, False)
        close_bad_connection(key, key.data.addr, key.sock)
        return

    player_id = key.data.player_id
    key.data.player_name = message['name']
    key.data.pub_key = message['pub_key']

    response = protocols.confirm_registration(player_id, SERVER_CONTEXT['pub_key'], ca)
    SERVER_CONTEXT['reg_ct'] += 1
    SERVER_CONTEXT['homeless'].append(key)
    repsonse_bytes = protocols.make_json_bytes(response)
    sock = key.fileobj
    protocols.send_bytes(repsonse_bytes, sock, None, False) #key.data.pub_key, True)

    if SERVER_CONTEXT['reg_ct'] == 2:
        SERVER_CONTEXT['reg_ct'] = 0
        protocols.print_and_log('Starting Game')
        start_game()

def start_game():
    """update game context for server and players, randomly select the first player and allow request the first move"""
    GAME_CONTEXT['connections'] = SERVER_CONTEXT['homeless'][:2]
    SERVER_CONTEXT['homeless'] = SERVER_CONTEXT['homeless'][2:]
    players = []

    for p in range(2):
        cur = GAME_CONTEXT['connections'][p]
        p = Player(cur.data.player_name, cur.data.player_id)
        print(p)
        players.append( p )
    # players = sorted(players)
    Player.set_player_colors(players)
    for p in players:
        print(p)

    GAME_CONTEXT['cur_player'] = random.choice([0,1])
    GAME_CONTEXT['board'] = Board(players)

    notify_other_player()

    # notify a player that they will begin
    message = protocols.your_turn(-1)
    cur_player = GAME_CONTEXT['connections'][GAME_CONTEXT['cur_player']]
    protocols.print_and_log(f"First player is {cur_player.data.player_name}, player id {cur_player.data.player_id}")
    protocols.send_bytes(protocols.make_json_bytes(message), cur_player.fileobj, cur_player.data.pub_key, True)

def notify_other_player():
    """Send both players the information they need about their opponent"""
    protocols.print_and_log('Sending other player data')
    for conn_i in range(len(GAME_CONTEXT['connections'])):
        other_player = GAME_CONTEXT['connections'][(conn_i + 1) % 2]
        cur_player = GAME_CONTEXT['connections'][conn_i]
        message = protocols.other_player(other_player.data.player_name, other_player.data.player_id)
        protocols.send_bytes(protocols.make_json_bytes(message), cur_player.fileobj, cur_player.data.pub_key, True)

def make_players_move(message, key):
    if len(GAME_CONTEXT['connections']) != 2:
        return # message was sent after the other player disconnected while live client was waiting for user input
        
    cur_player_key = GAME_CONTEXT['connections'][GAME_CONTEXT['cur_player']]
    # print(f"start game: cur player: {GAME_CONTEXT['connections'][GAME_CONTEXT['cur_player']]}")
    print(f"The player whose turn it is making a move?: {cur_player_key.data.player_id} == {key.data.player_id} ? : {cur_player_key.data.player_id == key.data.player_id}")
    board = GAME_CONTEXT['board']
    last_move = message['move']
    board.place_tile(last_move, key.data.player_id)

    print(board) # prints with colored circles
    with open(protocols.SERVER_LOG_PATH, 'a') as file:
        file.write(board.draw_board_for_log()) #print in log with player id

    over = board.game_over()
    protocols.print_and_log(f'Checking for game over: {over}')
    if over:
        game_over(last_move)
        return
    GAME_CONTEXT['cur_player'] = (GAME_CONTEXT['cur_player'] + 1) % 2

    message = protocols.your_turn(last_move)
    next_player_socket = GAME_CONTEXT['connections'][GAME_CONTEXT['cur_player']].fileobj
    player_public_key = GAME_CONTEXT['connections'][GAME_CONTEXT['cur_player']].data.pub_key
    protocols.send_bytes(protocols.make_json_bytes(message), next_player_socket, player_public_key, True)

def game_over(last_move):
    board = GAME_CONTEXT['board']
    protocols.print_and_log('game over')
    if board.winner == Board.FILL_VALUE:
        protocols.print_and_log("The game is a draw")
    else:
        protocols.print_and_log(f'WINNER IS {Player.get_player_by_id(board.players, board.winner).name}, player id: {Player.get_player_by_id(board.players, board.winner).id}')
    message = protocols.game_over(board.winner, last_move)
    for key in GAME_CONTEXT['connections']:
        protocols.send_bytes(protocols.make_json_bytes(message), key.fileobj, key.data.pub_key, True)

def check_sockets():
    try:
        while True:
            events = SEL.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj)
                else:
                    service_connection(key, mask)
    except ConnectionResetError as e:
        print(e)

def accept_wrapper(sock):
    conn, addr = sock.accept()
    protocols.print_and_log(f"accepted connection from {addr}")
    if SERVER_CONTEXT['conn_ct'] >= 2:
        # send message to say the game is full
        error_bytes = protocols.make_json_bytes(protocols.error_response(protocols.Errors.PLAYER_COUNT_EXCEEDED))
        protocols.send_bytes(error_bytes, conn, None, False)
        conn.close()
        return
    conn.setblocking(False)
    conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1) # WHY ARE MY SOCKETS TIMING OUT?
    data = types.SimpleNamespace(addr=addr, player_id=SERVER_CONTEXT['conn_ct'], player_name="", pub_key=None)
    events = selectors.EVENT_READ
    SEL.register(conn, events, data=data)
    SERVER_CONTEXT['conn_ct'] += 1

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        try:
            recv_data = sock.recv(11)
            if recv_data:
                message = protocols.read_json_bytes(recv_data, sock, SERVER_CONTEXT['pri_key'])
                handle_events(message, key)
            else:
                close_bad_connection(key, data.addr, sock)
        except ConnectionResetError:
            close_bad_connection(key, data.addr, sock)

def close_bad_connection(key, addr, sock):
    """update server and game state and close server side socket when a player disconnects"""
    protocols.print_and_log(f"Closing connection to {addr} {key.data.player_name}")
    if key in GAME_CONTEXT['connections']:
        #remove the connection from game connections
        GAME_CONTEXT['connections'].remove(key)
        board = GAME_CONTEXT['board']
        if not board.game_over() :
            forfeit_game(key, board)
    if key in SERVER_CONTEXT['homeless']: # remove connection from server context if it's been saved
        SERVER_CONTEXT['homeless'].remove(key)
        SERVER_CONTEXT['reg_ct'] -= 1
    SEL.unregister(sock)
    sock.close()
    SERVER_CONTEXT['conn_ct'] -= 1
    protocols.print_and_log(f"Current number of connections: {SERVER_CONTEXT['conn_ct']}")

def forfeit_game(key, board):
    # manually set the winner to the remaining player
    if len(GAME_CONTEXT['connections']) > 0:
        other_key = GAME_CONTEXT['connections'][0]
        protocols.print_and_log(f'Player {key.data.player_name} disconnected; Game forfeited to {other_key.data.player_name}')
        board.winner = other_key.data.player_id
        message = protocols.game_over(board.winner, -2)
        protocols.send_bytes(protocols.make_json_bytes(message), other_key.fileobj, other_key.data.pub_key, True)

def set_up_server_socket():
    port = DEFAULT_PORT
    if args.port is not None:
        port = args.port
    try:
        ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ss.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            ss.bind(('0.0.0.0', port)) # static port, default when one isn't provided at startup
        except OSError as e:
            ss.bind(('0.0.0.0', 0)) # any available port, if the requested one won't bind
            protocols.print_and_log(f"Port {port} is unavailable, using port {ss.getsockname()[1]}")
        ss.listen()
        ss.setblocking(False)
        SEL.register(ss, selectors.EVENT_READ, data=None)
        SERVER_CONTEXT['server_socket'] = ss
    except:
        traceback.print_exc()
        protocols.print_and_log('Unable to set up server connection. Exiting.')
        exit()

def handle_args():
    protocols.print_and_log('STARTING SERVER')
    set_up_server_socket()
    hostname = socket.gethostname()
    SERVER_CONTEXT['pub_key'], SERVER_CONTEXT['pri_key'] = rsa.newkeys(512)
    if args.dns:
        protocols.print_and_log(f'DNS name of server: {hostname}')
    if args.ipaddr:
        ipv4 = socket.gethostbyname(hostname)
        protocols.print_and_log(f'IP Address: {ipv4}')
    if args.port:
        protocols.print_and_log(f"PORT: {SERVER_CONTEXT['server_socket'].getsockname()[1]}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Server for 'Connect 4' game")
    parser.add_argument('-i', '--ipaddr', action='store_true', help='Prints the IPv4 address of the server')
    parser.add_argument('-p', '--port', type=int, help='Port number for the server to listen on')
    parser.add_argument('-d', '--dns', action='store_true', help='Prints the DNS name of the server')
    args = parser.parse_args()
    handle_args()
    main()

# python3 server.py -i -p