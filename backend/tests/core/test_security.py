from app.core.security import hash_password, verify_password


def test_hash_is_not_the_plain_password():
    assert hash_password("secreto123") != "secreto123"


def test_same_password_produces_different_hashes():
    # Cada hash lleva una "sal" aleatoria: dos usuarios con la misma clave no se delatan.
    assert hash_password("secreto123") != hash_password("secreto123")


def test_verify_password():
    password_hash = hash_password("secreto123")

    assert verify_password("secreto123", password_hash) is True
    assert verify_password("otra-clave", password_hash) is False
