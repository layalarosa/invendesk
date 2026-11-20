# Invendesk — Copyright (C) 2026 Luis A Ayala Rosa
# Licensed under the GNU GPL, version 3 or later. See LICENSE.

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import db
import excel_import
import ui
from validation import validate_product

COLUMNS = ["ID", "Código", "Nombre", "Categoría", "Costo", "Venta", "Stock", "Stock mín."]
WIDTHS = [50, 110, 260, 120, 90, 90, 80, 90]


class ProductDialog(tk.Toplevel):
    def __init__(self, parent, product=None):
        super().__init__(parent)
        self.title("Editar producto" if product else "Nuevo producto")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._vars = {
            k: tk.StringVar()
            for k in ("code", "name", "category", "description", "cost_price", "sale_price", "stock", "min_stock")
        }
        if product:
            self.product_id = product["id"]
            for k in self._vars:
                self._vars[k].set(product[k])
        else:
            self.product_id = None

        body = ttk.Frame(self, padding=14)
        body.pack(fill="both", expand=True)
        fields = [
            ("Código *", "code"), ("Nombre *", "name"), ("Categoría", "category"),
            ("Descripción", "description"), ("Precio de costo", "cost_price"),
            ("Precio de venta *", "sale_price"), ("Stock", "stock"), ("Stock mínimo", "min_stock"),
        ]
        for i, (label, key) in enumerate(fields[:4]):
            ui.add_form_entry(body, label, self._vars[key], i, width=48)
        body.rowconfigure(4, weight=0)
        buttons = ttk.Frame(body)
        buttons.grid(row=6, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text="Cancelar", command=self.destroy).pack(side="left", padx=6)
        ttk.Button(buttons, text="Guardar", command=self._save).pack(side="left")

        self.bind("<Return>", lambda e: self._save())
        self.wait_visibility()
        self.lift()
        self.focus_set()

    def _read_fields(self):
        return {k: var.get() for k, var in self._vars.items()}

    def _save(self):
        ok, clean, errs = validate_product(self._read_fields())
        if not ok:
            ui.error("Datos inválidos", "\n".join(f"• {e}" for e in errs))
            return
        conn = db.get_conn()
        dup = conn.execute(
            "SELECT id FROM products WHERE code = ? AND id != ?",
            (clean["code"], self.product_id or -1),
        ).fetchone()
        if dup:
            ui.error("Datos inválidos", f"Ya existe un producto con el código '{clean['code']}'.")
            return
        clean["id"] = self.product_id
        clean["created_at"] = db.now_iso()
        if self.product_id:
            conn.execute(
                "UPDATE products SET code=:code, name=:name, category=:category, description=:description, "
                "cost_price=:cost_price, sale_price=:sale_price, stock=:stock, min_stock=:min_stock "
                "WHERE id=:id",
                clean,
            )
        else:
            conn.execute(
                "INSERT INTO products (code, name, category, description, cost_price, sale_price, stock, min_stock, created_at) "
                "VALUES (:code, :name, :category, :description, :cost_price, :sale_price, :stock, :min_stock, :created_at)",
                clean,
            )
        conn.commit()
        self.destroy()


class ImportDialog(tk.Toplevel):
    def __init__(self, parent, on_done):
        super().__init__(parent)
        self.title("Importar productos desde Excel")
        self.geometry("640x420")
        self.transient(parent)
        self.on_done = on_done
        self._build()
        self.grab_set()

    def _build(self):
        bar = ttk.Frame(self, padding=(14, 14, 14, 0))
        bar.pack(fill="x")
        self.path_var = tk.StringVar()
        ui.add_form_entry(bar, "Archivo .xlsx", self.path_var, 0, width=52)
        ttk.Button(bar, text="Examinar…", command=self._browse).grid(row=0, column=2, padx=4)
        ttk.Button(bar, text="Descargar plantilla…", command=self._template).grid(row=0, column=3, padx=4)

        opts = ttk.Frame(self, padding=(120, 4, 14, 0))
        opts.pack(fill="x")
        self.upsert_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts, text="Actualizar productos que ya existen (por código)", variable=self.upsert_var).pack(anchor="w")

        note = ttk.Label(
            self,
            text="Reconoce columnas como: Código, Nombre, Categoría, Descripción, "
                 "Precio de costo, Precio de venta, Stock y Stock mínimo.",
            foreground="#6b7280",
        )
        note.pack(padx=16, pady=(2, 8), anchor="w")

        res_frame, self.result_tree = ui.make_tree(
            self, ["Acción / Filas con error"], [600], heights=9
        )
        ttk.Button(self, text="Importar", command=self._run).pack(pady=(0, 12))

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Seleccionar archivo de Excel",
            filetypes=[("Excel", "*.xlsx *.xlsm"), ("Todos los archivos", "*.*")],
        )
        if path:
            self.path_var.set(os.path.abspath(path))

    def _template(self):
        path = filedialog.asksaveasfilename(
            title="Guardar plantilla", defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")], initialfile="plantilla_inventario.xlsx",
        )
        if not path:
            return
        try:
            excel_import.create_template(path)
            ui.info("Plantilla", f"Plantilla guardada en:\n{path}")
        except Exception as exc:  # noqa: BLE001
            ui.error("Error", f"No se pudo guardar la plantilla:\n{exc}")

    def _run(self):
        if not self.path_var.get().strip():
            ui.warn("Importar", "Selecciona un archivo de Excel primero.")
            return
        try:
            summary = excel_import.import_from_excel(self.path_var.get().strip(), upsert=self.upsert_var.get())
        except Exception as exc:  # noqa: BLE001
            ui.error("Error de importación", str(exc))
            return
        ui.clear_tree(self.result_tree)
        self.result_tree.insert("", "end", values=(f"Filas procesadas: {summary['rows_read']}",))
        self.result_tree.insert("", "end", values=(f"Productos insertados: {summary['inserted']}",))
        self.result_tree.insert("", "end", values=(f"Productos actualizados: {summary['updated']}",))
        self.result_tree.insert("", "end", values=(f"Filas con error: {len(summary['errors'])}",))
        if summary["errors"]:
            self.result_tree.insert("", "end", values=("—",))
            for row, msg in summary["errors"][:200]:
                self.result_tree.insert("", "end", values=(f"Fila {row}: {msg}",))
        self.on_done()


