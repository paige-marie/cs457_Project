import socket
import argparse
import struct

import protocols

def main():
    try:

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((args.server_ip, args.port))
            setup(sock)
            while(True):
                # gameplay goes here
                # game logic will all be on the server
                # client will only update the board and ask the player for their move
                pass 
    
    except KeyboardInterrupt:
        print("caught keyboard interrupt, exiting")


def setup(sock):
    name = input('Please enter your name: ')
    sock.sendall(protocols.make_json_bytes(protocols.register_with_server(name)))
    recv_data = sock.recv(10)
    label, json_length = struct.unpack('>6sI', recv_data)
    data = sock.recv(json_length)
    response = protocols.read_json_bytes(data)
    if response['proto'] == protocols.Protocols.ERROR:
        print(response['error_message'])
        print('Exiting')
        exit()
    print(response)
    global MY_ID
    MY_ID = response['player_id']
    # my_player = Player(name, MY_ID, True)
    # return my_player

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