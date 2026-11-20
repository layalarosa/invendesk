# Invendesk — Copyright (C) 2026 Luis A Ayala Rosa
# Licensed under the GNU GPL, version 3 or later. See LICENSE.

import math
from datetime import datetime

MAX_TEXT = 200


def clean_text(value, default="", max_len=MAX_TEXT, label=""):
    """Limpia texto que puede venir sucio: None, numéricos, espacios, basura."""
    if value is None:
        return default
    if isinstance(value, bool):
        value = "1" if value else ""
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    if max_len and len(value) > max_len:
        value = value[:max_len].rstrip()
    return value


def parse_number(value, label, allow_negative=False, allow_zero=True, whole=False):
    """Parsea un número tolerando suciedad. Devuelve (ok, valor, mensaje_error)."""
    if value is None:
        return False, None, f"{label}: valor vacío"
    if isinstance(value, bool):
        return False, None, f"{label}: valor booleano no válido"
    if isinstance(value, (int, float)):
        num = float(value)
    else:
        s = str(value).strip().replace(" ", "").replace("\u00a0", "")
        if s in ("", "-", "+", ".", ",", "--", "++"):
            return False, None, f"{label}: '{value}' no es un número"
        if "," in s and "." in s:
            if s.rfind(",") > s.rfind("."):
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif "," in s:
            s = s.replace(",", ".")
        try:
            num = float(s)
        except (ValueError, TypeError):
            return False, None, f"{label}: '{value}' no es un número válido"
    if not math.isfinite(num):
        return False, None, f"{label}: número inválido"
    if not allow_negative and num < 0:
        return False, None, f"{label}: no puede ser negativo"
    if not allow_zero and num == 0:
        return False, None, f"{label}: debe ser mayor que cero"
    if whole and num != int(num):
        return False, None, f"{label}: debe ser un entero"
    return True, num, ""


def validate_email(value):
    s = clean_text(value)
    if not s:
        return True, s, ""
    if "@" not in s or "." not in s.split("@")[-1]:
        return False, s, "Correo electrónico no válido"
    return True, s, ""


def parse_date(value, label):
    """Parsea fechas en varios formatos. Devuelve (ok, date, mensaje_error)."""
    if value is None:
        return False, None, f"{label}: valor vacío"
    if isinstance(value, datetime):
        return True, value.date(), ""
    s = str(value).strip()
    if not s:
        return False, None, f"{label}: valor vacío"
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return True, datetime.strptime(s, fmt).date(), ""
        except ValueError:
            continue
    return False, None, f"{label}: fecha inválida (use AAAA-MM-DD)"


def validate_product(row):
    """Valida un dict de producto con llaves canónicas. Devuelve (ok, limpio, errores).

    Obligatorias: code, name, sale_price. Las numéricas opcionales vacías valen 0.
    """
    errs = []
    out = {}
    code = clean_text(row.get("code", ""), max_len=40, label="Código")
    if not code:
        errs.append("Código es obligatorio")
    out["code"] = code.upper()

    name = clean_text(row.get("name", ""), max_len=120, label="Nombre")
    if not name:
        errs.append("Nombre es obligatorio")
    out["name"] = name

    out["category"] = clean_text(row.get("category", ""), max_len=60, label="Categoría")
    out["description"] = clean_text(row.get("description", ""), max_len=600, label="Descripción")

    optional_numeric = {
        "cost_price": "Precio de costo",
        "min_stock": "Stock mínimo",
    }
    for field, label in optional_numeric.items():
        out[field] = _optional_number(row.get(field, ""), label, errs)

    ok, val, msg = parse_number(row.get("sale_price", ""), "Precio de venta")
    if not ok:
        errs.append(msg)
        val = 0.0
    out["sale_price"] = val

    out["stock"] = _optional_number(row.get("stock", ""), "Stock", errs)

    if errs:
        return False, out, errs
    return True, out, []


def _optional_number(value, label, errs):
    """Número opcional: vacío o None => 0; texto no numérico => error."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return 0.0
    ok, val, msg = parse_number(value, label)
    if not ok:
        errs.append(msg)
        return 0.0
    return val


def validate_client(row):
    errs = []
    out = {}
    name = clean_text(row.get("name", ""), max_len=120, label="Nombre")
    if not name:
        errs.append("Nombre es obligatorio")
    out["name"] = name
    out["phone"] = clean_text(row.get("phone", ""), max_len=40, label="Teléfono")
    ok, email, msg = validate_email(row.get("email", ""))
    if not ok:
        errs.append(msg)
    out["email"] = email
    out["address"] = clean_text(row.get("address", ""), max_len=200, label="Dirección")
    out["notes"] = clean_text(row.get("notes", ""), max_len=600, label="Notas")
    if errs:
        return False, out, errs
    return True, out, []
