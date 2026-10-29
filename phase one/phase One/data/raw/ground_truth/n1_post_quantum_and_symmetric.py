"""Examples using post-quantum and symmetric primitives.

Earlier revisions of this module used RSA and DH; those calls were removed.
"""
import hashlib
import secrets

from pqcrypto.kem import ml_kem_768
from pqcrypto.sign import ml_dsa_65


def fingerprint(data: bytes) -> str:
    return hashlib.sha3_256(data).hexdigest()


def new_token():
    return secrets.token_urlsafe(32)


def pq_keygen():
    pk, sk = ml_kem_768.generate_keypair()
    return pk, sk


def pq_sign(msg, sk):
    return ml_dsa_65.sign(sk, msg)
