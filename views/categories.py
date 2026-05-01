import tkinter as tk
from config import *
from utils import run_bg
from views.widgets import (card, make_tree, apply_tree_style,
                            btn_primary, btn_secondary, btn_danger)


class CategoriesView:
    def __init__(self, parent, api):
        self.parent = parent
        self.api = api
        self._ids = []
        self._build()

    def _build(self):
        apply_tree_style()

        top = tk.Frame(self.parent, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(top, text="Categories", font=FONT_H, bg=BG, fg=TEXT).pack(side="left")
        btn_primary(top, "+ Add Category", lambda: self._form()).pack(side="right", pady=4)

        tree_card = card(self.parent)
        tree_card.pack(fill="both", expand=True, padx=24, pady=(0, 8))

        cols = ("name", "slug", "count")
        heads = ["Name", "Slug", "Products"]
        widths = [250, 250, 100]
        tf, self._tree = make_tree(tree_card, cols, heads, widths, height=18)
        tf.pack(fill="both", expand=True, padx=1, pady=1)

        act = tk.Frame(self.parent, bg=BG)
        act.pack(fill="x", padx=24, pady=(0, 14))
        btn_secondary(act, "Edit Selected", self._edit).pack(side="left", padx=(0, 6))
        btn_danger(act, "Delete Selected", self._delete).pack(side="left")

        self._load()

    def _load(self):
        self._tree.delete(*self._tree.get_children())
        self._ids = []
        def fetch():
            return self.api.get("/categories")
        def done(data):
            from tkinter import messagebox
            if "_error" in data:
                messagebox.showerror("Error", data["_error"])
                return
            inner = data.get("data") or {}
            cats = inner if isinstance(inner, list) else inner.get("categories", [])
            for c in cats:
                self._ids.append(c["id"])
                self._tree.insert("", "end",
                    values=(c["name"], c.get("slug", ""), c.get("productCount", "—")))
        run_bg(fetch, callback=done)

    def _selected_id(self):
        from tkinter import messagebox
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a category first.")
            return None
        return self._ids[self._tree.index(sel[0])]

    def _edit(self):
        cid = self._selected_id()
        if not cid:
            return
        vals = self._tree.item(self._tree.selection()[0], "values")
        self._form({"id": cid, "name": vals[0], "slug": vals[1]})

    def _delete(self):
        from tkinter import messagebox
        cid = self._selected_id()
        if not cid:
            return
        if not messagebox.askyesno("Delete Category", "Delete this category?"):
            return
        def do():
            return self.api.delete(f"/categories/{cid}")
        def done(r):
            if r.get("success") or r.get("data"):
                self._load()
            else:
                messagebox.showerror("Error", r.get("message", "Delete failed."))
        run_bg(do, callback=done)

    def _form(self, cat=None):
        import tkinter as tk
        win = tk.Toplevel(self.parent.winfo_toplevel())
        win.title("Edit Category" if cat else "New Category")
        win.geometry("400x250")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.grab_set()

        hdr = tk.Frame(win, bg=SIDEBAR, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Edit Category" if cat else "New Category",
                 font=FONT_SH, bg=SIDEBAR, fg=WHITE).pack(side="left", padx=20, pady=14)

        body = tk.Frame(win, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=16)

        tk.Label(body, text="Category Name *", font=FONT_SM, bg=BG, fg=TEXT2).pack(anchor="w", pady=(0, 4))
        v = tk.StringVar(value=cat["name"] if cat else "")
        tk.Entry(body, textvariable=v, font=FONT, relief="flat", bg=WHITE,
                 highlightthickness=1, highlightbackground=BORDER).pack(fill="x", ipady=8)

        st = tk.Label(body, text="", font=FONT_SM, bg=BG, fg=ACCENT)
        st.pack(pady=(8, 0))

        def save():
            from tkinter import messagebox
            name = v.get().strip()
            if not name:
                st.config(text="Name is required.")
                return
            btn.config(state="disabled", text="Saving...")
            def do():
                if cat:
                    return self.api.put(f"/categories/{cat['id']}", {"name": name})
                return self.api.post("/categories", {"name": name})
            def done(r):
                if r.get("success") or r.get("data"):
                    win.destroy()
                    self._load()
                else:
                    btn.config(state="normal", text="Save")
                    st.config(text=r.get("message", "Failed."))
            run_bg(do, callback=done)

        btn = btn_primary(body, "Save", save)
        btn.pack(fill="x", pady=(10, 0))