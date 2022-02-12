import bech32
import ecdsa
import hashlib
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.backends import default_backend
from ecdsa import SigningKey
from ecdsa.curves import SECP256k1
from ecdsa.util import sigencode_der


class KeyInteraction:
    private_signing_key: SigningKey = None

    def __init__(self, keystore_password: bytes, keystore_path):
        self.set_private_signing_key(keystore_path, keystore_password)

    def set_private_signing_key(self, keystore_path: bytes, keystore_password):
        with open(keystore_path, "rb") as f:
            private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(f.read(),
                                                                                                 keystore_password,
                                                                                                 default_backend())
            private_key_bytes = private_key.private_bytes(Encoding.DER, PrivateFormat.PKCS8, NoEncryption())
            self.private_signing_key: SigningKey = ecdsa.SigningKey.from_der(private_key_bytes, hashfunc=hashlib.sha256)

    def get_verifying_key(self):
        return self.private_signing_key.get_verifying_key()

    def get_validator_hex_public_key(self):
        public_key_compressed_bytes = self.get_verifying_key().to_string("compressed")
        return public_key_compressed_bytes.hex()

    def get_validator_address(self):
        public_key_compressed_bytes = self.get_verifying_key().to_string("compressed")
        public_key_bytes5 = bech32.convertbits(public_key_compressed_bytes, 8, 5)
        return bech32.bech32_encode("rv", public_key_bytes5)

    def get_validator_wallet_address(self):
        public_key_compressed_bytes = self.get_verifying_key().to_string("compressed")
        readdr_bytes = b"x04" + public_key_compressed_bytes
        readdr_bytes5 = bech32.convertbits(readdr_bytes, 8, 5)
        validator_wallet_address = bech32.bech32_encode("rdx", readdr_bytes5)
        return validator_wallet_address

    def sign_payload(self, payload_to_sign):
        return self.private_signing_key.sign_digest(bytearray.fromhex(payload_to_sign),
                                                    sigencode=sigencode_der).hex()
