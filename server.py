import socket
import argparse
import selectors
import types
import random

import protocols
from Player import Player
from Board import Board

SEL = selectors.DefaultSelector()
SERVER_CONTEXT = {
    'conn_ct' : 0,
    'reg_ct' : 0,
    'homeless' : [],
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
    print(message)
    key.data.player_name = message['name']
    response = protocols.confirm_registration(player_id)
    SERVER_CONTEXT['reg_ct'] += 1
    SERVER_CONTEXT['homeless'].append(key)
    print('sending response')
    print(response)
    repsonse_bytes = protocols.make_json_bytes(response)
    sock = key.fileobj
    protocols.send_bytes(repsonse_bytes, sock)
    if SERVER_CONTEXT['reg_ct'] == 2:
        SERVER_CONTEXT['reg_ct'] = 0
        print('starting game')
        start_game()

def start_game():
    two_players = SERVER_CONTEXT['homeless'][:2]
    SERVER_CONTEXT['homeless'] = SERVER_CONTEXT['homeless'][2:]
    players = []

    for p in range(2):
        cur = two_players[p]
        players.append( Player(cur.data.player_name, cur.data.player_id) )

    GAME_CONTEXT['cur_player'] = random.choice([0,1])
    GAME_CONTEXT['board'] = Board(players)
    GAME_CONTEXT['connections'] = two_players

    # notify each player of the other player
    print('send other player data')
    for conn_i in range(len(two_players)):
        other_player = two_players[(conn_i + 1) % 2]
        cur_player = two_players[conn_i]
        message = protocols.other_player(other_player.data.player_name, other_player.data.player_id)
        print(message)
        protocols.send_bytes(protocols.make_json_bytes(message),cur_player.fileobj)

    # notify a player that they will begin
    message = protocols.your_turn(-1)
    cur_player = two_players[GAME_CONTEXT['cur_player']]
    protocols.send_bytes(protocols.make_json_bytes(message), cur_player.fileobj)

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
    protocols.send_bytes(protocols.make_json_bytes(message), GAME_CONTEXT['connections'][GAME_CONTEXT['cur_player']].fileobj)

def notify_game_over(last_move):
    board = GAME_CONTEXT['board']
    print('game over')
    print(f'WINNER IS {Player.get_player_by_id(board.players, board.winner).name}')
    message = protocols.game_over(board.winner, last_move)
    for key in GAME_CONTEXT['connections']:
        protocols.send_bytes(protocols.make_json_bytes(message), key.fileobj)
    
    # TODO send game over message

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
    # finally:
    #     #TODO close sockets
    #     SEL.close()

def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print("accepted connection from", addr)
    if SERVER_CONTEXT['conn_ct'] >= 2:
        #send message to say the game is full
        error_bytes = protocols.make_json_bytes(protocols.error_response(protocols.Errors.PLAYER_COUNT_EXCEEDED))
        protocols.send_bytes(error_bytes, conn)
        conn.close()
        return
    conn.setblocking(False)
    conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1) # WHY ARE MY SOCKETS TIMING OUT?
    data = types.SimpleNamespace(addr=addr, player_id=SERVER_CONTEXT['conn_ct'], player_name="")
    events = selectors.EVENT_READ
    SEL.register(conn, events, data=data)
    SERVER_CONTEXT['conn_ct'] += 1

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        try:
            recv_data = sock.recv(10)
            #TODO check there's actually 10 bytes to be read
            if recv_data:
                message = protocols.read_json_bytes(recv_data, sock)
                print(message)
                handle_events(message, key)
            else:
                print("closing connection to", data.addr)
                SEL.unregister(sock)
                sock.close()
                SERVER_CONTEXT['conn_ct'] -= 1
                print(f"{SERVER_CONTEXT['conn_ct']=}")
                # SERVER_CONTEXT['reg_ct'] -= 1 # need a way to detect if a closed connection was a registered player (or assume players will never disconnect randomly)
        except ConnectionResetError:
            print("closing connection to", data.addr)
            SEL.unregister(sock)
            sock.close()
            SERVER_CONTEXT['conn_ct'] -= 1
            print(f"{SERVER_CONTEXT['conn_ct']=}")

def set_up_server_socket():
    try:
        ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ss.bind(('0.0.0.0', 55667)) # static port for debugging
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