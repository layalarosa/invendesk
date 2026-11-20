# Invendesk — Copyright (C) 2026 Luis A Ayala Rosa
# Licensed under the GNU GPL, version 3 or later. See LICENSE.

import os
import re

from openpyxl import Workbook, load_workbook

import db
from validation import clean_text, validate_product

ALIASES = {
    "code": ["code", "codigo", "código", "sku", "clave", "cod"],
    "name": ["name", "nombre", "producto", "descripcion corta", "descripción corta"],
    "category": ["category", "categoria", "categoría", "grupo", "departamento"],
    "description": ["description", "descripcion", "descripción", "detalle", "nota"],
    "cost_price": ["cost_price", "cost price", "costo", "precio costo", "precio_compra",
                   "precio de compra", "precio compra", "costo unitario", "precio de costo"],
    "sale_price": ["sale_price", "sale price", "precio", "precio_venta", "precio de venta",
                   "precio venta", "precio publico", "precio público", "precio de lista", "pvp"],
    "stock": ["stock", "existencia", "cantidad", "cantidad disponible", "unidades", "existencias"],
    "min_stock": ["min_stock", "min stock", "stock minimo", "stock mínimo", "stock_min",
                  "minimo", "mínimo", "stock de alerta", "alerta", "min"],
}

REQUIRED_FIELDS = ["code", "name"]


def _normalize_key(value):
    if value is None:
        return ""
    s = clean_text(value, max_len=60).lower()
    s = re.sub(r"[_\-/()]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _column_aliases(field):
    return {_normalize_key(a) for a in ALIASES[field]}


def _map_headers(header_row):
    mapping = {}
    for idx, raw in enumerate(header_row):
        key = _normalize_key(raw)
        if not key:
            continue
        for field in ALIASES:
            if key in _column_aliases(field) or key.replace(" ", "") in {
                a.replace(" ", "") for a in ALIASES[field]
            }:
                mapping.setdefault(field, idx)
                break
    return mapping


def find_header_row(ws, max_scan=15):
    for r in range(1, min(ws.max_row, max_scan) + 1):
        cells = [_normalize_key(c.value) for c in ws[r]]
        hits = 0
        for field in ALIASES:
            for alias in _column_aliases(field):
                if alias in cells:
                    hits += 1
                    break
        if hits >= 3:
            return r
    return None


def _row_is_empty(row):
    for v in row:
        if v is not None:
            if not (isinstance(v, str) and not v.strip()):
                return False
    return True


def import_from_excel(path, upsert=False):
    """Importa productos desde un .xlsx. Devuelve dict resumen con errores por fila."""
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"No existe el archivo: {path}")
    if not path.lower().endswith((".xlsx", ".xlsm")):
        raise ValueError("El archivo debe ser .xlsx o .xlsm (Excel moderno)")

    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb.active

    header_row = find_header_row(ws)
    if header_row is None:
        wb.close()
        raise ValueError(
            "No se encontró una fila de encabezados reconocible. "
            "Se requieren al menos las columnas: Código y Nombre."
        )

    mapping = _map_headers([c.value for c in ws[header_row]])
    missing = [f for f in REQUIRED_FIELDS if f not in mapping]
    if missing:
        wb.close()
        raise ValueError(f"Faltan columnas obligatorias: {', '.join(missing)}")

    conn = db.get_conn()
    summary = {"inserted": 0, "updated": 0, "errors": [], "rows_read": 0}

    insert_sql = (
        "INSERT INTO products (code, name, category, description, cost_price, sale_price, stock, min_stock, created_at) "
        "VALUES (:code, :name, :category, :description, :cost_price, :sale_price, :stock, :min_stock, :created_at)"
    )
    update_sql = (
        "UPDATE products SET name=:name, category=:category, description=:description, "
        "cost_price=:cost_price, sale_price=:sale_price, stock=:stock, min_stock=:min_stock "
        "WHERE code=:code"
    )

    for r in range(header_row + 1, ws.max_row + 1):
        cells = [c.value for c in ws[r]]
        summary["rows_read"] += 1
        if _row_is_empty(cells):
            continue
        rec = {}
        for field, idx in mapping.items():
            rec[field] = cells[idx] if idx < len(cells) else None
        ok, clean, errs = validate_product(rec)
        if not ok:
            clean_code = clean.get("code") or "-"
            summary["errors"].append((r + 1, f"Código {clean_code}: {'; '.join(sorted(set(errs)))}"))
            continue
        clean["created_at"] = db.now_iso()
        try:
            existing = conn.execute(
                "SELECT id FROM products WHERE code = ?", (clean["code"],)
            ).fetchone()
            if existing:
                if upsert:
                    conn.execute(update_sql, clean)
                    summary["updated"] += 1
                else:
                    summary["errors"].append((r + 1, f"Código {clean['code']} ya existe en la base"))
            else:
                conn.execute(insert_sql, clean)
                summary["inserted"] += 1
        except Exception as exc:  # noqa: BLE001
            conn.rollback()
            summary["errors"].append((r + 1, f"Error al guardar: {exc}"))

    conn.commit()
    wb.close()
    return summary


def create_template(path):
    """Crea un archivo Excel de ejemplo con los encabezados reconocibles."""
    path = os.path.abspath(path)
    wb = Workbook()
    ws = wb.active
    ws.title = "Productos"
    headers = [
        ("Código", "COD-001"),
        ("Nombre", "Producto de ejemplo"),
        ("Categoría", "General"),
        ("Descripción", "Descripción opcional"),
        ("Precio de costo", 25.5),
        ("Precio de venta", 45.0),
        ("Stock", 100),
        ("Stock mínimo", 10),
    ]
    ws.append([h[0] for h in headers])
    ws.append([h[1] for h in headers])
    widths = [16, 30, 16, 40, 16, 16, 12, 14]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w
    wb.save(path)
    return path
