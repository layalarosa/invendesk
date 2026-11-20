# Invendesk — Copyright (C) 2026 Luis A Ayala Rosa
# Licensed under the GNU GPL, version 3 or later. See LICENSE.

import hashlib
import hmac
import secrets

import db

PBKDF2_ITERATIONS = 200_000
MIN_PASSWORD_LEN = 6


def _hash_password(password, iterations=PBKDF2_ITERATIONS):
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return "pbkdf2${}${}${}".format(iterations, salt.hex(), dk.hex())


def verify_password(password, stored):
    if not stored:
        return False
    try:
        algo, iter_s, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2":
            return False
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iter_s)
        )
        return hmac.compare_digest(dk.hex().lower(), hash_hex.lower())
    except (ValueError, TypeError):
        return False


def has_users():
    return db.get_conn().execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"] > 0


def create_user(username, password, full_name=""):
    """Crea un usuario. Devuelve (ok, mensaje). Valida entrada sucia."""
    username = (username or "").strip()
    full_name = (full_name or "").strip()[:120]
    if not username:
        return False, "El usuario es obligatorio."
    if len(password or "") < MIN_PASSWORD_LEN:
        return False, f"La contraseña debe tener al menos {MIN_PASSWORD_LEN} caracteres."
    conn = db.get_conn()
    if conn.execute(
        "SELECT id FROM users WHERE username = ? COLLATE NOCASE", (username,)
    ).fetchone():
        return False, "El usuario ya existe."
    conn.execute(
        "INSERT INTO users (username, full_name, password_hash, created_at) VALUES (?, ?, ?, ?)",
        (username, full_name, _hash_password(password), db.now_iso()),
    )
    conn.commit()
    return True, ""


def authenticate(username, password):
    username = (username or "").strip()
    if not username or not password:
        return None
    row = db.get_conn().execute(
        "SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username,)
    ).fetchone()
    if row is not None and verify_password(password, row["password_hash"]):
        return row
    return None


def change_password(user_id, current_password, new_password):
    row = db.get_conn().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        return False, "Usuario no encontrado."
    if not verify_password(current_password, row["password_hash"]):
        return False, "La contraseña actual es incorrecta."
    if len(new_password or "") < MIN_PASSWORD_LEN:
        return False, f"La nueva contraseña debe tener al menos {MIN_PASSWORD_LEN} caracteres."
    db.get_conn().execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (_hash_password(new_password), user_id),
    )
    db.get_conn().commit()
    return True, ""
