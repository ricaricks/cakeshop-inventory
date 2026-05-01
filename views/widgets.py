import tkinter as tk
from config import *

def btn_secondary(parent, text, command):
    return tk.Button(parent, text=text, font=FONT, bg=ACCENT2, fg=TEXT,
                    relief="flat", cursor="hand2", padx=12, pady=5, command=command)

def btn_danger(parent, text, command):
    return tk.Button(parent, text=text, font=FONT, bg=RED_BG, fg=ACCENT,
                    relief="flat", cursor="hand2", padx=12, pady=5, command=command)

def btn_primary(parent, text, command):
    return tk.Button(parent, text=text, font=FONT_B, bg=ACCENT, fg=WHITE,
                    relief="flat", cursor="hand2", padx=14, pady=6, command=command)

def card(parent):
    return tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground=BORDER)

def make_tree(parent, cols, heads, widths, height=15):
    from tkinter import ttk
    frame = tk.Frame(parent, bg=BG)
    tree = ttk.Treeview(frame, columns=cols, show="headings", height=height)
    for col, head, w in zip(cols, heads, widths):
        tree.heading(col, text=head)
        tree.column(col, width=w, anchor="w")
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    return frame, tree

def apply_tree_style():
    from tkinter import ttk
    style = ttk.Style()
    style.configure("Treeview", rowheight=32)

def badge_label(parent, text, color):
    return tk.Label(parent, text=text, font=FONT_XS, bg=color, fg=WHITE, padx=6, pady=2)

def section_sep(parent, text):
    tk.Label(parent, text=text, font=FONT_B, bg=BG, fg=TEXT).pack(anchor="w", padx=20, pady=(16, 6))

def field_row(parent, label, var, bg=BG):
    tk.Label(parent, text=label, font=FONT_B, bg=bg, fg=TEXT).pack(anchor="w", padx=20, pady=(6, 2))
    tk.Entry(parent, textvariable=var, font=FONT, relief="flat", bg="#faf5f0",
             highlightthickness=1, highlightbackground=BORDER).pack(fill="x", padx=20, ipady=7)