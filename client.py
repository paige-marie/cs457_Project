import socket
import argparse
import struct
import traceback
import rsa

import protocols
from Player import Player
from Board import Board
import auxillary

KEYS = {}

def main():
    game_over = False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # sock.settimeout(10)
            try:
                sock.connect((args.server_ip, args.port))
            except ConnectionRefusedError:
                print("Error: Unable to connect to server. Check the address and port and try again.\nExiting")
                return
            # except socket.error as e:
            #     print(f"Error: Socket error occurred - {e}")
            #     return

            my_player = setup(sock)
            other_player = get_other_player_info(sock)

            players = [my_player, other_player]
            players = sorted(players)
            board = Board(players)
            while(True):
                recv_data = sock.recv(11)
                if recv_data:
                    message = protocols.read_json_bytes(recv_data, sock, KEYS['pri_key'])
                    print(message)
                    if message['proto'] == protocols.Protocols.GAME_OVER:
                        game_over = True
                        break
                    if message['proto'] != protocols.Protocols.YOUR_TURN:
                        raise auxillary.CustomError(f"Unexpected message from server: {message}")
                        continue
                    my_move = take_my_turn(message, board, players)
                    message = protocols.make_move(my_move)
                    protocols.send_bytes(protocols.make_json_bytes(message), sock, KEYS['server_pub_key'], True)

                else:
                    print('Server has disconnected, closing socket')
                    sock.close()
                    break
            
            if game_over:
                print(f"The winner is {Player.get_player_by_id(players, message['winner']).name}!")
            else:
                print(f"The game was terminated early.")
    
    except KeyboardInterrupt:
        print("caught keyboard interrupt, exiting")
    except Exception as e:
        traceback.print_exc()
        print(f"An unexpected error occurred: {e}")


def setup(sock):
    KEYS['pub_key'], KEYS['pri_key'] = rsa.newkeys(512)
    print(f"my pub key: \n{KEYS['pub_key']}")
    name = input('Please enter your name: ')
    # sock.sendall(protocols.make_json_bytes(protocols.register_with_server(name, KEYS['pub_key'])))
    message = protocols.register_with_server(name, KEYS['pub_key'])
    protocols.send_bytes( protocols.make_json_bytes(message), sock, None, False)
    try:
        recv_data = sock.recv(11)
        # label, json_length = struct.unpack('>6sI', recv_data)
        # data = sock.recv(json_length)
        response = protocols.read_json_bytes(recv_data, sock, None)
    except socket.error as e:
        print(f"Error: Socket error during setup - {e}")
        return
    # except struct.error as e:
    #     print(f"Error: Struct error - {e}")
    #     return

    if response['proto'] == protocols.Protocols.ERROR:
        print(response['error_message'])
        print('Exiting')
        exit()
        
    print(response)
    global MY_ID
    KEYS['server_pub_key'] = response['pub_key']
    MY_ID = response['player_id']
    my_player = Player(name, MY_ID, True)
    return my_player

def get_other_player_info(sock):
    recv_data = sock.recv(11)
    response = protocols.read_json_bytes(recv_data, sock, KEYS['pri_key'])
    print(response)
    other_player = Player(response['other_name'], response['other_id'], False)
    return other_player

def take_my_turn(message, board, players):
    # assert message['proto'] == protocols.Protocols.YOUR_TURN
    if message['last_move'] != -1:
        col = message['last_move']
        board.place_tile(col, (MY_ID + 1)%2)
        auxillary.clear_terminal()
    print(board)
    while True:
        try:
            col = int(input(f'{auxillary.color_text(players[MY_ID], players[MY_ID].name)}, what column? '))
            valid = board.place_tile(col, MY_ID)
            if valid:
                break
            print("Invalid location")
        except ValueError:
            print('input must be a valid column number')
    auxillary.clear_terminal()
    print(board)
    return col

def get_instructions():
    return """
    The goal of the game is to get 4 of you tiles in a row (in any direction) before the other player.
    To drop a token into a column, simply enter the column number when it is your turn.
    """

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Client for 'Connect 4' game",
                                     epilog=get_instructions())

    parser.add_argument('-i', '--server_ip',
                         metavar='<Server IP Address>', 
                         required=True, 
                         help='The IP address the server is running at')
    parser.add_argument('-p', '--port',
                        metavar='<Server Port Number>', 
                        required=True,
                        type=int,
                        help='The port number the server is listening at')
    parser.add_argument('-n', '--dns',
                        action='store_true',
                        # metavar='DNS of Server', 
                        required=False,
                        help='Prints the DNS name of the server')
    args = parser.parse_args()
    # SERVER_IP = args.server_ip
    # SERVER_PORT = args.port
    main()

# python3 client.py -i harrisburg -p 55667
