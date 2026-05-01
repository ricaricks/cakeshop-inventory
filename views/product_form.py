import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import mimetypes
from config import *
from utils import run_bg
from views.widgets import section_sep, field_row, btn_primary, btn_secondary, apply_tree_style

try:
    from PIL import Image, ImageTk
    import io, requests as _req
    PIL_OK = True
except ImportError:
    PIL_OK = False


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

        for label, var in [("Price (₱) *", self.v_price), ("Stock", self.v_stock)]:
            col = tk.Frame(price_row, bg=BG)
            col.pack(side="left", fill="x", expand=True, padx=(0, 8 if label == "Price (₱) *" else 0))
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

    def _validate_image(self, file_path):
        valid_extensions = ('.jpg', '.jpeg', '.png', '.webp')
        return any(file_path.lower().endswith(ext) for ext in valid_extensions)

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp")]
        )
        if not path:
            return
        if not self._validate_image(path):
            messagebox.showerror("Invalid File", "Only JPG, PNG, and WEBP images are allowed.")
            return
        self._file_path = path
        name = path.replace("\\", "/").split("/")[-1]
        self._file_lbl.config(text=name[:42])
        self.v_img.set("")
        if PIL_OK:
            try:
                img = Image.open(path)
                img.thumbnail((80, 80), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._preview_lbl.config(image=photo, text="")
                self._preview_lbl.image = photo
                self._img_ref = photo
            except Exception as e:
                messagebox.showwarning("Preview Error", f"Cannot preview image: {str(e)}")

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
                    # Detect correct MIME type instead of hardcoding jpeg
                    mime_type, _ = mimetypes.guess_type(self._file_path)
                    mime_type = mime_type or "image/jpeg"
                    file_name = self._file_path.replace("\\", "/").split("/")[-1]

                    with open(self._file_path, 'rb') as f:
                        files = {'image': (file_name, f, mime_type)}
                        fields = {
                            "name": name,
                            "price": str(price),
                            "description": desc,
                            # Send as lowercase strings — avoids Python True/False JSON issues
                            "isFeatured": "true" if feat else "false",
                            "isActive": "true" if active else "false",
                        }
                        if stock_str:
                            try:
                                fields["stock"] = str(int(stock_str))
                            except ValueError:
                                pass
                        if cat_id:
                            fields["categoryId"] = str(cat_id)

                        if self.product:
                            r = self.api.session.put(
                                f"{self.api.base_url}/products/{self.product['id']}",
                                data=fields, files=files
                            )
                        else:
                            r = self.api.session.post(
                                f"{self.api.base_url}/products",
                                data=fields, files=files
                            )
                        return r.json()
                except Exception as e:
                    return {"_error": str(e)}
            else:
                body = {
                    "name": name,
                    "price": price,
                    "description": desc,
                    # Use proper Python bools for JSON — requests serialises correctly
                    "isFeatured": feat,
                    "isActive": active,
                }
                if img_url:
                    body["imageUrl"] = img_url
                if stock_str:
                    try:
                        body["stock"] = int(stock_str)
                    except ValueError:
                        pass
                if cat_id:
                    body["categoryId"] = cat_id

                if self.product:
                    return self.api.put(f"/products/{self.product['id']}", body)
                return self.api.post("/products", body)

        def done(r):
            # Accept success from any of: success flag, data present, or no error key
            ok = r.get("success") or r.get("data") or (
                not r.get("_error") and not r.get("message", "").lower().startswith("error")
                and r.get("id") is None  # avoid false positive on empty dict
            )
            # Simpler: treat any response with "data" or "success":true as OK
            ok = bool(r.get("success")) or bool(r.get("data")) or bool(r.get("id"))
            if ok:
                self.on_save()
                self.destroy()
            else:
                self.save_btn.config(state="normal", text="Save Product")
                error_msg = r.get("message") or r.get("_error") or "Save failed."
                self._status_lbl.config(text=error_msg)
                messagebox.showerror("Error", error_msg)

        run_bg(do, callback=done)