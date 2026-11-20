import tkinter as tk
from tkinter import ttk

import db
import ui
from validation import parse_number

COLUMNS = ["ID", "Fecha", "Cliente", "Artículos", "Total"]
WIDTHS = [60, 150, 220, 90, 110]


class SaleDetailDialog(tk.Toplevel):
    def __init__(self, parent, sale_id):
        super().__init__(parent)
        self.title(f"Detalle de venta #{sale_id}")
        self.geometry("620x360")
        self.transient(parent)
        conn = db.get_conn()
        sale = conn.execute("SELECT * FROM sales WHERE id = ?", (sale_id,)).fetchone()
        lines = conn.execute("SELECT * FROM sale_items WHERE sale_id = ?", (sale_id,)).fetchall()
        body = ttk.Frame(self, padding=12)
        body.pack(fill="both", expand=True)
        ttk.Label(
            body,
            text=f"Venta #{sale['id']} — {sale['created_at']} — Cliente: {sale['client_name'] or 'Mostrador'}",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 8))
        _, tree = ui.make_tree(body, ["Código", "Producto", "Cant.", "Precio", "Subtotal"], [90, 260, 70, 100, 110], stretch=("Producto",))
        for ln in lines:
            tree.insert(
                "", "end",
                values=(ln["product_code"], ln["product_name"], ui.fmt_qty(ln["quantity"]),
                        ui.fmt_money(ln["unit_price"]), ui.fmt_money(ln["subtotal"])),
            )
        ttk.Label(body, text=f"TOTAL: {ui.fmt_money(sale['total'])}", font=("Segoe UI", 12, "bold")).pack(anchor="e", pady=(8, 0))


