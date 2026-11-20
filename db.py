import os
import sqlite3
import sys
from datetime import datetime

APP_NAME = "Invendesk"

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    category    TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    cost_price  REAL NOT NULL DEFAULT 0,
    sale_price  REAL NOT NULL DEFAULT 0,
    stock       REAL NOT NULL DEFAULT 0,
    min_stock   REAL NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clients (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    phone      TEXT NOT NULL DEFAULT '',
    email      TEXT NOT NULL DEFAULT '',
    address    TEXT NOT NULL DEFAULT '',
    notes      TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sales (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id   INTEGER,
    client_name TEXT NOT NULL DEFAULT '',
    total       REAL NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sale_items (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id      INTEGER NOT NULL,
    product_id   INTEGER,
    product_code TEXT NOT NULL,
    product_name TEXT NOT NULL,
    quantity     REAL NOT NULL DEFAULT 0,
    unit_price   REAL NOT NULL DEFAULT 0,
    subtotal     REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    full_name     TEXT NOT NULL DEFAULT '',
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_products_name ON products (name);
CREATE INDEX IF NOT EXISTS idx_products_category ON products (category);
CREATE INDEX IF NOT EXISTS idx_sales_created ON sales (created_at);
CREATE INDEX IF NOT EXISTS idx_sale_items_sale ON sale_items (sale_id);
"""


def resource_path(relative_path):
    """Resuelve rutas absolutas a recursos exista el programa empaquetado o no."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(base, relative_path))


def get_data_dir():
    """Directorio de datos del usuario (siempre ruta absoluta y escribible)."""
    base = os.environ.get("APPDATA")
    if base:
        folder = os.path.join(os.path.abspath(base), APP_NAME)
    else:
        folder = os.path.join(os.path.abspath(os.path.expanduser("~")), f".{APP_NAME.lower()}")
    os.makedirs(folder, exist_ok=True)
    return folder


def get_db_path():
    return os.path.abspath(os.path.join(get_data_dir(), "invendesk.db"))


_conn = None


def get_conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(get_db_path())
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA foreign_keys = ON")
    return _conn


def initialize_database():
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()


def now_iso():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")