class InventoryScreen(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Content.TFrame")
        self._build_toolbar()
        self._build_table()
        self.refresh()

    def _build_toolbar(self):
        bar = ttk.Frame(self, style="Content.TFrame")
        bar.pack(fill="x", padx=14, pady=(14, 10))
        ttk.Label(bar, text="Buscar:", font=("Segoe UI", 10)).pack(side="left")
        self.search_var = tk.StringVar()
        ent = ttk.Entry(bar, textvariable=self.search_var, width=36)
        ent.pack(side="left", padx=6, ipady=2)
        ent.bind("<KeyRelease>", lambda e: self.refresh())
        btns = ttk.Frame(bar, style="Content.TFrame")
        btns.pack(side="right")
        ttk.Button(btns, text="+ Nuevo", command=self.add_product).pack(side="left", padx=4)
        ttk.Button(btns, text="Editar", command=self.edit_product).pack(side="left", padx=4)
        ttk.Button(btns, text="Eliminar", command=self.delete_product).pack(side="left", padx=4)
        ttk.Button(btns, text="Importar Excel", command=self.import_excel).pack(side="left", padx=4)

    def _build_table(self):
        self.frame, self.tree = ui.make_tree(self, COLUMNS, WIDTHS, heights=18, stretch=("Nombre",))
        self.tree.bind("<Double-1>", lambda e: self.edit_product())
        foot = ttk.Frame(self, style="Content.TFrame")
        foot.pack(fill="x", padx=16, pady=(0, 10))
        self.count_var = tk.StringVar()
        ttk.Label(foot, textvariable=self.count_var, foreground="#374151").pack(side="left")
        ttk.Button(foot, text="Exportar CSV", command=self.export_csv).pack(side="right")

    def refresh(self):
        term = "%" + self.search_var.get().strip() + "%"
        rows = db.get_conn().execute(
            """SELECT id, code, name, category, cost_price, sale_price, stock, min_stock
               FROM products
               WHERE code LIKE ? OR name LIKE ? OR category LIKE ?
               ORDER BY name COLLATE NOCASE ASC""",
            (term, term, term),
        ).fetchall()
        ui.clear_tree(self.tree)
        for r in rows:
            self.tree.insert(
                "", "end",
                values=(r["id"], r["code"], r["name"], r["category"],
                        ui.fmt_money(r["cost_price"]), ui.fmt_money(r["sale_price"]),
                        ui.fmt_qty(r["stock"]), ui.fmt_qty(r["min_stock"])),
            )
        low = sum(1 for r in rows if float(r["stock"] or 0) <= float(r["min_stock"] or 0))
        self.count_var.set(f"{len(rows)} producto(s) — {low} con stock bajo o agotado")

    def _product_from_selection(self):
        values, _ = ui.selected_row(self.tree)
        if not values:
            ui.warn("Inventario", "Selecciona un producto.")
            return None
        return db.get_conn().execute("SELECT * FROM products WHERE id = ?", (values[0],)).fetchone()

    def add_product(self):
        dlg = ProductDialog(self.winfo_toplevel())
        self.wait_window(dlg)
        self.refresh()

    def edit_product(self):
        product = self._product_from_selection()
        if product:
            dlg = ProductDialog(self.winfo_toplevel(), product)
            self.wait_window(dlg)
            self.refresh()

    def delete_product(self):
        product = self._product_from_selection()
        if not product:
            return
        if not ui.confirm(
            "Eliminar producto",
            f"¿Eliminar '{product['name']}' ({product['code']})?\nLas ventas históricas se conservan.",
        ):
            return
        conn = db.get_conn()
        conn.execute("DELETE FROM products WHERE id = ?", (product["id"],))
        conn.commit()
        self.refresh()

    def import_excel(self):
        dlg = ImportDialog(self.winfo_toplevel(), self.refresh)
        self.wait_window(dlg)

    def export_csv(self):
        path = filedialog.asksaveasfilename(
            title="Exportar inventario a CSV",
            defaultextension=".csv", initialfile="inventario.csv",
            filetypes=[("CSV", "*.csv")],
        )
        if not path:
            return
        rows = db.get_conn().execute(
            "SELECT code, name, category, cost_price, sale_price, stock, min_stock FROM products ORDER BY name COLLATE NOCASE"
        ).fetchall()
        import csv
        with open(os.path.abspath(path), "w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.writer(fh)
            writer.writerow(["Código", "Nombre", "Categoría", "Costo", "Venta", "Stock", "Stock mín."])
            for r in rows:
                writer.writerow([r["code"], r["name"], r["category"], r["cost_price"], r["sale_price"], r["stock"], r["min_stock"]])
        ui.info("Exportar", f"Inventario exportado a:\n{os.path.abspath(path)}")
