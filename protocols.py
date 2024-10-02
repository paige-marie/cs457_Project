import json
import struct

class Protocols:
    REGISTER_CLIENT = 0
    REGISTER_CONFIRM = 1
    ERROR = -1

class Errors:
    PLAYER_COUNT_EXCEEDED = 1
    CUSTOM_ERROR = -1

def send_bytes(message_bytes, sock):
    length = len(message_bytes)
    total_sent = 0
    while total_sent < length:
        try:
            message_bytes = message_bytes[total_sent:]
            sent = sock.send(message_bytes)
            total_sent += sent
        except BlockingIOError:
            continue

def read_json_bytes(data):
    return json.loads(data.decode('utf-8'))

def make_json_bytes(data):
    json_bytes = json.dumps(data).encode('utf-8')
    length_prefix = struct.pack('>6sI', b'length', len(json_bytes))
    return length_prefix + json_bytes

def register_with_server(player_name):
    return {
        'proto' : Protocols.REGISTER_CLIENT,
        'name' : player_name
    }

def confirm_registration(player_id):
    return {
        'proto' : Protocols.REGISTER_CONFIRM,
        'player_id' : player_id
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