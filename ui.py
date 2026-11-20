import tkinter as tk
from tkinter import messagebox, ttk


def fmt_money(value):
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def fmt_qty(value):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "0"
    if v == int(v):
        return str(int(v))
    return f"{v:g}"


def clear_tree(tree):
    tree.delete(*tree.get_children())


def fill_tree(tree, rows):
    for r in rows:
        tree.insert("", "end", values=list(r))


def selected_row(tree):
    sel = tree.selection()
    if not sel:
        return None
    idx = tree.index(sel[0])
    return tree.item(sel[0], "values"), idx


def confirm(title, message):
    return messagebox.askyesno(title, message)


def info(title, message):
    messagebox.showinfo(title, message)


def warn(title, message):
    messagebox.showwarning(title, message)


def error(title, message):
    messagebox.showerror(title, message)


def make_tree(parent, columns, widths, heights=14, stretch=(), packing=True, title=None):
    frame = ttk.Frame(parent)
    if packing:
        frame.pack(fill="both", expand=True, padx=14, pady=(0, 14))
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=heights)
    for col, w in zip(columns, widths):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="w", stretch=(col in stretch))
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    if title:
        ttk.Label(frame, text=title, font=("Segoe UI", 9, "bold"),
                  background="#f9fafb").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        frame.rowconfigure(1, weight=1)
    else:
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    return frame, tree


def add_form_entry(parent, label, var, row, col=0, width=36, show=None):
    ttk.Label(parent, text=label).grid(row=row, column=col, sticky="e", padx=(0, 8), pady=4)
    ent = ttk.Entry(parent, textvariable=var, width=width, show=show)
    ent.grid(row=row, column=col + 1, sticky="we", pady=4, padx=(0, 12))
    parent.columnconfigure(col + 1, weight=1)
    return ent