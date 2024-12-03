import json
import struct
import rsa
import base64

from auxillary import CustomError

IS_SERVER = False
SERVER_LOG_PATH = 'server-log.log'

class Protocols:
    REGISTER_CLIENT = 0
    REGISTER_CONFIRM = 1
    OTHER_PLAYER = 8
    YOUR_TURN = 5
    MAKE_MOVE = 6
    GAME_OVER = 7
    ERROR = -1

    PROTO_NAMES = {
        0: "REGISTER_CLIENT",
        1: "REGISTER_CONFIRM",
        8: "OTHER_PLAYER",
        5: "YOUR_TURN",
        6: "MAKE_MOVE",
        7: "GAME_OVER",
        -1: "ERROR"
    }

class Errors:
    PLAYER_COUNT_EXCEEDED = 1
    PUBLIC_KEY_NOT_VERIFIED = 2
    CUSTOM_ERROR = -1

def print_and_log(log_str):
    """ONLY CALLED BY SERVER, print to terminal and to a log file"""
    with open(SERVER_LOG_PATH, 'a') as file:
        if isinstance(log_str, dict):
            log_str = log_str.copy()
            for key, value in log_str.items():
                if key == 'pub_key' or key == 'signature':
                    log_str[key] = 'REDACTED'
                file.write(f"\t{key}: {log_str[key]}\n")
                if key == 'proto':
                    file.write(f"\tmessag_type: {Protocols.PROTO_NAMES[value]}\n")
        else:
            file.write(log_str + '\n')
    print(log_str)

def send_bytes(message_bytes, sock, other_pubKey, encrypt): #will only be none and False for the first messages between client and server
    if encrypt:
        message_bytes = rsa.encrypt(message_bytes, other_pubKey)
    length = len(message_bytes)
    encrypt_flag = int(encrypt)
    prefix = struct.pack('>6sI?', b'length', length, encrypt_flag)
    message_bytes = prefix + message_bytes

    total_sent = 0
    while total_sent < length:
        try:
            message_bytes = message_bytes[total_sent:]
            sent = sock.send(message_bytes)
            total_sent += sent
        except BlockingIOError:
            continue

def read_json_bytes(recv_data, sock, my_priKey): #will only be none for the first messages between client and server
    label, json_length, encrypt_flag = struct.unpack('>6sI?', recv_data)
    if label != b'length':
        print(label)
        raise CustomError("Message recieved has an incompatible header. Ignoring message.")
    data = sock.recv(json_length)
    if encrypt_flag:
        data = rsa.decrypt(data, my_priKey)
    message = json.loads(data.decode('utf-8'))

    # convert the key from a serialized object back to the type we need
    if message['proto'] == Protocols.REGISTER_CLIENT or message['proto'] == Protocols.REGISTER_CONFIRM:
        message['pub_key'] = rsa.PublicKey.load_pkcs1(base64.b64decode(message['pub_key']), format='PEM')
        message['signature'] = base64.b64decode(message['signature'])

    if IS_SERVER:
        with open(SERVER_LOG_PATH, 'a') as file:
            file.write('Message received:\n')
        print_and_log(message)
    return message
        

def make_json_bytes(data):
    json_bytes = json.dumps(data).encode('utf-8')
    if IS_SERVER:
        with open(SERVER_LOG_PATH, 'a') as file:
            file.write('Message sent:\n')
        print_and_log(data)
    return json_bytes

def register_with_server(player_name, client_public_key, ca):
    """
    SENT BY CLIENT
    """
    client_public_key_ser = base64.b64encode(client_public_key.save_pkcs1(format='PEM')).decode('utf-8')
    signature = base64.b64encode(ca.create_signature(client_public_key_ser)).decode('utf-8')
    return {
        'proto' : Protocols.REGISTER_CLIENT,
        'name' : player_name,
        'pub_key' : client_public_key_ser,
        'signature': signature
    }

def confirm_registration(player_id, server_public_key, ca):
    """
    SENT BY SERVER
    """
    server_public_key_ser = base64.b64encode(server_public_key.save_pkcs1(format='PEM')).decode('utf-8')
    signature = base64.b64encode(ca.create_signature(server_public_key_ser)).decode('utf-8')
    return {
        'proto' : Protocols.REGISTER_CONFIRM,
        'player_id' : player_id,
        'pub_key' : server_public_key_ser,
        'signature': signature
    }

def other_player(other_name, other_id):
    """
    SENT BY SERVER
    """
    return {
        'proto' : Protocols.OTHER_PLAYER,
        'other_name' : other_name,
        'other_id' : other_id
    }

def your_turn(last_move):
    """
    SENT BY SERVER
    """
    return {
        'proto' : Protocols.YOUR_TURN,
        'last_move' : last_move
    }

def make_move(move):
    """
    SENT BY CLIENT
    """
    return {
        'proto' : Protocols.MAKE_MOVE,
        'move' : move
    }

def game_over(winner, last_move):
    """
    SENT BY SERVER
    """
    return {
        'proto' : Protocols.GAME_OVER,
        'winner' : int(winner),
        'last_move' : last_move
    }

def error_response(error, custom_message=""):
    match error:
        case Errors.PLAYER_COUNT_EXCEEDED:
            error_message = "The maximum player count has been reached. Please try again later"
        case Errors.CUSTOM_ERROR:
            error_message = custom_message
        case _:
            error_message = "An unknown error has occured."
    
    return {
        'proto' : Protocols.ERROR,
        'error_code' : error,
        'error_message' : error_message
    }