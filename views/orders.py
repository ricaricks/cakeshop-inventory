import tkinter as tk
from tkinter import ttk, messagebox
from config import *
from utils import run_bg
from views.widgets import card, make_tree, apply_tree_style, btn_primary, btn_secondary

STATUS_OPTS = [
    "pending", "confirmed", "processing",
    "out_for_delivery", "delivered", "cancelled", "refunded"
]


class OrdersView:
    def __init__(self, parent, api):
        self.parent = parent
        self.api = api
        self._ids = []
        self._build()

    def _build(self):
        apply_tree_style()

        # header
        top = tk.Frame(self.parent, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 8))
        tk.Label(top, text="Orders", font=FONT_H, bg=BG, fg=TEXT).pack(side="left")
        btn_secondary(top, "Refresh", self._load).pack(side="right", pady=4)

        # action buttons BEFORE the tree so they are always visible
        act = tk.Frame(self.parent, bg=BG)
        act.pack(fill="x", padx=24, pady=(0, 6))

        tk.Label(act, text="Selected order:", font=FONT_B, bg=BG, fg=TEXT).pack(side="left", padx=(0, 10))
        btn_primary(act, "Confirm", lambda: self._quick("confirmed")).pack(side="left", padx=(0, 6))
        tk.Button(act, text="Cancel Order", font=FONT_B, bg=ACCENT, fg=WHITE,
                  relief="flat", cursor="hand2", padx=14, pady=6,
                  command=lambda: self._quick("cancelled")).pack(side="left", padx=(0, 6))
        tk.Button(act, text="Mark Delivered", font=FONT_B, bg=GREEN, fg=WHITE,
                  relief="flat", cursor="hand2", padx=14, pady=6,
                  command=lambda: self._quick("delivered")).pack(side="left", padx=(0, 14))

        tk.Label(act, text="|", font=FONT, bg=BG, fg=MUTED).pack(side="left", padx=(0, 10))
        tk.Label(act, text="Set status:", font=FONT_SM, bg=BG, fg=TEXT2).pack(side="left", padx=(0, 6))
        self._status_var = tk.StringVar(value="confirmed")
        ttk.Combobox(act, textvariable=self._status_var, values=STATUS_OPTS,
                     font=FONT, state="readonly", width=18).pack(side="left", padx=(0, 6))
        btn_secondary(act, "Apply", self._update_status).pack(side="left")

        # tree
        tree_card = card(self.parent)
        tree_card.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        cols = ("num", "customer", "total", "payment", "status", "date")
        heads = ["Order #", "Customer", "Total (P)", "Payment", "Status", "Date"]
        widths = [120, 190, 90, 110, 130, 100]
        tf, self._tree = make_tree(tree_card, cols, heads, widths, height=17)
        tf.pack(fill="both", expand=True, padx=1, pady=1)

        self._tree.tag_configure("delivered",        foreground=GREEN)
        self._tree.tag_configure("cancelled",        foreground=ACCENT)
        self._tree.tag_configure("refunded",         foreground=ACCENT)
        self._tree.tag_configure("pending",          foreground=ORANGE)
        self._tree.tag_configure("out_for_delivery", foreground=GREEN)

        self._load()

    def _load(self):
        self._tree.delete(*self._tree.get_children())
        self._ids = []

        def fetch():
            return self.api.get("/orders", {"limit": 100})

        def done(data):
            if "_error" in data:
                messagebox.showerror("Error", data["_error"])
                return
            outer = data.get("data") or data
            if isinstance(outer, list):
                orders = outer
            elif isinstance(outer, dict):
                orders = outer.get("rows") or outer.get("data") or outer.get("orders") or []
            else:
                orders = []
            for o in orders:
                self._ids.append(o["id"])
                customer = (o.get("user") or o.get("User") or {}).get("name", "—")
                total = f"{float(o.get('total', 0)):,.2f}"
                date = str(o.get("createdAt", ""))[:10]
                status = o.get("status", "—")
                self._tree.insert("", "end",
                    values=(o.get("orderNumber", o["id"]), customer, total,
                            o.get("paymentMethod", "—"), status, date),
                    tags=(status,))

        run_bg(fetch, callback=done)

    def _get_id(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select an order first.")
            return None
        idx = self._tree.index(sel[0])
        return self._ids[idx] if idx < len(self._ids) else None

    def _quick(self, status):
        oid = self._get_id()
        if oid:
            self._do_update(oid, status)

    def _update_status(self):
        oid = self._get_id()
        if oid:
            self._do_update(oid, self._status_var.get())

    def _do_update(self, oid, status):
        def do():
            return self.api.patch(f"/orders/{oid}/status", {"status": status})
        def done(r):
            if r.get("success") or r.get("data") or r.get("message"):
                self._load()
                messagebox.showinfo("Updated", f"Status set to '{status}'.")
            else:
                messagebox.showerror("Error", r.get("message", "Update failed."))
        run_bg(do, callback=done)