import secrets


def get_access_code(length=10):
    characters = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    access_code = ''.join(secrets.choice(characters) for _ in range(length))
    return access_code.upper()
