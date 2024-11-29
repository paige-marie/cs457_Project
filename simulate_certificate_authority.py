import hashlib
import rsa
import base64
import os
import time

class CertificateAuthority:

    def __init__(self, is_server: bool):
        self.ca_keys = self._get_CA_keys()
        self.is_server = is_server

    def verify_signature(self, to_be_verified: rsa.PublicKey, signature: bytes) -> bool:
        to_be_verified_str = key_to_string(to_be_verified)
        hash_hex = self._get_hash(to_be_verified_str)
        try:
            rsa.verify(hash_hex.encode('utf-8'), signature, self.ca_keys['pri_key'])
            return True
        except rsa.VerificationError:
            # print("Signature verification failed.")
            return False

    def create_signature(self, to_be_signed) -> bytes:
        if type(to_be_signed) != str:
            to_be_signed = key_to_string(to_be_signed)
        hash_digest = self._get_hash(to_be_signed)
        ca_signature = rsa.sign(hash_digest.encode('utf-8'), self.ca_keys['pri_key'], 'SHA-256') # message_bytes, private key, hash method
        return ca_signature

    def _get_CA_keys(self) -> dict:
        """Returns the CA keys, create them if they don't exist but only for server. Client will sleep and try again to avoid a race condition (though a race conidtion still exists)"""
        ca_keys = dict()
        ca_folder = os.path.join(".", "ca_keys")
        got_keys = False
        while not got_keys: 
            if not os.path.exists(ca_folder) and self.is_server: # if keys don't exist, create, save, and use them
                os.makedirs(ca_folder, exist_ok=True)
                ca_keys['pub_key'], ca_keys['pri_key'] = rsa.newkeys(512)
                with open(os.path.join(ca_folder, "public_key.pem"), "wb") as pub_file:
                    pub_file.write(ca_keys['pub_key'].save_pkcs1(format='PEM'))
                with open(os.path.join(ca_folder, "private_key.pem"), "wb") as pri_file:
                    pri_file.write(ca_keys['pri_key'].save_pkcs1(format='PEM'))
                got_keys = True
            elif not os.path.exists(ca_folder) and not self.is_server: #only the server can cause the keys to generate
                got_keys = False
                print('waiting')
                time.sleep(0.2)
            else: # if keys do exist, load and use them
                with open(os.path.join(ca_folder, "public_key.pem"), "rb") as pub_file:
                    ca_keys['pub_key'] = rsa.PublicKey.load_pkcs1(pub_file.read(), format='PEM')
                with open(os.path.join(ca_folder, "private_key.pem"), "rb") as pri_file:
                    ca_keys['pri_key'] = rsa.PrivateKey.load_pkcs1(pri_file.read(), format='PEM')
                got_keys = True
        
        return ca_keys

    def _get_hash(self, to_be_hashed: str) -> str:
        """creates a hash using SHA256 for a given string"""
        hasher = hashlib.sha256()
        hasher.update(to_be_hashed.encode('utf-8'))
        hash_hex = hasher.hexdigest()
        return hash_hex

def main():
    ca_obj = CertificateAuthority(True)
    server_pub_key, server_pri_key = rsa.newkeys(512)
    server_public_key_ser = key_to_string(server_pub_key)
    server_public_key_signature = ca_obj.create_signature(server_public_key_ser)
    message_sent = {'pub_key': server_public_key_ser, 'signature': server_public_key_signature}
    sent_bytes = make_json_bytes(message_sent)
    message_recv = read_json_bytes(sent_bytes)
    verified = ca_obj.verify_signature(message_recv['pub_key'], message_recv['signature'])
    print(f"verified: {verified}")

def key_to_string(key):
    if type(key) == str:
        return key
    return base64.b64encode(key.save_pkcs1(format='PEM')).decode('utf-8')

def make_json_bytes(data):
    data['signature'] = base64.b64encode(data['signature']).decode('utf-8')
    print(data)
    return json.dumps(data).encode('utf-8')

def read_json_bytes(data):
    message = json.loads(data.decode('utf-8'))
    message['pub_key'] = rsa.PublicKey.load_pkcs1(base64.b64decode(message['pub_key']), format='PEM')
    message['signature'] = base64.b64decode(message['signature'])
    return message


if __name__ == "__main__":
    import json
    try:
        main()
    except KeyboardInterrupt:
        pass