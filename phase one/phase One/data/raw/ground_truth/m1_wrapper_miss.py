from internal_keystore import keystore


def provision_device(device_id: str):
    keypair = keystore.make_rsa_keypair(bits=3072)  # EXPECT: RSA
    keystore.save(device_id, keypair)
    return keypair
