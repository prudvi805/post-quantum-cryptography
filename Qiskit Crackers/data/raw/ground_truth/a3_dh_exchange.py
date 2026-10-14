from cryptography.hazmat.primitives.asymmetric import dh, x25519


def start_classic_dh():
    params = dh.generate_parameters(generator=2, key_size=2048)  # EXPECT: DH
    return params


def start_x25519_side():
    alice = x25519.X25519PrivateKey.generate()  # EXPECT: ECC
    return alice.public_key()
