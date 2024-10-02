import socket
import argparse
import selectors
import protocols
import types
import struct

SEL = selectors.DefaultSelector()
CONNECTION_COUNT = 0
CONNECTIONS = {}

def main():
    try:
        check_sockets()
    except KeyboardInterrupt:
        print("caught keyboard interrupt, exiting")
    finally:
        SEL.close()

def handle_events(message, key):
    message_type = message['proto']
    match message_type:
        case protocols.Protocols.REGISTER_CLIENT:
            register_a_player(message, key)

def register_a_player(message, key):
    player_id = key.data.player_id
    response = protocols.confirm_registration(player_id)
    print('sending response')
    print(response)
    repsonse_bytes = protocols.make_json_bytes(response)
    sock = key.fileobj
    protocols.send_bytes(repsonse_bytes, sock)
    #TODO once there are 2 players (CONNECTION_COUNT) the creation of the game should occur
    # including creating the player and board objects and requesting a move from one of the players


def check_sockets():
    try:
        while True:
            events = SEL.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj)
                else:
                    service_connection(key, mask)
    finally:
        SEL.close()

def accept_wrapper(sock):
    global CONNECTION_COUNT
    conn, addr = sock.accept()  # Should be ready to read
    print("accepted connection from", addr)
    if CONNECTION_COUNT >= 2:
        #send message to say the game is full
        error_bytes = protocols.make_json_bytes(protocols.error_response(protocols.Errors.PLAYER_COUNT_EXCEEDED))
        protocols.send_bytes(error_bytes, conn)
        conn.close()
        return
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, player_id=CONNECTION_COUNT)
    events = selectors.EVENT_READ
    key = SEL.register(conn, events, data=data)
    CONNECTIONS[CONNECTION_COUNT] = key
    # conn.sendall(protocols.make_json_bytes(protocols.confirm_registration(CONNECTION_COUNT)))
    CONNECTION_COUNT += 1

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(10)
        if recv_data:
            #TODO check that there's actually 10 bytes
            label, json_length = struct.unpack('>6sI', recv_data)
            #TODO check that label is the string 'length', send error response if not?
            json_bytes = sock.recv(json_length)
            message = protocols.read_json_bytes(json_bytes)
            print(message)
            handle_events(message, key)
        else:
            print("closing connection to", data.addr)
            SEL.unregister(sock)
            sock.close()
            global CONNECTION_COUNT
            CONNECTION_COUNT -= 1

def set_up_server_socket():
    try:
        global SERVER_SOCKET
        SERVER_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        SERVER_SOCKET.bind(('0.0.0.0', 55667)) # static port for debugging
        # SERVER_SOCKET.bind(('0.0.0.0', 0)) # any available port 
        SERVER_SOCKET.listen()
        SERVER_SOCKET.setblocking(False)
        SEL.register(SERVER_SOCKET, selectors.EVENT_READ, data=None)
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
        print(f"PORT: {SERVER_SOCKET.getsockname()[1]}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Server for 'Connect 4' game")
    parser.add_argument('-i', '--ipaddr', action='store_true', help='Prints the IPv4 address of the server')
    parser.add_argument('-p', '--port', action='store_true', help='Prints the port number the server is listening at')
    parser.add_argument('-d', '--dns', action='store_true', help='Prints the DNS name of the server')
    args = parser.parse_args()
    handle_args(args)
    main()