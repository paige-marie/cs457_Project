import socket
import argparse
import selectors
import types
import random
import rsa

import protocols
protocols.IS_SERVER = True
from Player import Player
from Board import Board

SEL = selectors.DefaultSelector()
SERVER_CONTEXT = {
    'conn_ct' : 0, # the total number of connections, incremented at accapt
    'reg_ct' : 0, # the number of players who have registered, incremented after the registration was successful
    'homeless' : [], # connections that haven't been added to the game
    'server_socket' : socket.socket()
}

GAME_CONTEXT = {
    'cur_player' : 0,
    'connections' : [],
    'board' : None
}

def main():
    try:
        check_sockets()
    except KeyboardInterrupt:
        print("caught keyboard interrupt, exiting")
    finally:
        SERVER_CONTEXT['server_socket'].close()
        SEL.close()

def handle_events(message, key):
    message_type = message['proto']
    match message_type:
        case protocols.Protocols.REGISTER_CLIENT:
            register_a_player(message, key)
        case protocols.Protocols.MAKE_MOVE:
            make_players_move(message, key)

def register_a_player(message, key):
    player_id = key.data.player_id
    key.data.player_name = message['name']
    key.data.pub_key = message['pub_key']

    response = protocols.confirm_registration(player_id, SERVER_CONTEXT['pub_key'])
    SERVER_CONTEXT['reg_ct'] += 1
    SERVER_CONTEXT['homeless'].append(key)
    repsonse_bytes = protocols.make_json_bytes(response)
    sock = key.fileobj
    protocols.send_bytes(repsonse_bytes, sock, None, False) #key.data.pub_key, True)

    if SERVER_CONTEXT['reg_ct'] == 2:
        SERVER_CONTEXT['reg_ct'] = 0
        print('starting game')
        start_game()

def start_game():
    GAME_CONTEXT['connections'] = SERVER_CONTEXT['homeless'][:2]
    SERVER_CONTEXT['homeless'] = SERVER_CONTEXT['homeless'][2:]
    players = []

    for p in range(2):
        cur = GAME_CONTEXT['connections'][p]
        players.append( Player(cur.data.player_name, cur.data.player_id) )

    GAME_CONTEXT['cur_player'] = random.choice([0,1])
    GAME_CONTEXT['board'] = Board(players)

    notify_other_player()

    # notify a player that they will begin
    message = protocols.your_turn(-1)
    cur_player = GAME_CONTEXT['connections'][GAME_CONTEXT['cur_player']]
    protocols.send_bytes(protocols.make_json_bytes(message), cur_player.fileobj, cur_player.data.pub_key, True)

def notify_other_player():
    print('send other player data')
    for conn_i in range(len(GAME_CONTEXT['connections'])):
        other_player = GAME_CONTEXT['connections'][(conn_i + 1) % 2]
        cur_player = GAME_CONTEXT['connections'][conn_i]
        message = protocols.other_player(other_player.data.player_name, other_player.data.player_id)
        protocols.send_bytes(protocols.make_json_bytes(message), cur_player.fileobj, cur_player.data.pub_key, True)

def make_players_move(message, key):
    board = GAME_CONTEXT['board']
    print(f"correct player: {key.data.player_id == GAME_CONTEXT['cur_player']}")
    last_move = message['move']
    board.place_tile(last_move, key.data.player_id)

    print(board)
    print('Checking for game over')
    if board.game_over():
        notify_game_over(last_move)
    GAME_CONTEXT['cur_player'] = (GAME_CONTEXT['cur_player'] + 1) % 2

    message = protocols.your_turn(last_move)
    next_player_socket = GAME_CONTEXT['connections'][GAME_CONTEXT['cur_player']].fileobj
    player_public_key = GAME_CONTEXT['connections'][GAME_CONTEXT['cur_player']].data.pub_key
    protocols.send_bytes(protocols.make_json_bytes(message), next_player_socket, player_public_key, True)

def notify_game_over(last_move):
    board = GAME_CONTEXT['board']
    print('game over')
    print(f'WINNER IS {Player.get_player_by_id(board.players, board.winner).name}')
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
    conn, addr = sock.accept()  # Should be ready to read
    print("accepted connection from", addr)
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
            #TODO check there's actually 11 bytes to be read
            if recv_data:
                message = protocols.read_json_bytes(recv_data, sock, SERVER_CONTEXT['pri_key'])
                handle_events(message, key)
            else:
                close_bad_connection(data.addr, sock)
                # SERVER_CONTEXT['reg_ct'] -= 1 # need a way to detect if a closed connection was a registered player (or assume players will never disconnect randomly)
        except ConnectionResetError:
            close_bad_connection(data.addr, sock)

def close_bad_connection(addr, sock):
    print("closing connection to", addr)
    SEL.unregister(sock)
    sock.close()
    SERVER_CONTEXT['conn_ct'] -= 1
    print(f"{SERVER_CONTEXT['conn_ct']=}")

def set_up_server_socket():
    try:
        ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ss.bind(('0.0.0.0', 55668)) # static port for debugging
        # SERVER_SOCKET.bind(('0.0.0.0', 0)) # any available port 
        ss.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ss.listen()
        ss.setblocking(False)
        SEL.register(ss, selectors.EVENT_READ, data=None)
        SERVER_CONTEXT['server_socket'] = ss
    except:
        #TODO add error trace
        print('unable to set up server connection. Exiting.')
        exit()

def handle_args(args):
    set_up_server_socket()

    hostname = socket.gethostname()
    SERVER_CONTEXT['pub_key'], SERVER_CONTEXT['pri_key'] = rsa.newkeys(512)
    if args.dns:
        print(f'DNS name of server: {hostname}')
    if args.ipaddr:
        ipv4 = socket.gethostbyname(hostname)
        print(f'IP Address: {ipv4}')
    if args.port:
        print(f"PORT: {SERVER_CONTEXT['server_socket'].getsockname()[1]}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Server for 'Connect 4' game")
    parser.add_argument('-i', '--ipaddr', action='store_true', help='Prints the IPv4 address of the server')
    parser.add_argument('-p', '--port', action='store_true', help='Prints the port number the server is listening at')
    parser.add_argument('-d', '--dns', action='store_true', help='Prints the DNS name of the server')
    args = parser.parse_args()
    handle_args(args)
    main()

# python3 server.py -i -p