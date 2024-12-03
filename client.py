import socket
import argparse
import traceback
import rsa

import protocols
from Player import Player
from Board import Board
import auxillary

from simulate_certificate_authority import CertificateAuthority

ca = CertificateAuthority(is_server=False)

KEYS = {}

def main():
    game_over = False
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.connect((args.server_ip, args.port))
                if args.dns:
                    resolved_ip = socket.gethostbyname(args.server_ip)
                    print(f"Connected to server at {resolved_ip} ({args.server_ip})")
            except ConnectionRefusedError:
                print("Error: Unable to connect to server. Check the address and port and try again.\nExiting")
                return

            my_player = setup(sock)
            other_player = get_other_player_info(sock)

            players = [my_player, other_player]
            players = sorted(players)
            Player.set_player_colors(players)

            board = Board(players)
            while(True):
                try:
                    recv_data = sock.recv(11)
                    if recv_data:
                        message = protocols.read_json_bytes(recv_data, sock, KEYS['pri_key'])
                        if message['proto'] == protocols.Protocols.GAME_OVER:
                            game_over = True
                            break
                        if message['proto'] != protocols.Protocols.YOUR_TURN:
                            raise auxillary.CustomError(f"Unexpected message from server: {message}")
                            
                        my_move = take_my_turn(message, board, players)
                        message = protocols.make_move(my_move)
                        protocols.send_bytes(protocols.make_json_bytes(message), sock, KEYS['server_pub_key'], True)

                    else:
                        print('Server has disconnected, closing socket')
                        sock.close()
                        break
                except auxillary.CustomError as e:
                    print(e)
                    continue
            
            if game_over:
                if message['last_move'] == -2: 
                    print(f"{auxillary.color_text(other_player, other_player.name)} has forfeited.")
                if message['winner'] != MY_ID: # if I am not the winner, reprint the board with the winning move
                    col = message['last_move']
                    board.place_tile(col, (MY_ID + 1)%2)
                    auxillary.clear_terminal()
                    print(board)
                if message['winner'] == -1:
                    print("There are no more valid moves; the game is a draw")
                else:
                    winning_player = Player.get_player_by_id(players, message['winner'])
                    print(f"The winner is {auxillary.color_text(winning_player, winning_player.name)}!")
            else: # pretty much only caused by unexpected message from server, like it shuts down
                print(f"The game was terminated early.")
    
    except KeyboardInterrupt:
        print(" Caught keyboard interrupt, exiting")
    except auxillary.CustomError as e: 
        print(e)
    except Exception as e:
        traceback.print_exc()
        print(f"An unexpected error occurred: {e}")
    finally:
        sock.close()
        print("Restart to play again")


def setup(sock):
    KEYS['pub_key'], KEYS['pri_key'] = rsa.newkeys(512)
    name = input('Please enter your name: ')
    message = protocols.register_with_server(name, KEYS['pub_key'], ca)
    protocols.send_bytes( protocols.make_json_bytes(message), sock, None, False)
    try:
        recv_data = sock.recv(11)
        response = protocols.read_json_bytes(recv_data, sock, None)
    except socket.error as e:
        print(f"Error: Socket error during setup - {e}")
        return

    if response['proto'] == protocols.Protocols.ERROR:
        print(response['error_message'])
        print('Exiting')
        exit()
    
    global MY_ID

    verified = ca.verify_signature(response['pub_key'], response['signature'])
    if not verified: 
        raise auxillary.CustomError("Server's public key could not be verified. Disconnecting and exiting.")
    print(f'Server key verified: {verified}')
    KEYS['server_pub_key'] = response['pub_key']
    MY_ID = response['player_id']
    my_player = Player(name, MY_ID, True)
    return my_player

def get_other_player_info(sock):
    recv_data = sock.recv(11)
    response = protocols.read_json_bytes(recv_data, sock, KEYS['pri_key'])
    other_player = Player(response['other_name'], response['other_id'], False)
    return other_player

def take_my_turn(message, board, players):
    if message['last_move'] != -1: #place the other players tile because this isn't the first move
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
                         help='The IP address or hostname the server is running at')
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
    
    main()

# python3 client.py -i harrisburg -p 55668
