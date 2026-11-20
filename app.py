import tkinter as tk
from tkinter import ttk

import auth
import db
import ui
from screens.clients import ClientsScreen
from screens.inventory import InventoryScreen
from screens.reports import ReportsScreen
from screens.sales import SalesScreen

APP_TITLE = "Invendesk"
NAV = [
    ("inventory", "Inventario"),
    ("sales", "Ventas"),
    ("clients", "Clientes"),
    ("reports", "Reportes"),
]

COLOR_BG = "#f3f4f6"
COLOR_SIDEBAR = "#1f2937"
COLOR_HOVER = "#374151"
COLOR_ACTIVE = "#2563eb"
COLOR_TEXT = "#f9fafb"


class ChangePasswordDialog(tk.Toplevel):
    def __init__(self, parent, user):
        super().__init__(parent)
        self.title("Cambiar contraseña")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.user = user

        body = ttk.Frame(self, padding=14)
        body.pack(fill="both", expand=True)
        self.current_var = tk.StringVar()
        self.new_var = tk.StringVar()
        self.confirm_var = tk.StringVar()
        ui.add_form_entry(body, "Contraseña actual:", self.current_var, 0, width=34, show="*")
        ui.add_form_entry(body, "Nueva contraseña:", self.new_var, 1, width=34, show="*")
        ui.add_form_entry(body, "Confirmar nueva:", self.confirm_var, 2, width=34, show="*")
        btns = ttk.Frame(body)
        btns.grid(row=3, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Cancelar", command=self.destroy).pack(side="left", padx=6)
        ttk.Button(btns, text="Guardar", command=self._save).pack(side="left")

    def _save(self):
        if self.new_var.get() != self.confirm_var.get():
            ui.warn("Cambiar contraseña", "La nueva contraseña y su confirmación no coinciden.")
            return
        ok, msg = auth.change_password(
            self.user["id"], self.current_var.get(), self.new_var.get()
        )
        if not ok:
            ui.error("Cambiar contraseña", msg)
            return
        ui.info("Cambiar contraseña", "Contraseña actualizada correctamente.")
        self.destroy()


class LoginScreen(ttk.Frame):
    def __init__(self, parent, on_success, on_quit):
        super().__init__(parent, style="Content.TFrame")
        self.on_success = on_success
        self.on_quit = on_quit
        self.first_user = not auth.has_users()
        self._render()

    def _render(self):
        for widget in self.winfo_children():
            widget.destroy()

        card = ttk.Frame(self, padding=40)
        card.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(card, text=APP_TITLE, font=("Segoe UI", 22, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 4))
        info = ("Primera vez: crea el usuario administrador."
                if self.first_user else "Inicia sesión para continuar.")
        ttk.Label(card, text=info, font=("Segoe UI", 10), foreground="#6b7280").grid(
            row=1, column=0, columnspan=2, pady=(0, 20))

        row = 2
        self.user_var = tk.StringVar()
        ttk.Label(card, text="Usuario:").grid(row=row, column=0, sticky="e", padx=(0, 8), pady=4)
        ent_user = ttk.Entry(card, textvariable=self.user_var, width=28)
        ent_user.grid(row=row, column=1, sticky="we", pady=4)
        row += 1

        if self.first_user:
            self.full_var = tk.StringVar()
            ttk.Label(card, text="Nombre completo:").grid(row=row, column=0, sticky="e", padx=(0, 8), pady=4)
            ent_full = ttk.Entry(card, textvariable=self.full_var, width=28)
            ent_full.grid(row=row, column=1, sticky="we", pady=4)
            row += 1

        self.pass_var = tk.StringVar()
        ttk.Label(card, text="Contraseña:").grid(row=row, column=0, sticky="e", padx=(0, 8), pady=4)
        ent_pass = ttk.Entry(card, textvariable=self.pass_var, show="*", width=28)
        ent_pass.grid(row=row, column=1, sticky="we", pady=4)
        row += 1

        if self.first_user:
            self.pass2_var = tk.StringVar()
            ttk.Label(card, text="Confirmar contraseña:").grid(row=row, column=0, sticky="e", padx=(0, 8), pady=4)
            ent_pass2 = ttk.Entry(card, textvariable=self.pass2_var, show="*", width=28)
            ent_pass2.grid(row=row, column=1, sticky="we", pady=4)
            row += 1

        self.error_var = tk.StringVar()
        ttk.Label(card, textvariable=self.error_var, foreground="#dc2626").grid(
            row=row, column=0, columnspan=2, pady=(6, 0))
        row += 1

        btns = ttk.Frame(card)
        btns.grid(row=row, column=0, columnspan=2, pady=(16, 0))
        ttk.Button(btns, text="Cancelar", command=self.on_quit).pack(side="left", padx=8)
        submit_text = "Crear e iniciar sesión" if self.first_user else "Iniciar sesión"
        ttk.Button(btns, text=submit_text, command=self._submit).pack(side="left", padx=8)

        card.columnconfigure(1, weight=1)
        for widget in (ent_user, ent_pass):
            widget.bind("<Return>", lambda e: self._submit())

    def _submit(self):
        if self.first_user:
            if self.pass_var.get() != self.pass2_var.get():
                self.error_var.set("Las contraseñas no coinciden.")
                return
            ok, msg = auth.create_user(self.user_var.get(), self.pass_var.get(), self.full_var.get())
            if not ok:
                self.error_var.set(msg)
                return
            self._login(self.user_var.get(), self.pass_var.get())
        else:
            self._login(self.user_var.get(), self.pass_var.get())

    def _login(self, username, password):
        user = auth.authenticate(username, password)
        if user is None:
            self.error_var.set("Usuario o contraseña incorrectos.")
            self.pass_var.set("")
            return
        self.error_var.set("")
        self.on_success(user)


class Dashboard(ttk.Frame):
    def __init__(self, parent, user, on_logout):
        super().__init__(parent, style="Content.TFrame")
        self.user = user
        self.on_logout = on_logout
        self._build_layout()

    def _build_layout(self):
        self.sidebar = tk.Frame(self, bg=COLOR_SIDEBAR, width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        title = tk.Label(self.sidebar, text=APP_TITLE, bg=COLOR_SIDEBAR, fg="#ffffff",
                         font=("Segoe UI", 15, "bold"), anchor="w")
        title.pack(fill="x", padx=18, pady=(20, 18))

        subtitle = tk.Label(self.sidebar, text=f"Bienvenido, {self.user['full_name'] or self.user['username']}",
                            bg=COLOR_SIDEBAR, fg="#9ca3af", font=("Segoe UI", 9), anchor="w")
        subtitle.pack(fill="x", padx=18, pady=(0, 16))

        self.nav_buttons = {}
        for key, label in NAV:
            btn = tk.Button(
                self.sidebar, text=label, command=lambda k=key: self.show_screen(k),
                bg=COLOR_SIDEBAR, fg=COLOR_TEXT, activebackground=COLOR_HOVER, activeforeground="#ffffff",
                relief="flat", bd=0, font=("Segoe UI", 11), anchor="w", padx=18, pady=12, cursor="hand2",
            )
            btn.pack(fill="x", ipady=4)
            self.nav_buttons[key] = btn

        side_actions = tk.Frame(self.sidebar, bg=COLOR_SIDEBAR)
        side_actions.pack(side="bottom", fill="x", padx=12, pady=(0, 10))
        ttk.Button(side_actions, text="Cambiar contraseña",
                   command=self._change_password).pack(fill="x", pady=3)
        ttk.Button(side_actions, text="Cerrar sesión", command=self.on_logout).pack(fill="x", pady=3)

        db_path = db.get_db_path()
        footer = tk.Label(self.sidebar, text=f"Datos:\n{db_path}", bg=COLOR_SIDEBAR, fg="#9ca3af",
                          font=("Segoe UI", 7), justify="left", wraplength=170)
        footer.pack(side="bottom", fill="x", padx=12, pady=(0, 8))

        self.main = ttk.Frame(self, style="Content.TFrame")
        self.main.pack(side="left", fill="both", expand=True)

        self.screens = {
            "inventory": InventoryScreen(self.main),
            "sales": SalesScreen(self.main),
            "clients": ClientsScreen(self.main),
            "reports": ReportsScreen(self.main),
        }
        for screen in self.screens.values():
            screen.pack(fill="both", expand=True)
        self.current = None

    def show_screen(self, key):
        if self.current:
            self.screens[self.current].pack_forget()
        self.screens[key].pack(fill="both", expand=True)
        self.screens[key].refresh()
        self.current = key
        for k, btn in self.nav_buttons.items():
            btn.config(bg=COLOR_ACTIVE if k == key else COLOR_SIDEBAR)

    def _change_password(self):
        dlg = ChangePasswordDialog(self.winfo_toplevel(), self.user)
        self.wait_window(dlg)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1180x720")
        self.minsize(980, 620)

        db.initialize_database()

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Content.TFrame", background=COLOR_BG)

        self.login = None
        self.dashboard = None
        self._show_login()

    def _show_login(self):
        if self.dashboard is not None:
            self.dashboard.pack_forget()
        self.dashboard = None
        self.login = LoginScreen(self, on_success=self._show_dashboard, on_quit=self.destroy)
        self.login.pack(fill="both", expand=True)

    def _show_dashboard(self, user):
        self.login.pack_forget()
        self.dashboard = Dashboard(self, user=user, on_logout=self._show_login)
        self.dashboard.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = App()
    app.mainloop()