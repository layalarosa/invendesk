import tkinter as tk
from tkinter import ttk

import db
import ui
from validation import validate_client

COLUMNS = ["ID", "Nombre", "Teléfono", "Correo", "Dirección", "Notas"]
WIDTHS = [50, 220, 130, 180, 220, 200]


class ClientDialog(tk.Toplevel):
    def __init__(self, parent, client=None):
        super().__init__(parent)
        self.title("Editar cliente" if client else "Nuevo cliente")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._vars = {k: tk.StringVar() for k in ("name", "phone", "email", "address", "notes")}
        if client:
            self.client_id = client["id"]
            for k in self._vars:
                self._vars[k].set(client[k])
        else:
            self.client_id = None

        body = ttk.Frame(self, padding=14)
        body.pack(fill="both", expand=True)
        fields = [
            ("Nombre *", "name"), ("Teléfono", "phone"), ("Correo", "email"),
            ("Dirección", "address"), ("Notas", "notes"),
        ]
        for i, (label, key) in enumerate(fields):
            ui.add_form_entry(body, label, self._vars[key], i, width=52)
        buttons = ttk.Frame(body)
        buttons.grid(row=5, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text="Cancelar", command=self.destroy).pack(side="left", padx=6)
        ttk.Button(buttons, text="Guardar", command=self._save).pack(side="left")
        self.bind("<Return>", lambda e: self._save())

    def _read_fields(self):
        return {k: var.get() for k, var in self._vars.items()}

    def _save(self):
        ok, clean, errs = validate_client(self._read_fields())
        if not ok:
            ui.error("Datos inválidos", "\n".join(f"• {e}" for e in errs))
            return
        conn = db.get_conn()
        clean["id"] = self.client_id
        clean["created_at"] = db.now_iso()
        if self.client_id:
            conn.execute(
                "UPDATE clients SET name=:name, phone=:phone, email=:email, "
                "address=:address, notes=:notes WHERE id=:id",
                clean,
            )
        else:
            conn.execute(
                "INSERT INTO clients (name, phone, email, address, notes, created_at) "
                "VALUES (:name, :phone, :email, :address, :notes, :created_at)",
                clean,
            )
        conn.commit()
        self.destroy()


class ClientsScreen(ttk.Frame):
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
        ttk.Button(btns, text="+ Nuevo", command=self.add_client).pack(side="left", padx=4)
        ttk.Button(btns, text="Editar", command=self.edit_client).pack(side="left", padx=4)
        ttk.Button(btns, text="Eliminar", command=self.delete_client).pack(side="left", padx=4)

    def _build_table(self):
        self.frame, self.tree = ui.make_tree(self, COLUMNS, WIDTHS, heights=18, stretch=("Nombre", "Dirección"))
        self.tree.bind("<Double-1>", lambda e: self.edit_client())
        foot = ttk.Frame(self, style="Content.TFrame")
        foot.pack(fill="x", padx=16, pady=(0, 10))
        self.count_var = tk.StringVar()
        ttk.Label(foot, textvariable=self.count_var, foreground="#374151").pack(side="left")

    def refresh(self):
        term = "%" + self.search_var.get().strip() + "%"
        rows = db.get_conn().execute(
            """SELECT id, name, phone, email, address, notes FROM clients
               WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
               ORDER BY name COLLATE NOCASE ASC""",
            (term, term, term),
        ).fetchall()
        ui.clear_tree(self.tree)
        for r in rows:
            self.tree.insert(
                "", "end",
                values=(r["id"], r["name"], r["phone"], r["email"], r["address"], r["notes"]),
            )
        self.count_var.set(f"{len(rows)} cliente(s)")

    def _client_from_selection(self):
        values, _ = ui.selected_row(self.tree)
        if not values:
            ui.warn("Clientes", "Selecciona un cliente.")
            return None
        return db.get_conn().execute("SELECT * FROM clients WHERE id = ?", (values[0],)).fetchone()

    def add_client(self):
        dlg = ClientDialog(self.winfo_toplevel())
        self.wait_window(dlg)
        self.refresh()

    def edit_client(self):
        client = self._client_from_selection()
        if client:
            dlg = ClientDialog(self.winfo_toplevel(), client)
            self.wait_window(dlg)
            self.refresh()

    def delete_client(self):
        client = self._client_from_selection()
        if not client:
            return
        if not ui.confirm("Eliminar cliente", f"¿Eliminar al cliente '{client['name']}'?"):
            return
        conn = db.get_conn()
        conn.execute("DELETE FROM clients WHERE id = ?", (client["id"],))
        conn.commit()
        self.refresh()