import tkinter as tk
from tkinter import messagebox
from config import *
from utils import run_bg, extract_list
from views.widgets import (card, make_tree, apply_tree_style,
                            btn_primary, btn_secondary, btn_danger, badge_label)

try:
    from PIL import Image, ImageTk
    import io, requests as _req
    PIL_OK = True
except ImportError:
    PIL_OK = False


class ProductsView:
    def __init__(self, parent, api):
        self.parent = parent
        self.api = api
        self._meta = []
        self._img_ref = None
        self._stat_vars = {}
        self._build()

    def _build(self):
        apply_tree_style()

        # ── header ──
        top = tk.Frame(self.parent, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 0))
        tk.Label(top, text="Product Inventory", font=FONT_H, bg=BG, fg=TEXT).pack(side="left")
        btn_primary(top, "+ Add Product", self._add).pack(side="right", pady=4)

        self._build_stats()
        self._build_toolbar()

        # ── action buttons FIRST so they're always visible ──
        act = tk.Frame(self.parent, bg=BG)
        act.pack(fill="x", padx=24, pady=(8, 0))
        btn_secondary(act, "✏  Edit Selected", self._edit).pack(side="left", padx=(0, 6))
        btn_danger(act, "🗑  Delete Selected", self._delete).pack(side="left")

        # ── body: tree + detail panel ──
        body = tk.Frame(self.parent, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=(6, 10))

        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True)

        tree_card = card(left)
        tree_card.pack(fill="both", expand=True)

        cols = ("name", "category", "price", "stock", "status")
        heads = ["Product", "Category", "Price (P)", "Stock", "Status"]
        widths = [220, 130, 90, 70, 80]
        tf, self._tree = make_tree(tree_card, cols, heads, widths, height=14)
        tf.pack(fill="both", expand=True, padx=1, pady=1)

        self._detail_wrap = tk.Frame(body, bg=BG, width=230)
        self._detail_wrap.pack(side="right", fill="y", padx=(14, 0))
        self._detail_wrap.pack_propagate(False)
        self._build_detail_empty()

        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._load()

    def _build_stats(self):
        fr = tk.Frame(self.parent, bg=BG)
        fr.pack(fill="x", padx=24, pady=(12, 0))
        for key, label in [("total", "Total"), ("active", "Active"),
                            ("inactive", "Inactive"), ("featured", "Featured")]:
            c = card(fr)
            c.pack(side="left", padx=(0, 8), ipadx=16, ipady=10)
            v = tk.StringVar(value="—")
            self._stat_vars[key] = v
            colors = {"total": TEXT, "active": GREEN, "inactive": MUTED, "featured": ORANGE}
            tk.Label(c, textvariable=v, font=("Segoe UI", 18, "bold"),
                     bg=CARD, fg=colors[key]).pack()
            tk.Label(c, text=label, font=FONT_XS, bg=CARD, fg=MUTED).pack()

    def _build_toolbar(self):
        tb = tk.Frame(self.parent, bg=BG)
        tb.pack(fill="x", padx=24, pady=(10, 0))
        self._search_var = tk.StringVar()
        e = tk.Entry(tb, textvariable=self._search_var, font=FONT, relief="flat", bg=WHITE,
                     highlightthickness=1, highlightbackground=BORDER, width=28)
        e.pack(side="left", ipady=7, padx=(0, 6))
        e.insert(0, "Search products...")
        e.bind("<FocusIn>", lambda ev: e.delete(0, "end") if e.get() == "Search products..." else None)
        e.bind("<Return>", lambda ev: self._load(self._search_var.get()))
        btn_secondary(tb, "Search", lambda: self._load(self._search_var.get())).pack(side="left", padx=(0, 6))
        btn_secondary(tb, "Refresh", lambda: self._load("")).pack(side="left")

    def _build_detail_empty(self):
        for w in self._detail_wrap.winfo_children():
            w.destroy()
        c = card(self._detail_wrap)
        c.pack(fill="both", expand=True)
        tk.Label(c, text="Select a product\nto preview details",
                 font=FONT_SM, bg=CARD, fg=MUTED, justify="center").place(relx=.5, rely=.4, anchor="center")
        self._detail_card = c

    def _update_detail(self, p):
        dc = self._detail_card
        for w in dc.winfo_children():
            w.destroy()

        img_url = p.get("imageUrl", "")
        if PIL_OK and img_url:
            self._load_detail_image(dc, img_url)
        else:
            ph = tk.Frame(dc, bg=ACCENT2, height=140)
            ph.pack(fill="x")
            ph.pack_propagate(False)
            tk.Label(ph, text="No Image", font=FONT_SM, bg=ACCENT2,
                     fg=MUTED).place(relx=.5, rely=.5, anchor="center")

        info = tk.Frame(dc, bg=CARD)
        info.pack(fill="both", expand=True, padx=14, pady=12)

        tk.Label(info, text=p.get("name", ""), font=FONT_B, bg=CARD, fg=TEXT,
                 wraplength=195, justify="left").pack(anchor="w")
        cat = (p.get("category") or {}).get("name", "—")
        tk.Label(info, text=cat, font=FONT_XS, bg=CARD, fg=MUTED).pack(anchor="w", pady=(2, 6))
        tk.Label(info, text=f"P{float(p.get('price', 0)):,.2f}",
                 font=("Segoe UI", 14, "bold"), bg=CARD, fg=ACCENT).pack(anchor="w")

        badges = tk.Frame(info, bg=CARD)
        badges.pack(fill="x", pady=(8, 4))
        if p.get("isActive"):
            badge_label(badges, "Active", GREEN).pack(side="left", padx=(0, 4))
        else:
            badge_label(badges, "Inactive", MUTED).pack(side="left", padx=(0, 4))
        if p.get("isFeatured"):
            badge_label(badges, "Featured", ORANGE).pack(side="left")

        stock = p.get("stock", 0)
        color = GREEN if stock > 10 else (ORANGE if stock > 0 else ACCENT)
        tk.Label(info, text=f"Stock: {stock}", font=FONT_SM, bg=CARD, fg=color).pack(anchor="w")

        desc = p.get("description", "")
        if desc:
            tk.Frame(info, bg=BORDER, height=1).pack(fill="x", pady=(10, 6))
            tk.Label(info, text=desc[:140] + ("..." if len(desc) > 140 else ""),
                     font=FONT_XS, bg=CARD, fg=TEXT2,
                     wraplength=195, justify="left").pack(anchor="w")

    def _load_detail_image(self, parent, url):
        full = url if url.startswith("http") else f"http://localhost:3000{url}"
        def fetch():
            try:
                return _req.get(full, timeout=5).content
            except Exception:
                return None
        def done(content):
            if not content:
                return
            try:
                img = Image.open(io.BytesIO(content))
                img.thumbnail((228, 150), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                lbl = tk.Label(parent, image=photo, bg=CARD)
                lbl.image = photo
                lbl.pack()
                self._img_ref = photo
            except Exception:
                pass
        run_bg(fetch, callback=done)

    def _on_select(self, _):
        sel = self._tree.selection()
        if not sel:
            return
        idx = self._tree.index(sel[0])
        if idx >= len(self._meta):
            return
        slug = self._meta[idx]["slug"]
        def fetch():
            return self.api.get(f"/products/{slug}")
        def done(r):
            p = r.get("data") or {}
            if isinstance(p, dict) and "product" in p:
                p = p["product"]
            if p:
                self._update_detail(p)
        run_bg(fetch, callback=done)

    def _load(self, search=""):
        self._tree.delete(*self._tree.get_children())
        self._meta = []
        total = active = inactive = featured = 0

        def fetch():
            params = {"limit": 100}
            if search:
                params["search"] = search
            return self.api.get("/products", params)

        def done(data):
            nonlocal total, active, inactive, featured
            if "_error" in data:
                messagebox.showerror("Error", data["_error"])
                return
            prods = extract_list(data, "products", "rows")
            for p in prods:
                self._meta.append({"id": p["id"], "slug": p.get("slug", "")})
                price = f"{float(p.get('price', 0)):,.2f}"
                is_active = p.get("isActive", True)
                cat = (p.get("category") or p.get("Category") or {}).get("name", "—")
                tag = "active" if is_active else "inactive"
                self._tree.insert("", "end",
                    values=(p["name"], cat, price, str(p.get("stock", 0)),
                            "Active" if is_active else "Inactive"),
                    tags=(tag,))
                total += 1
                active += int(is_active)
                inactive += int(not is_active)
                featured += int(bool(p.get("isFeatured")))
            self._tree.tag_configure("inactive", foreground=MUTED)
            for k, v in zip(["total", "active", "inactive", "featured"],
                             [total, active, inactive, featured]):
                self._stat_vars[k].set(str(v))

        run_bg(fetch, callback=done)

    def _get_meta(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a product first.")
            return None
        idx = self._tree.index(sel[0])
        return self._meta[idx] if idx < len(self._meta) else None

    def _add(self):
        ProductForm(self.parent.winfo_toplevel(), self.api, None, lambda: self._load())

    def _edit(self):
        meta = self._get_meta()
        if not meta:
            return
        def fetch():
            return self.api.get(f"/products/{meta['slug']}")
        def done(r):
            p = r.get("data") or {}
            if isinstance(p, dict) and "product" in p:
                p = p["product"]
            if p:
                ProductForm(self.parent.winfo_toplevel(), self.api, p, lambda: self._load())
            else:
                messagebox.showerror("Error", "Could not load product.")
        run_bg(fetch, callback=done)

    def _delete(self):
        meta = self._get_meta()
        if not meta:
            return
        if not messagebox.askyesno("Delete Product", "This cannot be undone. Continue?"):
            return
        def do():
            return self.api.delete(f"/products/{meta['id']}")
        def done(r):
            ok = r.get("success") or r.get("data") or "deleted" in str(r.get("message", "")).lower()
            if ok:
                self._build_detail_empty()
                self._load()
            else:
                messagebox.showerror("Error", r.get("message", "Delete failed."))
        run_bg(do, callback=done)


# ── inline product form (no separate file needed) ──────────────────────────

from tkinter import ttk, filedialog
import mimetypes

class ProductForm(tk.Toplevel):
    def __init__(self, master, api, product, on_save):
        super().__init__(master)
        self.api = api
        self.product = product
        self.on_save = on_save
        self._file_path = None
        self._cat_map = {}
        self._img_ref = None

        self.title("Edit Product" if product else "New Product")
        self.geometry("520x680")
        self.configure(bg=BG)
        self.resizable(False, True)
        self.grab_set()
        self._build()
        self._load_cats()

    def _build(self):
        from views.widgets import section_sep, field_row
        p = self.product or {}

        hdr = tk.Frame(self, bg=SIDEBAR, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Edit Product" if self.product else "New Product",
                 font=FONT_SH, bg=SIDEBAR, fg=WHITE).pack(side="left", padx=20, pady=14)

        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=BG)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(-1 * int(e.delta / 120), "units"))

        self.v_name  = tk.StringVar(value=p.get("name", ""))
        self.v_price = tk.StringVar(value=str(p.get("price", "")))
        self.v_stock = tk.StringVar(value=str(p.get("stock", "")))
        self.v_img   = tk.StringVar(value=p.get("imageUrl", ""))
        self.v_feat  = tk.BooleanVar(value=bool(p.get("isFeatured")))
        self.v_avail = tk.BooleanVar(value=bool(p.get("isActive", True)))
        self.v_cat   = tk.StringVar()

        section_sep(inner, "Basic Information")
        field_row(inner, "Product Name *", self.v_name, bg=BG)

        section_sep(inner, "Pricing & Inventory")
        price_row = tk.Frame(inner, bg=BG)
        price_row.pack(fill="x", padx=20, pady=(6, 0))
        for label, var in [("Price (P) *", self.v_price), ("Stock", self.v_stock)]:
            col = tk.Frame(price_row, bg=BG)
            col.pack(side="left", fill="x", expand=True, padx=(0, 8 if "Price" in label else 0))
            tk.Label(col, text=label, font=FONT_SM, bg=BG, fg=TEXT2).pack(anchor="w")
            tk.Entry(col, textvariable=var, font=FONT, relief="flat", bg="#faf5f0",
                     highlightthickness=1, highlightbackground=BORDER).pack(fill="x", ipady=7)

        section_sep(inner, "Category")
        tk.Label(inner, text="Category", font=FONT_SM, bg=BG, fg=TEXT2).pack(anchor="w", padx=20, pady=(6, 2))
        self.cat_cb = ttk.Combobox(inner, textvariable=self.v_cat, font=FONT, state="readonly")
        self.cat_cb.pack(fill="x", padx=20)

        section_sep(inner, "Description")
        tk.Label(inner, text="Description", font=FONT_SM, bg=BG, fg=TEXT2).pack(anchor="w", padx=20, pady=(6, 2))
        self.desc_text = tk.Text(inner, font=FONT, relief="flat", bg="#faf5f0", height=3,
                                  highlightthickness=1, highlightbackground=BORDER, wrap="word")
        self.desc_text.pack(fill="x", padx=20)
        if p.get("description"):
            self.desc_text.insert("1.0", p["description"])

        section_sep(inner, "Product Image")
        img_fr = tk.Frame(inner, bg=BG)
        img_fr.pack(fill="x", padx=20, pady=(8, 0))
        self._preview_lbl = tk.Label(img_fr, bg=ACCENT2, width=10, height=5,
                                      text="No image", font=FONT_XS, fg=MUTED)
        self._preview_lbl.pack(side="left", padx=(0, 14))
        right = tk.Frame(img_fr, bg=BG)
        right.pack(side="left", fill="x", expand=True)
        tk.Label(right, text="Image URL", font=FONT_SM, bg=BG, fg=TEXT2).pack(anchor="w")
        tk.Entry(right, textvariable=self.v_img, font=FONT_SM, relief="flat", bg="#faf5f0",
                 highlightthickness=1, highlightbackground=BORDER).pack(fill="x", ipady=5)
        tk.Label(right, text="or upload a local file:", font=FONT_XS, bg=BG, fg=MUTED).pack(anchor="w", pady=(6, 2))
        btn_secondary(right, "Browse File", self._browse).pack(anchor="w")
        self._file_lbl = tk.Label(right, text="", font=FONT_XS, bg=BG, fg=GREEN)
        self._file_lbl.pack(anchor="w", pady=(3, 0))
        if p.get("imageUrl") and PIL_OK:
            self._preview_from_url(p["imageUrl"])

        section_sep(inner, "Visibility")
        chk = tk.Frame(inner, bg=BG)
        chk.pack(fill="x", padx=20, pady=(8, 4))
        tk.Checkbutton(chk, text="Featured product", variable=self.v_feat,
                       bg=BG, font=FONT, fg=TEXT, activebackground=BG,
                       selectcolor=CARD).pack(side="left", padx=(0, 28))
        tk.Checkbutton(chk, text="Active (visible in shop)", variable=self.v_avail,
                       bg=BG, font=FONT, fg=TEXT, activebackground=BG,
                       selectcolor=CARD).pack(side="left")

        self._status_lbl = tk.Label(inner, text="", font=FONT_SM, bg=BG, fg=ACCENT)
        self._status_lbl.pack(padx=20, pady=(8, 2))

        self.save_btn = btn_primary(inner, "Save Product", self._save)
        self.save_btn.pack(fill="x", padx=20, pady=(0, 20))

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp")]
        )
        if not path:
            return
        self._file_path = path
        self._file_lbl.config(text=path.replace("\\", "/").split("/")[-1][:42])
        self.v_img.set("")
        if PIL_OK:
            try:
                img = Image.open(path)
                img.thumbnail((80, 80), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._preview_lbl.config(image=photo, text="")
                self._preview_lbl.image = photo
                self._img_ref = photo
            except Exception:
                pass

    def _preview_from_url(self, url):
        full = url if url.startswith("http") else f"http://localhost:3000{url}"
        def fetch():
            try:
                return _req.get(full, timeout=5).content
            except Exception:
                return None
        def done(content):
            if not content:
                return
            try:
                img = Image.open(io.BytesIO(content))
                img.thumbnail((80, 80), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._preview_lbl.config(image=photo, text="")
                self._preview_lbl.image = photo
                self._img_ref = photo
            except Exception:
                pass
        run_bg(fetch, callback=done)

    def _load_cats(self):
        def fetch():
            return self.api.get("/categories")
        def done(r):
            inner = r.get("data") or {}
            cats = inner if isinstance(inner, list) else inner.get("categories", [])
            self._cat_map = {c["name"]: c["id"] for c in cats}
            self.cat_cb["values"] = list(self._cat_map.keys())
            if self.product:
                cat_obj = self.product.get("category") or self.product.get("Category") or {}
                if cat_obj.get("name") in self._cat_map:
                    self.v_cat.set(cat_obj["name"])
            if not self.v_cat.get() and self.cat_cb["values"]:
                self.v_cat.set(self.cat_cb["values"][0])
        run_bg(fetch, callback=done)

    def _save(self):
        name = self.v_name.get().strip()
        if not name:
            self._status_lbl.config(text="Product name is required.")
            return
        try:
            price = float(self.v_price.get().strip())
        except ValueError:
            self._status_lbl.config(text="Price must be a number.")
            return

        desc = self.desc_text.get("1.0", "end").strip()
        cat_id = self._cat_map.get(self.v_cat.get())
        stock_str = self.v_stock.get().strip()
        img_url = self.v_img.get().strip()
        feat = self.v_feat.get()
        active = self.v_avail.get()

        self.save_btn.config(state="disabled", text="Saving...")
        self._status_lbl.config(text="")

        def do():
            if self._file_path:
                try:
                    mime, _ = mimetypes.guess_type(self._file_path)
                    fname = self._file_path.replace("\\", "/").split("/")[-1]
                    with open(self._file_path, "rb") as f:
                        files = {"image": (fname, f, mime or "image/jpeg")}
                        fields = {
                            "name": name, "price": str(price), "description": desc,
                            "isFeatured": "true" if feat else "false",
                            "isActive": "true" if active else "false",
                        }
                        if stock_str:
                            try: fields["stock"] = str(int(stock_str))
                            except ValueError: pass
                        if cat_id:
                            fields["categoryId"] = str(cat_id)
                        if self.product:
                            r = self.api.session.put(
                                f"{self.api.base_url}/products/{self.product['id']}",
                                data=fields, files=files)
                        else:
                            r = self.api.session.post(
                                f"{self.api.base_url}/products",
                                data=fields, files=files)
                        return r.json()
                except Exception as e:
                    return {"_error": str(e)}
            else:
                body = {
                    "name": name, "price": price, "description": desc,
                    "isFeatured": feat, "isActive": active,
                }
                if img_url: body["imageUrl"] = img_url
                if stock_str:
                    try: body["stock"] = int(stock_str)
                    except ValueError: pass
                if cat_id: body["categoryId"] = cat_id
                if self.product:
                    return self.api.put(f"/products/{self.product['id']}", body)
                return self.api.post("/products", body)

        def done(r):
            if r.get("success") or r.get("data") or r.get("id"):
                self.on_save()
                self.destroy()
            else:
                self.save_btn.config(state="normal", text="Save Product")
                msg = r.get("message") or r.get("_error") or "Save failed."
                self._status_lbl.config(text=msg)
                messagebox.showerror("Error", msg)

        run_bg(do, callback=done)