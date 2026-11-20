# Invendesk — Copyright (C) 2026 Luis A Ayala Rosa
# Licensed under the GNU GPL, version 3 or later. See LICENSE.

import csv
import os
from datetime import date, timedelta

import tkinter as tk
from tkinter import filedialog, ttk

import db
import ui
from validation import parse_date

PERIODS = [
    ("hoy", "Hoy"),
    ("semana", "Esta semana"),
    ("mes", "Este mes"),
    ("todo", "Todo el historial"),
    ("custom", "Rango personalizado"),
]


class ReportsScreen(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Content.TFrame")
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=14)
        self._build_sales_tab()
        self._build_inventory_tab()
        self._build_clients_tab()
        self.refresh()

    # ---------- Ventas ----------
    def _build_sales_tab(self):
        tab = ttk.Frame(self.notebook, style="Content.TFrame")
        self.notebook.add(tab, text="  Ventas  ")

        bar = ttk.Frame(tab, style="Content.TFrame")
        bar.pack(fill="x", padx=10, pady=10)
        ttk.Label(bar, text="Período:").pack(side="left")
        self.period_var = tk.StringVar(value="mes")
        combo = ttk.Combobox(bar, textvariable=self.period_var, state="readonly", width=20,
                             values=[k for _, k in PERIODS])
        combo.pack(side="left", padx=8)
        combo.bind("<<ComboboxSelected>>", lambda e: self._toggle_custom())
        ttk.Label(bar, text="Desde:").pack(side="left", padx=(14, 4))
        self.from_var = tk.StringVar(value=(date.today() - timedelta(days=7)).isoformat())
        self.from_entry = ttk.Entry(bar, textvariable=self.from_var, width=12)
        self.from_entry.pack(side="left")
        ttk.Label(bar, text="Hasta:").pack(side="left", padx=(14, 4))
        self.to_var = tk.StringVar(value=date.today().isoformat())
        self.to_entry = ttk.Entry(bar, textvariable=self.to_var, width=12)
        self.to_entry.pack(side="left")
        ttk.Button(bar, text="Aplicar", command=self._load_sales_report).pack(side="left", padx=14)
        ttk.Button(bar, text="Exportar CSV", command=self._export_sales).pack(side="right")

        self._set_custom_enabled(False)
        self.sales_summary = tk.StringVar()
        ttk.Label(tab, textvariable=self.sales_summary, font=("Segoe UI", 10, "bold"),
                  padding=(12, 4)).pack(anchor="w")

        split = tk.PanedWindow(tab, orient="vertical", sashrelief="flat")
        split.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        frame1, self.days_tree = ui.make_tree(split, ["Día", "Ventas", "Ingresos"], [150, 110, 150],
                                              heights=10, packing=False, title="Ingresos por día")
        frame2, self.products_tree = ui.make_tree(
            split, ["Código", "Producto", "Unidades", "Ventas", "Ingresos"], [110, 260, 90, 90, 120],
            heights=10, stretch=("Producto",), packing=False, title="Productos vendidos",
        )
        split.add(frame1)
        split.add(frame2)

    def _toggle_custom(self):
        name = dict(PERIODS).get(self.period_var.get(), "")
        self._set_custom_enabled(name == "Rango personalizado")
        if name == "Rango personalizado":
            self._load_sales_report()

    def _set_custom_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        self.from_entry.config(state=state)
        self.to_entry.config(state=state)

    def _collect_boundaries(self):
        name = dict(PERIODS).get(self.period_var.get(), "")
        today = date.today()
        if name == "Hoy":
            return today, today
        if name == "Esta semana":
            start = today - timedelta(days=today.weekday())
            return start, today
        if name == "Este mes":
            return today.replace(day=1), today
        if name == "Rango personalizado":
            ok1, d1, e1 = parse_date(self.from_var.get(), "Desde")
            ok2, d2, e2 = parse_date(self.to_var.get(), "Hasta")
            if not (ok1 and ok2):
                ui.warn("Reporte", f"{e1}\n{e2}")
                return None, None
            if d1 > d2:
                ui.warn("Reporte", "La fecha 'Desde' es posterior a 'Hasta'.")
                return None, None
            return d1, d2
        return None, None

    def _load_sales_report(self):
        start, end = self._collect_boundaries()
        if start is None and end is None and self.period_var.get() != "Todo el historial":
            return
        conn = db.get_conn()
        cond, params = "", []
        if start is not None and end is not None:
            cond = "WHERE date(created_at) BETWEEN ? AND ?"
            params = [start.isoformat(), end.isoformat()]

        sales = conn.execute(
            f"SELECT COUNT(*) AS n, COALESCE(SUM(total),0) AS total FROM sales {cond}", params
        ).fetchone()
        days = conn.execute(
            f"""SELECT date(created_at) AS day, COUNT(*) AS n, COALESCE(SUM(total),0) AS total
                FROM sales {cond} GROUP BY day ORDER BY day DESC LIMIT 60""",
            params,
        ).fetchall()
        products = conn.execute(
            f"""SELECT product_code, product_name, SUM(quantity) AS qty, COUNT(DISTINCT sale_id) AS sales,
                       SUM(subtotal) AS revenue
                FROM sale_items i JOIN sales s ON s.id = i.sale_id {cond}
                GROUP BY product_code, product_name ORDER BY revenue DESC LIMIT 100""",
            params,
        ).fetchall()

        avg = (sales["total"] / sales["n"]) if sales["n"] else 0
        self.sales_summary.set(
            f"Ventas: {sales['n']}   •   Ingresos: {ui.fmt_money(sales['total'])}   •   Ticket promedio: {ui.fmt_money(avg)}"
        )
        ui.clear_tree(self.days_tree)
        for d in days:
            self.days_tree.insert("", "end", values=(d["day"], d["n"], ui.fmt_money(d["total"])))
        ui.clear_tree(self.products_tree)
        for p in products:
            self.products_tree.insert(
                "", "end",
                values=(p["product_code"], p["product_name"], ui.fmt_qty(p["qty"]), p["sales"], ui.fmt_money(p["revenue"])),
            )

    def _export_sales(self):
        start, end = self._collect_boundaries()
        conn = db.get_conn()
        cond, params = "", []
        if start is not None and end is not None:
            cond = "WHERE date(created_at) BETWEEN ? AND ?"
            params = [start.isoformat(), end.isoformat()]
        rows = conn.execute(
            f"""SELECT s.id, s.created_at, s.client_name, i.product_code, i.product_name,
                       i.quantity, i.unit_price, i.subtotal
                FROM sales s JOIN sale_items i ON i.sale_id = s.id {cond}
                ORDER BY s.id DESC""",
            params,
        ).fetchall()
        path = filedialog.asksaveasfilename(
            title="Exportar ventas a CSV", defaultextension=".csv",
            initialfile="ventas.csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        with open(os.path.abspath(path), "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh)
            w.writerow(["Venta", "Fecha", "Cliente", "Código", "Producto", "Cantidad", "Precio", "Subtotal"])
            for r in rows:
                w.writerow([r["id"], r["created_at"], r["client_name"], r["product_code"],
                            r["product_name"], r["quantity"], r["unit_price"], r["subtotal"]])
        ui.info("Exportar", f"Ventas exportadas a:\n{os.path.abspath(path)}")

    # ---------- Inventario ----------
    def _build_inventory_tab(self):
        tab = ttk.Frame(self.notebook, style="Content.TFrame")
        self.notebook.add(tab, text="  Inventario  ")
        bar = ttk.Frame(tab, style="Content.TFrame")
        bar.pack(fill="x", padx=10, pady=10)
        self.stock_filter_var = tk.StringVar(value="bajo")
        for text, val in [("Solo stock bajo", "bajo"), ("Todos los productos", "todo")]:
            ttk.Radiobutton(bar, text=text, value=val, variable=self.stock_filter_var,
                            command=self._load_stock_report).pack(side="left", padx=6)
        ttk.Button(bar, text="Exportar CSV", command=self._export_stock).pack(side="right")
        self.stock_frame, self.stock_tree = ui.make_tree(
            tab, ["Código", "Nombre", "Categoría", "Stock", "Stock mín.", "Valor (costo)", "Valor (venta)"],
            [110, 260, 120, 80, 90, 120, 120], heights=18, stretch=("Nombre",),
        )

    def _load_stock_report(self):
        order = """SELECT code, name, category, stock, min_stock, cost_price, sale_price
                   FROM products ORDER BY name COLLATE NOCASE"""
        rows = db.get_conn().execute(order).fetchall()
        if self.stock_filter_var.get() == "bajo":
            rows = [r for r in rows if float(r["stock"] or 0) <= float(r["min_stock"] or 0)]
        ui.clear_tree(self.stock_tree)
        for r in rows:
            val_cost = float(r["stock"] or 0) * float(r["cost_price"] or 0)
            val_sale = float(r["stock"] or 0) * float(r["sale_price"] or 0)
            self.stock_tree.insert(
                "", "end",
                values=(r["code"], r["name"], r["category"], ui.fmt_qty(r["stock"]),
                        ui.fmt_qty(r["min_stock"]), ui.fmt_money(val_cost), ui.fmt_money(val_sale)),
            )

    def _export_stock(self):
        path = filedialog.asksaveasfilename(
            title="Exportar reporte de stock a CSV", defaultextension=".csv",
            initialfile="reporte_stock.csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        cond = "WHERE stock <= min_stock" if self.stock_filter_var.get() == "bajo" else ""
        rows = db.get_conn().execute(
            f"SELECT code, name, category, stock, min_stock, cost_price, sale_price FROM products {cond} ORDER BY name COLLATE NOCASE"
        ).fetchall()
        with open(os.path.abspath(path), "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh)
            w.writerow(["Código", "Nombre", "Categoría", "Stock", "Stock mín.", "Valor costo", "Valor venta"])
            for r in rows:
                w.writerow([r["code"], r["name"], r["category"], r["stock"], r["min_stock"],
                            round(float(r["stock"] or 0) * float(r["cost_price"] or 0), 2),
                            round(float(r["stock"] or 0) * float(r["sale_price"] or 0), 2)])
        ui.info("Exportar", f"Reporte guardado en:\n{os.path.abspath(path)}")

    # ---------- Clientes ----------
    def _build_clients_tab(self):
        tab = ttk.Frame(self.notebook, style="Content.TFrame")
        self.notebook.add(tab, text="  Clientes  ")
        bar = ttk.Frame(tab, style="Content.TFrame")
        bar.pack(fill="x", padx=10, pady=10)
        ttk.Button(bar, text="Exportar CSV", command=self._export_clients).pack(side="right")
        self.clients_frame, self.clients_tree = ui.make_tree(
            tab, ["Cliente", "Compras", "Total gastado"], [300, 120, 160], heights=18, stretch=("Cliente",),
        )

    def _load_clients_report(self):
        rows = db.get_conn().execute(
            """SELECT client_name, COUNT(*) AS n, COALESCE(SUM(total),0) AS total
               FROM sales GROUP BY client_name ORDER BY total DESC"""
        ).fetchall()
        ui.clear_tree(self.clients_tree)
        for r in rows:
            self.clients_tree.insert("", "end", values=(r["client_name"] or "Mostrador", r["n"], ui.fmt_money(r["total"])))

    def _export_clients(self):
        path = filedialog.asksaveasfilename(
            title="Exportar clientes a CSV", defaultextension=".csv",
            initialfile="clientes.csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        rows = db.get_conn().execute(
            "SELECT client_name, COUNT(*) AS n, SUM(total) AS total FROM sales GROUP BY client_name ORDER BY total DESC"
        ).fetchall()
        with open(os.path.abspath(path), "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh)
            w.writerow(["Cliente", "Compras", "Total"])
            for r in rows:
                w.writerow([r["client_name"] or "Mostrador", r["n"], r["total"]])
        ui.info("Exportar", f"Clientes exportados a:\n{os.path.abspath(path)}")

    # ---------- Refresh ----------
    def refresh(self):
        self._load_sales_report()
        self._load_stock_report()
        self._load_clients_report()