class SalesScreen(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Content.TFrame")
        self.cart = []
        self._build_top()
        self._build_cart()
        self._build_history()
        self.refresh()

    # ---------- UI ----------
    def _build_top(self):
        head = ttk.LabelFrame(self, text=" Registrar venta ", padding=10)
        head.pack(fill="x", padx=14, pady=(14, 8))
        head.columnconfigure(1, weight=1)

        ttk.Label(head, text="Cliente:").grid(row=0, column=0, sticky="e", padx=(0, 8), pady=4)
        self.client_combo = ttk.Combobox(head, state="readonly", width=40)
        self.client_combo.grid(row=0, column=1, sticky="we", pady=4, padx=(0, 16))

        ttk.Label(head, text="Producto:").grid(row=1, column=0, sticky="e", padx=(0, 8), pady=4)
        self.product_combo = ttk.Combobox(head, state="readonly", width=40)
        self.product_combo.grid(row=1, column=1, sticky="we", pady=4, padx=(0, 16))

        ttk.Label(head, text="Cantidad:").grid(row=2, column=0, sticky="e", padx=(0, 8), pady=4)
        self.qty_var = tk.StringVar(value="1")
        ent = ttk.Entry(head, textvariable=self.qty_var, width=10)
        ent.grid(row=2, column=1, sticky="w", pady=4, padx=(0, 16))
        ent.bind("<Return>", lambda e: self.add_line())
        ttk.Button(head, text="Agregar", command=self.add_line).grid(row=2, column=2, sticky="w")

        self._client_map = {}
        self._product_map = {}

    def _build_cart(self):
        cart_frame, self.cart_tree = ui.make_tree(
            self, ["Código", "Producto", "Precio", "Cantidad", "Subtotal"], [110, 300, 100, 80, 110],
            heights=8, stretch=("Producto",),
        )
        bar = ttk.Frame(self, style="Content.TFrame")
        bar.pack(fill="x", padx=14)
        self.total_var = tk.StringVar(value="Total: $0.00")
        ttk.Label(bar, textvariable=self.total_var, font=("Segoe UI", 14, "bold")).pack(side="left")
        ttk.Button(bar, text="Quitar línea", command=self.remove_line).pack(side="left", padx=10)
        ttk.Button(bar, text="Registrar venta", command=self.register_sale).pack(side="right")

    def _build_history(self):
        self.frame, self.history_tree = ui.make_tree(self, COLUMNS, WIDTHS, heights=6, stretch=("Cliente",))
        self.history_tree.bind("<Double-1>", lambda e: self.show_detail())

    # ---------- Estado ----------
    def refresh(self):
        conn = db.get_conn()
        clients = conn.execute("SELECT * FROM clients ORDER BY name COLLATE NOCASE").fetchall()
        products = conn.execute(
            "SELECT * FROM products ORDER BY name COLLATE NOCASE"
        ).fetchall()

        self._client_map = {}
        client_labels = ["— Cliente mostrador —"]
        for c in clients:
            label = f"{c['name']}  ({c['phone'] or 'sin teléfono'})"
            client_labels.append(label)
            self._client_map[label] = c
        self.client_combo["values"] = client_labels
        if not self.client_combo.get():
            self.client_combo.current(0)

        self._product_map = {}
        values = []
        for p in products:
            label = f"{p['code']} | {p['name']} ({ui.fmt_qty(p['stock'])} disp.)"
            self._product_map[label] = p
            values.append(label)
        self.product_combo["values"] = values

        self._load_history()

    def _load_history(self):
        rows = db.get_conn().execute(
            """SELECT s.id, s.created_at, s.client_name,
                      (SELECT COUNT(*) FROM sale_items si WHERE si.sale_id = s.id) AS items,
                      s.total
               FROM sales s ORDER BY s.id DESC LIMIT 200"""
        ).fetchall()
        ui.clear_tree(self.history_tree)
        for r in rows:
            self.history_tree.insert(
                "", "end",
                values=(r["id"], r["created_at"], r["client_name"] or "Mostrador", r["items"], ui.fmt_money(r["total"])),
            )

    # ---------- Acciones carrito ----------
    def add_line(self):
        label = self.product_combo.get()
        product = self._product_map.get(label)
        if not product:
            ui.warn("Venta", "Selecciona un producto.")
            return
        ok, qty, msg = parse_number(self.qty_var.get(), "Cantidad", allow_negative=False, allow_zero=False)
        if not ok:
            ui.warn("Venta", msg)
            return
        reserved = sum(l["quantity"] for l in self.cart if l["product_id"] == product["id"])
        available = float(product["stock"] or 0) - reserved
        if qty > available:
            ui.warn("Venta", f"No hay suficiente stock de '{product['name']}'.\nDisponible: {ui.fmt_qty(available)}")
            return
        self.cart.append({
            "product_id": product["id"],
            "code": product["code"],
            "name": product["name"],
            "unit_price": float(product["sale_price"] or 0),
            "quantity": qty,
        })
        self._render_cart()
        self.qty_var.set("1")

    def remove_line(self):
        values, idx = ui.selected_row(self.cart_tree)
        if values is None:
            return
        if 0 <= idx < len(self.cart):
            del self.cart[idx]
        self._render_cart()

    def _render_cart(self):
        ui.clear_tree(self.cart_tree)
        total = 0.0
        for l in self.cart:
            subtotal = round(l["unit_price"] * l["quantity"], 2)
            l["subtotal"] = subtotal
            total += subtotal
            self.cart_tree.insert(
                "", "end",
                values=(l["code"], l["name"], ui.fmt_money(l["unit_price"]), ui.fmt_qty(l["quantity"]), ui.fmt_money(subtotal)),
            )
        self.total_var.set(f"Total: {ui.fmt_money(total)}")

    def _selected_client(self):
        label = self.client_combo.get()
        return self._client_map.get(label)

    # ---------- Acciones venta ----------
    def register_sale(self):
        if not self.cart:
            ui.warn("Venta", "El carrito está vacío.")
            return
        conn = db.get_conn()
        for l in self.cart:
            cur = conn.execute("SELECT stock FROM products WHERE id = ?", (l["product_id"],)).fetchone()
            stock = cur["stock"] if cur else 0
            if float(stock) < l["quantity"]:
                ui.warn("Venta", f"Stock insuficiente de '{l['name']}' (disponible: {ui.fmt_qty(stock)}).")
                return

        client = self._selected_client()
        client_id = client["id"] if client else None
        client_name = client["name"] if client else "Mostrador"
        total = round(sum(l["subtotal"] for l in self.cart), 2)

        try:
            conn.execute("BEGIN")
            cur = conn.execute(
                "INSERT INTO sales (client_id, client_name, total, created_at) VALUES (?, ?, ?, ?)",
                (client_id, client_name, total, db.now_iso()),
            )
            sale_id = cur.lastrowid
            for l in self.cart:
                conn.execute(
                    "INSERT INTO sale_items (sale_id, product_id, product_code, product_name, quantity, unit_price, subtotal) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (sale_id, l["product_id"], l["code"], l["name"], l["quantity"], l["unit_price"], l["subtotal"]),
                )
                conn.execute(
                    "UPDATE products SET stock = stock - ? WHERE id = ?",
                    (l["quantity"], l["product_id"]),
                )
            conn.commit()
        except Exception as exc:  # noqa: BLE001
            conn.rollback()
            ui.error("Venta", f"No se pudo registrar la venta:\n{exc}")
            return

        ui.info("Venta registrada", f"Venta #{sale_id} registrada.\nTotal: {ui.fmt_money(total)}")
        self.cart = []
        self._render_cart()
        self.refresh()

    def show_detail(self):
        values, _ = ui.selected_row(self.history_tree)
        if values:
            SaleDetailDialog(self.winfo_toplevel(), int(values[0]))