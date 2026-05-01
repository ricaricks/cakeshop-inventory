import tkinter as tk
from tkinter import ttk
from config import *
from api import ApiClient
from utils import set_root, run_bg


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rica's Cake Shop")
        self.geometry("1240x740")
        self.minsize(960, 620)
        self.configure(bg=BG)
        self.api = ApiClient()
        set_root(self)
        self._nav_items = []
        self._build_login()

    def _build_login(self):
        self._clear()
        outer = tk.Frame(self, bg=BG)
        outer.place(relx=.5, rely=.5, anchor="center")

        brand = tk.Frame(outer, bg=ACCENT, padx=36, pady=28)
        brand.pack(fill="x")
        tk.Label(brand, text="Rica's Cake Shop", font=("Segoe UI", 20, "bold"),
                 bg=ACCENT, fg=WHITE).pack()
        tk.Label(brand, text="Admin Panel", font=FONT, bg=ACCENT, fg="#f5c0b8").pack(pady=(4, 0))

        form = tk.Frame(outer, bg=WHITE, padx=36, pady=30,
                        highlightthickness=1, highlightbackground=BORDER)
        form.pack(fill="x")

        for label, attr, show in [("Email", "_email", None), ("Password", "_pw", "*")]:
            tk.Label(form, text=label, font=FONT_SM, bg=WHITE, fg=TEXT2).pack(anchor="w", pady=(0 if label == "Email" else 14, 4))
            kw = dict(font=FONT, relief="flat", bg="#faf5f0",
                      highlightthickness=1, highlightbackground=BORDER, width=32)
            if show:
                kw["show"] = show
            e = tk.Entry(form, **kw)
            e.pack(fill="x", ipady=8)
            setattr(self, attr, e)

        from config import ADMIN_EMAIL, ADMIN_PASSWORD
        self._email.insert(0, ADMIN_EMAIL)
        self._pw.insert(0, ADMIN_PASSWORD)

        self._login_btn = tk.Button(form, text="Sign In", font=FONT_B,
                                     bg=ACCENT, fg=WHITE, relief="flat",
                                     cursor="hand2", pady=10,
                                     activebackground=ACCENT_H, activeforeground=WHITE,
                                     command=self._do_login)
        self._login_btn.pack(fill="x", pady=(22, 0))

        self._err_lbl = tk.Label(outer, text="", font=FONT_SM, bg=BG, fg=ACCENT)
        self._err_lbl.pack(pady=(10, 0))

        self._email.bind("<Return>", lambda e: self._pw.focus())
        self._pw.bind("<Return>", lambda e: self._do_login())
        if not ADMIN_EMAIL:
            self._email.focus()

    def _do_login(self):
        email = self._email.get().strip()
        pw = self._pw.get().strip()
        self._login_btn.config(state="disabled", text="Signing in...")
        self._err_lbl.config(text="")

        def attempt():
            return self.api.login(email, pw)

        def done(result):
            ok, msg = result
            if ok:
                self._build_main()
            else:
                self._login_btn.config(state="normal", text="Sign In")
                self._err_lbl.config(text=f"Login failed: {msg}")

        run_bg(attempt, callback=done)

    def _build_main(self):
        self._clear()

        side = tk.Frame(self, bg=SIDEBAR, width=200)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        brand = tk.Frame(side, bg=ACCENT, padx=18, pady=18)
        brand.pack(fill="x")
        tk.Label(brand, text="Rica's Cakes", font=FONT_B, bg=ACCENT, fg=WHITE).pack(anchor="w")
        tk.Label(brand, text="Admin Panel", font=FONT_XS, bg=ACCENT, fg="#f5c0b8").pack(anchor="w")

        self._content = tk.Frame(self, bg=BG)
        self._content.pack(side="left", fill="both", expand=True)

        self._nav_items = []
        nav_wrap = tk.Frame(side, bg=SIDEBAR)
        nav_wrap.pack(fill="both", expand=True, pady=(10, 0))

        for label, cmd in [("Products", self._show_products),
                            ("Categories", self._show_categories),
                            ("Orders", self._show_orders)]:
            self._make_nav(nav_wrap, label, cmd)

        tk.Button(side, text="Log Out", font=FONT, bg=SIDEBAR, fg=MUTED,
                  relief="flat", cursor="hand2", anchor="w", padx=20, pady=10,
                  activebackground=SB_HOV, activeforeground=WHITE,
                  command=self._build_login).pack(fill="x", side="bottom", pady=10)

        self._show_products()

    def _make_nav(self, parent, label, cmd):
        fr = tk.Frame(parent, bg=SIDEBAR, cursor="hand2")
        fr.pack(fill="x")
        ind = tk.Frame(fr, bg=SIDEBAR, width=3)
        ind.pack(side="left", fill="y")
        ind.pack_propagate(False)

        def click():
            self._activate_nav(fr, ind, cmd)

        btn = tk.Button(fr, text=label, font=FONT, bg=SIDEBAR, fg=ACCENT2,
                        relief="flat", anchor="w", padx=16, pady=12,
                        cursor="hand2", activebackground=SB_HOV,
                        activeforeground=WHITE, command=click)
        btn.pack(fill="x")
        fr.bind("<Button-1>", lambda e: click())
        self._nav_items.append((fr, ind, btn))

    def _activate_nav(self, active_fr, active_ind, cmd):
        for fr, ind, btn in self._nav_items:
            fr.configure(bg=SIDEBAR)
            ind.configure(bg=SIDEBAR)
            btn.configure(bg=SIDEBAR, fg=ACCENT2)
        active_fr.configure(bg=SB_ACT)
        active_ind.configure(bg=ACCENT)
        for child in active_fr.winfo_children():
            if isinstance(child, tk.Button):
                child.configure(bg=SB_ACT, fg=WHITE)
        cmd()

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def _clear_content(self):
        for w in self._content.winfo_children():
            w.destroy()

    def _show_products(self):
        self._clear_content()
        from views.products import ProductsView
        ProductsView(self._content, self.api)

    def _show_categories(self):
        self._clear_content()
        from views.categories import CategoriesView
        CategoriesView(self._content, self.api)

    def _show_orders(self):
        self._clear_content()
        from views.orders import OrdersView
        OrdersView(self._content, self.api)