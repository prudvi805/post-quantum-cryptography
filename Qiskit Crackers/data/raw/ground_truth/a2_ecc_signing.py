from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def new_ec_identity():
    return ec.generate_private_key(ec.SECP256R1())  # EXPECT: ECC


def sign_release(payload: bytes) -> bytes:
    key = Ed25519PrivateKey.generate()  # EXPECT: ECC
    return key.sign(payload)


def sign_ecdsa(key, payload: bytes) -> bytes:
    return key.sign(payload, ec.ECDSA(hashes.SHA256()))  # EXPECT: ECC
