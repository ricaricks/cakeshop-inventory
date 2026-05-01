import tkinter as tk
from config import *
from api import ApiClient
from utils import set_root, run_bg
from views import ProductsView, CategoriesView, OrdersView

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rica's Cake Shop")
        self.geometry("1200x700")
        self.minsize(1000, 600)
        self.configure(bg=BG)
        self.api = ApiClient()
        set_root(self)
        
        if self.api.token:
            self._build_main()
        else:
            self._build_login()
    
    def _build_login(self):
        for w in self.winfo_children():
            w.destroy()
        
        center_frame = tk.Frame(self, bg=BG)
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        login_card = tk.Frame(center_frame, bg=CARD, highlightthickness=1, 
                              highlightbackground=BORDER)
        login_card.pack(padx=40, pady=40, ipadx=50, ipady=40)
        
        tk.Label(login_card, text="🎂", font=("Segoe UI", 48), bg=CARD, fg=ACCENT).pack()
        tk.Label(login_card, text="Rica's Cake Shop", font=FONT_H, bg=CARD, fg=TEXT).pack(pady=(8, 4))
        tk.Label(login_card, text="Inventory Management", font=FONT_SM, bg=CARD, fg=TEXT2).pack()
        
        form_frame = tk.Frame(login_card, bg=CARD)
        form_frame.pack(pady=30)
        
        tk.Label(form_frame, text="Email", font=FONT, bg=CARD, fg=TEXT).pack(anchor="w")
        self.email_entry = tk.Entry(form_frame, font=FONT, relief="flat", 
                                     bg=BG, width=30, highlightthickness=1, 
                                     highlightbackground=BORDER)
        self.email_entry.pack(pady=(4, 12), ipady=8)
        self.email_entry.insert(0, ADMIN_EMAIL)
        
        tk.Label(form_frame, text="Password", font=FONT, bg=CARD, fg=TEXT).pack(anchor="w")
        self.pw_entry = tk.Entry(form_frame, font=FONT, show="•", relief="flat",
                                  bg=BG, width=30, highlightthickness=1,
                                  highlightbackground=BORDER)
        self.pw_entry.pack(pady=(4, 20), ipady=8)
        self.pw_entry.insert(0, ADMIN_PASSWORD)
        
        self.login_btn = tk.Button(form_frame, text="Login", font=FONT_B,
                                    bg=ACCENT, fg=WHITE, relief="flat", cursor="hand2",
                                    command=self._do_login, padx=20, pady=8)
        self.login_btn.pack(fill="x")
        
        self.status_label = tk.Label(login_card, text="", font=FONT_SM, bg=CARD, fg=ACCENT)
        self.status_label.pack(pady=(10, 0))
        
        self.email_entry.bind("<Return>", lambda e: self.pw_entry.focus())
        self.pw_entry.bind("<Return>", lambda e: self._do_login())
    
    def _do_login(self):
        email = self.email_entry.get().strip()
        pw = self.pw_entry.get().strip()
        self.login_btn.config(state="disabled", text="Logging in...")
        self.status_label.config(text="")
        
        def attempt():
            return self.api.login(email, pw)
        
        def done(result):
            ok, msg = result
            if ok:
                self._build_main()
            else:
                self.login_btn.config(state="normal", text="Login")
                self.status_label.config(text=f"Login failed: {msg}")
        
        run_bg(attempt, callback=done)
    
    def _build_main(self):
        for w in self.winfo_children():
            w.destroy()
        
        self.sidebar = tk.Frame(self, bg=SIDEBAR, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        logo_frame = tk.Frame(self.sidebar, bg=SIDEBAR)
        logo_frame.pack(fill="x", pady=(30, 20))
        tk.Label(logo_frame, text="🎂", font=("Segoe UI", 36), bg=SIDEBAR, fg=ACCENT2).pack()
        tk.Label(logo_frame, text="Rica's Cakes", font=FONT_SH, bg=SIDEBAR, fg=WHITE).pack()
        tk.Label(logo_frame, text="Admin Panel", font=FONT_SM, bg=SIDEBAR, fg=MUTED).pack()
        
        nav_frame = tk.Frame(self.sidebar, bg=SIDEBAR)
        nav_frame.pack(fill="x", pady=20)
        
        nav_buttons = [
            ("📦 Products", self._show_products),
            ("📁 Categories", self._show_categories),
            ("🛒 Orders", self._show_orders)
        ]
        
        for text, cmd in nav_buttons:
            btn = tk.Button(nav_frame, text=text, font=FONT, bg=SIDEBAR, fg=ACCENT2,
                           relief="flat", anchor="w", padx=24, pady=12, cursor="hand2",
                           activebackground=SB_HOV, activeforeground=WHITE,
                           command=cmd)
            btn.pack(fill="x")
        
        tk.Button(self.sidebar, text="🚪 Logout", font=FONT, bg=SIDEBAR, fg=MUTED,
                 relief="flat", anchor="w", padx=24, pady=12, cursor="hand2",
                 activebackground=SB_HOV, activeforeground=WHITE,
                 command=self._logout).pack(side="bottom", fill="x", pady=20)
        
        self.content_frame = tk.Frame(self, bg=BG)
        self.content_frame.pack(side="left", fill="both", expand=True)
        
        self._show_products()
    
    def _show_products(self):
        for w in self.content_frame.winfo_children():
            w.destroy()
        ProductsView(self.content_frame, self.api)
    
    def _show_categories(self):
        for w in self.content_frame.winfo_children():
            w.destroy()
        CategoriesView(self.content_frame, self.api)
    
    def _show_orders(self):
        for w in self.content_frame.winfo_children():
            w.destroy()
        OrdersView(self.content_frame, self.api)
    
    def _logout(self):
        self.api.logout()
        self._build_login()

if __name__ == "__main__":
    app = App()
    
    app.mainloop()