import ssl

import ecdsa
from Crypto.PublicKey import ECC
from nacl.public import PrivateKey


def make_identity_keys():
    ecc_key = ECC.generate(curve="P-256")  # EXPECT: ECC
    box_key = PrivateKey.generate()  # EXPECT: ECC
    sign_key = ecdsa.SigningKey.generate()  # EXPECT: ECC
    return ecc_key, box_key, sign_key


def tls_context():
    return ssl.create_default_context()
