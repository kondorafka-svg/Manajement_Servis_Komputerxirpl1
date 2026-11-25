import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
import subprocess

from database import fetch_all, execute, check_connection
from auth import login_user, create_default_admin
from reports import export_excel, export_pdf
from config import DB_CONFIG, APP_TITLE


BLUE = "#1769AA"
DARK = "#123B5D"
LIGHT = "#EFF6FF"
WHITE = "#FFFFFF"
TEXT = "#1F2937"


TABLES = {
    "Pelanggan": {
        "key": "pelanggan",
        "table": "pelanggan",
        "pk": "id_pelanggan",
        "fields": [
            ("nama", "Nama pelanggan", "text"),
            ("alamat", "Alamat", "text"),
            ("telepon", "Nomor telepon", "text")
        ],
        "columns": ["id_pelanggan", "nama", "alamat", "telepon"],
        "select": "SELECT id_pelanggan, nama, alamat, telepon FROM pelanggan ORDER BY id_pelanggan DESC"
    },

    "Perangkat": {
        "key": "perangkat",
        "table": "perangkat",
        "pk": "id_perangkat",
        "fields": [
            ("id_pelanggan", "Pelanggan", "customer"),
            ("jenis", "Jenis perangkat", "text"),
            ("merek", "Merek", "text"),
            ("model", "Model", "text"),
            ("nomor_seri", "Nomor seri", "text")
        ],
        "columns": [
            "id_perangkat", "pelanggan", "jenis",
            "merek", "model", "nomor_seri"
        ],
        "select": """
            SELECT p.id_perangkat, pl.nama AS pelanggan,
            p.jenis, p.merek, p.model, p.nomor_seri
            FROM perangkat p
            JOIN pelanggan pl ON p.id_pelanggan=pl.id_pelanggan
            ORDER BY p.id_perangkat DESC
        """
    },

    "Teknisi": {
        "key": "teknisi",
        "table": "teknisi",
        "pk": "id_teknisi",
        "fields": [
            ("nama", "Nama teknisi", "text"),
            ("telepon", "Nomor telepon", "text"),
            ("keahlian", "Keahlian", "text")
        ],
        "columns": [
            "id_teknisi", "nama", "telepon", "keahlian"
        ],
        "select": "SELECT id_teknisi, nama, telepon, keahlian FROM teknisi ORDER BY id_teknisi DESC"
    },

    "Servis": {
        "key": "servis",
        "table": "servis",
        "pk": "id_servis",
        "fields": [
            ("id_perangkat", "Perangkat", "device"),
            ("id_teknisi", "Teknisi", "technician"),
            ("tanggal_masuk", "Tanggal masuk (YYYY-MM-DD)", "date"),
            ("kerusakan", "Keluhan/kerusakan", "text"),
            ("tindakan", "Tindakan perbaikan", "text"),
            ("status", "Status", "status"),
            ("biaya", "Biaya servis", "number")
        ],
        "columns": [
            "id_servis", "pelanggan", "perangkat",
            "teknisi", "tanggal_masuk",
            "kerusakan", "status", "biaya"
        ],
        "select": """
            SELECT s.id_servis,
            pl.nama AS pelanggan,
            CONCAT(p.jenis,' ',p.merek,' ',p.model) AS perangkat,
            COALESCE(t.nama,'Belum ditugaskan') AS teknisi,
            s.tanggal_masuk, s.kerusakan,
            s.status, s.biaya
            FROM servis s
            JOIN perangkat p ON s.id_perangkat=p.id_perangkat
            JOIN pelanggan pl ON p.id_pelanggan=pl.id_pelanggan
            LEFT JOIN teknisi t ON s.id_teknisi=t.id_teknisi
            ORDER BY s.id_servis DESC
        """
    },

    "Pembayaran": {
        "key": "pembayaran",
        "table": "pembayaran",
        "pk": "id_pembayaran",
        "fields": [
            ("id_servis", "ID servis", "service"),
            ("tanggal_bayar", "Tanggal bayar (YYYY-MM-DD)", "date"),
            ("jumlah", "Jumlah pembayaran", "number"),
            ("metode", "Metode pembayaran", "method")
        ],
        "columns": [
            "id_pembayaran", "id_servis",
            "tanggal_bayar", "jumlah", "metode"
        ],
        "select": """
            SELECT id_pembayaran, id_servis,
            tanggal_bayar, jumlah, metode
            FROM pembayaran
            ORDER BY id_pembayaran DESC
        """
    }
}


class LoginWindow:

    def __init__(self, root):
        self.root = root

        root.title("Login - " + APP_TITLE)
        root.geometry("420x360")
        root.configure(bg=LIGHT)
        root.resizable(False, False)

        card = tk.Frame(
            root,
            bg=WHITE,
            padx=30,
            pady=28,
            highlightthickness=1,
            highlightbackground="#D6E4F0"
        )

        card.place(
            relx=.5,
            rely=.5,
            anchor="center",
            width=340,
            height=290
        )

        tk.Label(
            card,
            text="SERVIS KOMPUTER",
            bg=WHITE,
            fg=BLUE,
            font=("Segoe UI", 17, "bold")
        ).pack(pady=(2, 5))

        tk.Label(
            card,
            text="Silakan masuk ke aplikasi",
            bg=WHITE,
            fg="#64748B"
        ).pack(pady=(0, 20))

        tk.Label(
            card,
            text="Username",
            bg=WHITE,
            fg=TEXT
        ).pack(anchor="w")

        self.username = ttk.Entry(card)
        self.username.pack(fill="x", pady=(4, 12))

        tk.Label(
            card,
            text="Password",
            bg=WHITE,
            fg=TEXT
        ).pack(anchor="w")

        self.password = ttk.Entry(card, show="*")
        self.password.pack(fill="x", pady=(4, 18))

        ttk.Button(
            card,
            text="LOGIN",
            command=self.login
        ).pack(fill="x")

        tk.Label(
            card,
            text="Default: admin / admin123",
            bg=WHITE,
            fg="#64748B"
        ).pack(pady=12)

        self.password.bind(
            "<Return>",
            lambda e: self.login()
        )

    def login(self):

        try:
            user = login_user(
                self.username.get().strip(),
                self.password.get()
            )

            if not user:
                messagebox.showerror(
                    "Login gagal",
                    "Username atau password salah."
                )
                return

            self.root.destroy()

            main_root = tk.Tk()
            ServiceApp(main_root, user)
            main_root.mainloop()

        except Exception as e:
            messagebox.showerror(
                "Koneksi database",
                f"Tidak dapat mengakses MySQL.\n\n{e}"
            )


class ServiceApp:

    def __init__(self, root, user):

        self.root = root
        self.user = user

        root.title(APP_TITLE)
        root.geometry("1200x760")
        root.minsize(980, 620)
        root.configure(bg=LIGHT)

        self.style()
        self.build_layout()
        self.show_dashboard()

    def style(self):

        s = ttk.Style()

        try:
            s.theme_use("clam")
        except tk.TclError:
            pass

        s.configure("TFrame", background=LIGHT)

        s.configure(
            "TLabel",
            background=LIGHT,
            foreground=TEXT,
            font=("Segoe UI", 9)
        )

        s.configure(
            "Treeview",
            rowheight=29,
            font=("Segoe UI", 9),
            background=WHITE,
            fieldbackground=WHITE
        )

        s.configure(
            "Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#DCEBFA",
            foreground=DARK
        )

        s.configure(
            "TButton",
            font=("Segoe UI", 9),
            padding=7
        )

        s.configure(
            "Accent.TButton",
            background=BLUE,
            foreground=WHITE,
            font=("Segoe UI", 9, "bold")
        )

    def build_layout(self):

        header = tk.Frame(
            self.root,
            bg=DARK,
            height=65
        )

        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="  🖥  MANAJEMEN SERVIS KOMPUTER",
            bg=DARK,
            fg=WHITE,
            font=("Segoe UI", 15, "bold")
        ).pack(side="left", padx=10)

        tk.Label(
            header,
            text=f"{self.user['nama']} | {self.user['role']}  ",
            bg=DARK,
            fg="#DBEAFE"
        ).pack(side="right")

        body = tk.Frame(
            self.root,
            bg=LIGHT
        )

        body.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(
            body,
            bg=WHITE,
            width=205
        )

        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(
            self.sidebar,
            text="MENU UTAMA",
            bg=WHITE,
            fg="#64748B",
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w", padx=18, pady=(22, 10))

        menus = [("Dashboard", self.show_dashboard)]

        menus += [
            (name, lambda n=name: self.show_table(n))
            for name in TABLES
        ]

        for name, command in menus:

            tk.Button(
                self.sidebar,
                text="   " + name,
                command=command,
                anchor="w",
                relief="flat",
                bd=0,
                bg=WHITE,
                fg=DARK,
                activebackground=LIGHT,
                font=("Segoe UI", 10),
                padx=12,
                pady=10
            ).pack(fill="x", padx=8, pady=1)

        ttk.Separator(
            self.sidebar
        ).pack(fill="x", padx=14, pady=12)

        tk.Button(
            self.sidebar,
            text="   Ekspor laporan PDF",
            command=self.pdf_report,
            anchor="w",
            relief="flat",
            bg=WHITE,
            fg=DARK,
            padx=12,
            pady=9
        ).pack(fill="x", padx=8)

        tk.Button(
            self.sidebar,
            text="   Backup database",
            command=self.backup_db,
            anchor="w",
            relief="flat",
            bg=WHITE,
            fg=DARK,
            padx=12,
            pady=9
        ).pack(fill="x", padx=8)

        tk.Button(
            self.sidebar,
            text="   Restore database",
            command=self.restore_db,
            anchor="w",
            relief="flat",
            bg=WHITE,
            fg=DARK,
            padx=12,
            pady=9
        ).pack(fill="x", padx=8)

        self.content = tk.Frame(
            body,
            bg=LIGHT,
            padx=24,
            pady=22
        )

        self.content.pack(
            side="left",
            fill="both",
            expand=True
        )

    def clear_content(self):

        for w in self.content.winfo_children():
            w.destroy()

    def heading(self, title, subtitle=""):

        tk.Label(
            self.content,
            text=title,
            bg=LIGHT,
            fg=DARK,
            font=("Segoe UI", 19, "bold")
        ).pack(anchor="w")

        if subtitle:
            tk.Label(
                self.content,
                text=subtitle,
                bg=LIGHT,
                fg="#64748B"
            ).pack(anchor="w", pady=(3, 15))


def show_dashboard(self):

    self.clear_content()

    self.heading(
        "Dashboard",
        "Ringkasan aktivitas usaha servis komputer."
    )

    try:

        total_customer = fetch_all(
            "SELECT COUNT(*) n FROM pelanggan"
        )[0]["n"]

        total_device = fetch_all(
            "SELECT COUNT(*) n FROM perangkat"
        )[0]["n"]

        total_service = fetch_all(
            "SELECT COUNT(*) n FROM servis"
        )[0]["n"]

        waiting = fetch_all(
            "SELECT COUNT(*) n FROM servis WHERE status IN ('Menunggu','Diproses')"
        )[0]["n"]

        income = fetch_all(
            "SELECT COALESCE(SUM(jumlah),0) n FROM pembayaran"
        )[0]["n"]

        # KARTU STATISTIK
        cards = [
            ("Total pelanggan", total_customer),
            ("Total perangkat", total_device),
            ("Total servis", total_service),
            ("Menunggu/diproses", waiting),
            ("Total pembayaran", f"Rp {income:,.0f}")
        ]

        wrap = tk.Frame(
            self.content,
            bg=LIGHT
        )

        wrap.pack(fill="x", pady=12)

        for i, (label, value) in enumerate(cards):

            card = tk.Frame(
                wrap,
                bg=WHITE,
                padx=18,
                pady=18,
                highlightthickness=1,
                highlightbackground="#D6E4F0"
            )

            card.grid(
                row=i // 3,
                column=i % 3,
                sticky="nsew",
                padx=6,
                pady=6
            )

            tk.Label(
                card,
                text=label,
                bg=WHITE,
                fg="#64748B"
            ).pack(anchor="w")

            tk.Label(
                card,
                text=str(value),
                bg=WHITE,
                fg=BLUE,
                font=("Segoe UI", 19, "bold")
            ).pack(anchor="w", pady=(8, 0))

        for i in range(3):
            wrap.grid_columnconfigure(i, weight=1)

        # DATA GRAFIK 6 BULAN
        monthly_rows = fetch_all("""
            SELECT
                DATE_FORMAT(tanggal_masuk, '%Y-%m') AS bulan,
                COUNT(*) AS jumlah
            FROM servis
            WHERE tanggal_masuk >= DATE_SUB(
                DATE_FORMAT(CURDATE(), '%Y-%m-01'),
                INTERVAL 5 MONTH
            )
            GROUP BY DATE_FORMAT(tanggal_masuk, '%Y-%m')
            ORDER BY bulan
        """)

        monthly_data = {
            r["bulan"]: r["jumlah"]
            for r in monthly_rows
        }

        today = date.today()
        month_keys = []

        year = today.year
        month = today.month

        for _ in range(6):
            month_keys.append(f"{year:04d}-{month:02d}")

            month -= 1

            if month == 0:
                month = 12
                year -= 1

        month_keys.reverse()

        month_names = [
            "Jan", "Feb", "Mar", "Apr",
            "Mei", "Jun", "Jul", "Agu",
            "Sep", "Okt", "Nov", "Des"
        ]

        # DATA GRAFIK STATUS
        status_rows = fetch_all("""
            SELECT status, COUNT(*) AS jumlah
            FROM servis
            GROUP BY status
            ORDER BY status
        """)

        # TEMPAT GRAFIK
        charts_frame = tk.Frame(
            self.content,
            bg=LIGHT
        )

        charts_frame.pack(
            fill="x",
            pady=(12, 15)
        )

        # GRAFIK AKTIVITAS SERVIS
        monthly_card = tk.Frame(
            charts_frame,
            bg=WHITE,
            padx=14,
            pady=12,
            highlightthickness=1,
            highlightbackground="#D6E4F0"
        )

        monthly_card.pack(
            side="left",
            fill="both",
            expand=True,
            padx=6
        )

        tk.Label(
            monthly_card,
            text="Aktivitas Servis (6 Bulan)",
            bg=WHITE,
            fg=DARK,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 8))

        monthly_chart = tk.Canvas(
            monthly_card,
            height=190,
            bg=WHITE,
            highlightthickness=0
        )

        monthly_chart.pack(fill="x")

        def draw_monthly_chart(event=None):

            monthly_chart.delete("all")

            width = max(monthly_chart.winfo_width(), 300)

            left = 35
            right = width - 12
            top = 12
            bottom = 145

            values = [
                monthly_data.get(key, 0)
                for key in month_keys
            ]

            max_value = max(values) if values else 0
            scale = max(max_value, 1)

            for step in range(4):

                y = bottom - step * (bottom - top) / 3

                amount = round(scale * step / 3)

                monthly_chart.create_line(
                    left, y, right, y,
                    fill="#E2E8F0",
                    dash=(3, 3)
                )

                monthly_chart.create_text(
                    left - 7,
                    y,
                    text=str(amount),
                    anchor="e",
                    fill="#64748B",
                    font=("Segoe UI", 8)
                )

            slot = (right - left) / 6
            bar_width = min(30, slot * 0.55)

            for i, key in enumerate(month_keys):

                value = monthly_data.get(key, 0)

                center = left + slot * (i + 0.5)

                bar_height = (
                    value / scale
                ) * (bottom - top)

                if value > 0:

                    monthly_chart.create_rectangle(
                        center - bar_width / 2,
                        bottom - bar_height,
                        center + bar_width / 2,
                        bottom,
                        fill=BLUE,
                        outline=""
                    )

                    monthly_chart.create_text(
                        center,
                        max(bottom - bar_height - 10, top),
                        text=str(value),
                        fill=DARK,
                        font=("Segoe UI", 8, "bold")
                    )

                month_number = int(key.split("-")[1])

                monthly_chart.create_text(
                    center,
                    bottom + 18,
                    text=month_names[month_number - 1],
                    fill="#64748B",
                    font=("Segoe UI", 8)
                )

        monthly_chart.bind(
            "<Configure>",
            draw_monthly_chart
        )

        monthly_chart.after(
            100,
            draw_monthly_chart
        )

        # GRAFIK STATUS SERVIS
        status_card = tk.Frame(
            charts_frame,
            bg=WHITE,
            padx=14,
            pady=12,
            highlightthickness=1,
            highlightbackground="#D6E4F0"
        )

        status_card.pack(
            side="left",
            fill="both",
            expand=True,
            padx=6
        )

        tk.Label(
            status_card,
            text="Statistik Status Servis",
            bg=WHITE,
            fg=DARK,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 8))

        status_chart = tk.Canvas(
            status_card,
            height=190,
            bg=WHITE,
            highlightthickness=0
        )

        status_chart.pack(fill="x")

        def draw_status_chart(event=None):

            status_chart.delete("all")

            width = max(status_chart.winfo_width(), 300)

            colors = [
                "#D97706",
                "#1769AA",
                "#15803D",
                "#7C3AED",
                "#DC2626"
            ]

            if not status_rows:

                status_chart.create_text(
                    width / 2,
                    90,
                    text="Belum ada data servis",
                    fill="#64748B"
                )

                return

            max_value = max(
                r["jumlah"] for r in status_rows
            )

            max_value = max(max_value, 1)

            y = 12

            for i, row in enumerate(status_rows):

                label = str(row["status"])
                value = row["jumlah"]

                status_chart.create_text(
                    5,
                    y + 9,
                    text=label[:16],
                    anchor="w",
                    fill="#475569",
                    font=("Segoe UI", 8)
                )

                bar_start = 105
                bar_end = width - 45

                bar_width = (
                    (value / max_value) *
                    max(bar_end - bar_start, 20)
                )

                status_chart.create_rectangle(
                    bar_start,
                    y,
                    bar_end,
                    y + 18,
                    fill="#F1F5F9",
                    outline=""
                )

                status_chart.create_rectangle(
                    bar_start,
                    y,
                    bar_start + bar_width,
                    y + 18,
                    fill=colors[i % len(colors)],
                    outline=""
                )

                status_chart.create_text(
                    width - 5,
                    y + 9,
                    text=str(value),
                    anchor="e",
                    fill=DARK,
                    font=("Segoe UI", 8, "bold")
                )

                y += 32

        status_chart.bind(
            "<Configure>",
            draw_status_chart
        )

        status_chart.after(
            100,
            draw_status_chart
        )

        # TABEL SERVIS TERBARU
        tk.Label(
            self.content,
            text="Servis terbaru",
            bg=LIGHT,
            fg=DARK,
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", pady=(10, 8))

        tree = ttk.Treeview(
            self.content,
            columns=(
                "id",
                "pelanggan",
                "perangkat",
                "status",
                "biaya"
            ),
            show="headings",
            height=8
        )

        for c, title, width in [
            ("id", "ID", 55),
            ("pelanggan", "Pelanggan", 180),
            ("perangkat", "Perangkat", 200),
            ("status", "Status", 130),
            ("biaya", "Biaya", 120)
        ]:

            tree.heading(c, text=title)
            tree.column(c, width=width)

        tree.pack(fill="x")

        rows = fetch_all("""
            SELECT
                s.id_servis,
                pl.nama AS pelanggan,
                CONCAT(p.jenis,' ',p.merek) AS perangkat,
                s.status,
                s.biaya
            FROM servis s
            JOIN perangkat p
                ON s.id_perangkat=p.id_perangkat
            JOIN pelanggan pl
                ON p.id_pelanggan=pl.id_pelanggan
            ORDER BY s.id_servis DESC
            LIMIT 10
        """)

        for r in rows:

            tree.insert(
                "",
                "end",
                values=(
                    r["id_servis"],
                    r["pelanggan"],
                    r["perangkat"],
                    r["status"],
                    f"Rp {float(r['biaya'] or 0):,.0f}"
                )
            )

    except Exception as e:

        messagebox.showerror(
            "Dashboard",
            f"Gagal memuat data.\n{e}"
        )

    def show_table(self, menu):

        self.clear_content()

        cfg = TABLES[menu]

        self.heading(
            "Data " + menu,
            f"Kelola data {menu.lower()}."
        )

        toolbar = tk.Frame(
            self.content,
            bg=LIGHT
        )

        toolbar.pack(fill="x", pady=(0, 10))

        search_var = tk.StringVar()

        ttk.Entry(
            toolbar,
            textvariable=search_var,
            width=32
        ).pack(side="left", padx=(0, 6))

        tree_frame = tk.Frame(
            self.content,
            bg=WHITE
        )

        tree_frame.pack(
            fill="both",
            expand=True
        )

        tree = ttk.Treeview(
            tree_frame,
            columns=cfg["columns"],
            show="headings"
        )

        yscroll = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=tree.yview
        )

        xscroll = ttk.Scrollbar(
            tree_frame,
            orient="horizontal",
            command=tree.xview
        )

        tree.configure(
            yscrollcommand=yscroll.set,
            xscrollcommand=xscroll.set
        )

        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        for c in cfg["columns"]:

            tree.heading(
                c,
                text=c.replace("_", " ").title()
            )

            tree.column(
                c,
                width=135,
                minwidth=90
            )

        def load():

            try:

                for item in tree.get_children():
                    tree.delete(item)

                rows = fetch_all(cfg["select"])

                term = search_var.get().strip().lower()

                for row in rows:

                    vals = [
                        row.get(c, "")
                        for c in cfg["columns"]
                    ]

                    if term and term not in " ".join(
                        str(v) for v in vals
                    ).lower():
                        continue

                    tree.insert(
                        "",
                        "end",
                        iid=str(row[cfg["columns"][0]]),
                        values=vals
                    )

            except Exception as e:

                messagebox.showerror(
                    "Gagal memuat",
                    str(e)
                )

        def selected_id():

            sel = tree.selection()

            return int(sel[0]) if sel else None

        def form(mode):

            selected = selected_id()

            if mode == "edit" and not selected:

                messagebox.showwarning(
                    "Pilih data",
                    "Pilih satu baris yang ingin diubah."
                )

                return

            old = None

            if selected:

                old = fetch_all(
                    f"SELECT * FROM {cfg['table']} WHERE {cfg['pk']}=%s",
                    (selected,)
                )

                old = old[0] if old else {}

            win = tk.Toplevel(self.root)

            win.title(
                ("Tambah " if mode == "add" else "Ubah ") + menu
            )

            win.geometry("470x620")
            win.configure(bg=LIGHT)
            win.transient(self.root)
            win.grab_set()

            canvas = tk.Canvas(
                win,
                bg=LIGHT,
                highlightthickness=0
            )

            canvas.pack(
                side="left",
                fill="both",
                expand=True
            )

            inner = tk.Frame(
                canvas,
                bg=LIGHT,
                padx=22,
                pady=18
            )

            canvas.create_window(
                (0, 0),
                window=inner,
                anchor="nw",
                width=440
            )

            widgets = {}

            tk.Label(
                inner,
                text=("Tambah " if mode == "add" else "Ubah ") + menu,
                bg=LIGHT,
                fg=DARK,
                font=("Segoe UI", 15, "bold")
            ).pack(anchor="w", pady=(0, 15))

            for field, label, kind in cfg["fields"]:

                tk.Label(
                    inner,
                    text=label,
                    bg=LIGHT,
                    fg=TEXT
                ).pack(anchor="w", pady=(7, 3))

                if kind in (
                    "customer",
                    "device",
                    "technician",
                    "service"
                ):

                    if kind == "customer":

                        opts = fetch_all(
                            "SELECT id_pelanggan, nama FROM pelanggan ORDER BY nama"
                        )

                        values = [
                            f"{x['id_pelanggan']} - {x['nama']}"
                            for x in opts
                        ]

                    elif kind == "device":

                        opts = fetch_all("""
                            SELECT p.id_perangkat, pl.nama,
                            p.jenis, p.merek
                            FROM perangkat p
                            JOIN pelanggan pl
                            ON p.id_pelanggan=pl.id_pelanggan
                        """)

                        values = [
                            f"{x['id_perangkat']} - {x['nama']} / {x['jenis']} {x['merek']}"
                            for x in opts
                        ]

                    elif kind == "technician":

                        opts = fetch_all(
                            "SELECT id_teknisi, nama FROM teknisi ORDER BY nama"
                        )

                        values = [""] + [
                            f"{x['id_teknisi']} - {x['nama']}"
                            for x in opts
                        ]

                    else:

                        opts = fetch_all(
                            "SELECT id_servis FROM servis ORDER BY id_servis DESC"
                        )

                        values = [
                            str(x["id_servis"])
                            for x in opts
                        ]

                    widget = ttk.Combobox(
                        inner,
                        values=values,
                        state="readonly"
                    )

                    if kind == "technician":
                        widget.set("")

                    elif kind == "service":
                        widget.set(values[0] if values else "")

                    if old and old.get(field):

                        prefix = str(old[field]) + " -"

                        match = next(
                            (v for v in values if v.startswith(prefix)),
                            None
                        )

                        if match:
                            widget.set(match)

                        elif kind == "service":
                            widget.set(str(old[field]))

                    elif kind in ("customer", "device") and values:

                        widget.set(values[0])

                elif kind == "status":

                    widget = ttk.Combobox(
                        inner,
                        values=[
                            "Menunggu",
                            "Diproses",
                            "Selesai",
                            "Diambil",
                            "Dibatalkan"
                        ],
                        state="readonly"
                    )

                    widget.set(
                        old.get(field, "Menunggu")
                        if old else "Menunggu"
                    )

                elif kind == "method":

                    widget = ttk.Combobox(
                        inner,
                        values=[
                            "Tunai",
                            "Transfer",
                            "QRIS",
                            "Debit"
                        ],
                        state="readonly"
                    )

                    widget.set(
                        old.get(field, "Tunai")
                        if old else "Tunai"
                    )

                else:

                    widget = ttk.Entry(inner)

                    if old and old.get(field) is not None:

                        widget.insert(
                            0,
                            str(old[field])
                        )

                    elif kind == "date":

                        widget.insert(
                            0,
                            str(date.today())
                        )

                    elif kind == "number":

                        widget.insert(0, "0")

                widget.pack(fill="x")

                widgets[field] = (widget, kind)

            def save():

                vals = {}

                try:

                    for field, (widget, kind) in widgets.items():

                        value = widget.get().strip()

                        if kind in (
                            "customer",
                            "device",
                            "technician"
                        ):

                            value = (
                                int(value.split(" - ")[0])
                                if value else None
                            )

                        elif kind == "service":

                            value = int(value) if value else None

                        elif kind == "number":

                            value = float(value or 0)

                        if kind != "technician" and value in ("", None):

                            raise ValueError(
                                f"{field} wajib diisi."
                            )

                        vals[field] = value

                    if mode == "add":

                        cols = list(vals)

                        placeholders = ",".join(
                            ["%s"] * len(cols)
                        )

                        execute(
                            f"INSERT INTO {cfg['table']} ({','.join(cols)}) VALUES ({placeholders})",
                            tuple(vals.values())
                        )

                    else:

                        assignments = ",".join(
                            f"{c}=%s" for c in vals
                        )

                        execute(
                            f"UPDATE {cfg['table']} SET {assignments} WHERE {cfg['pk']}=%s",
                            tuple(vals.values()) + (selected,)
                        )

                    win.destroy()
                    load()

                except Exception as e:

                    messagebox.showerror(
                        "Validasi / database",
                        str(e),
                        parent=win
                    )

            ttk.Button(
                inner,
                text="Simpan",
                command=save,
                style="Accent.TButton"
            ).pack(fill="x", pady=18)

        ttk.Button(
            toolbar,
            text="Cari",
            command=load
        ).pack(side="left", padx=3)

        ttk.Button(
            toolbar,
            text="Tampilkan semua",
            command=lambda: (search_var.set(""), load())
        ).pack(side="left", padx=3)

        ttk.Button(
            toolbar,
            text="+ Tambah",
            command=lambda: form("add"),
            style="Accent.TButton"
        ).pack(side="right", padx=3)

        ttk.Button(
            toolbar,
            text="Ubah",
            command=lambda: form("edit")
        ).pack(side="right", padx=3)

        def delete():

            sid = selected_id()

            if not sid:

                messagebox.showwarning(
                    "Pilih data",
                    "Pilih data yang akan dihapus."
                )

                return

            if messagebox.askyesno(
                "Konfirmasi",
                "Yakin ingin menghapus data terpilih?"
            ):

                try:

                    execute(
                        f"DELETE FROM {cfg['table']} WHERE {cfg['pk']}=%s",
                        (sid,)
                    )

                    load()

                except Exception as e:

                    messagebox.showerror(
                        "Tidak dapat menghapus",
                        f"Data mungkin masih digunakan tabel lain.\n\n{e}"
                    )

        ttk.Button(
            toolbar,
            text="Hapus",
            command=delete
        ).pack(side="right", padx=3)

        ttk.Button(
            toolbar,
            text="Ekspor Excel",
            command=lambda: self.excel_report(cfg["key"])
        ).pack(side="right", padx=3)

        load()

    def excel_report(self, key):

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"laporan_{key}.xlsx"
        )

        if path:

            try:

                export_excel(key, path)

                messagebox.showinfo(
                    "Berhasil",
                    f"File tersimpan:\n{path}"
                )

            except Exception as e:

                messagebox.showerror(
                    "Ekspor gagal",
                    str(e)
                )

    def pdf_report(self):

        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="laporan_servis.pdf"
        )

        if path:

            try:

                export_pdf(path)

                messagebox.showinfo(
                    "Berhasil",
                    f"Laporan tersimpan:\n{path}"
                )

            except Exception as e:

                messagebox.showerror(
                    "Ekspor gagal",
                    str(e)
                )

    def backup_db(self):

        path = filedialog.asksaveasfilename(
            defaultextension=".sql",
            filetypes=[("SQL", "*.sql")],
            initialfile="backup_servis.sql"
        )

        if not path:
            return

        cmd = [
            r"C:\xampp\mysql\bin\mysqldump.exe",
            "-h", DB_CONFIG["host"],
            "-P", str(DB_CONFIG["port"]),
            "-u", DB_CONFIG["user"],
            DB_CONFIG["database"]
        ]

        if DB_CONFIG["password"]:
            cmd.insert(-1, "-p" + DB_CONFIG["password"])

        try:

            with open(path, "w", encoding="utf-8") as f:

                subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )

            messagebox.showinfo(
                "Backup berhasil",
                f"Backup tersimpan:\n{path}"
            )

        except subprocess.CalledProcessError as e:

            messagebox.showerror(
                "Backup gagal",
                e.stderr
            )

        except Exception as e:

            messagebox.showerror(
                "Backup gagal",
                str(e)
            )

    def restore_db(self):

        path = filedialog.askopenfilename(
            title="Pilih file backup database",
            filetypes=[("File SQL", "*.sql")]
        )

        if not path:
            return

        if not messagebox.askyesno(
            "Konfirmasi Restore",
            "Restore dapat menimpa data yang ada.\nYakin ingin melanjutkan?"
        ):
            return

        cmd = [
            r"C:\xampp\mysql\bin\mysql.exe",
            "-h", DB_CONFIG["host"],
            "-P", str(DB_CONFIG["port"]),
            "-u", DB_CONFIG["user"],
            DB_CONFIG["database"]
        ]

        if DB_CONFIG["password"]:
            cmd.insert(-1, "-p" + DB_CONFIG["password"])

        try:

            with open(path, "r", encoding="utf-8") as file:

                subprocess.run(
                    cmd,
                    stdin=file,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )

            messagebox.showinfo(
                "Restore Berhasil",
                "Database berhasil dipulihkan!"
            )

            self.show_dashboard()

        except subprocess.CalledProcessError as e:

            messagebox.showerror(
                "Restore Gagal",
                f"Terjadi kesalahan:\n{e.stderr}"
            )

        except Exception as e:

            messagebox.showerror(
                "Restore Gagal",
                str(e)
            )


if __name__ == "__main__":

    try:

        check_connection()
        create_default_admin()

        root = tk.Tk()

        LoginWindow(root)

        root.mainloop()

    except Exception as e:

        messagebox.showerror(
            "Kesalahan aplikasi",
            f"Tidak dapat menjalankan aplikasi:\n{e}"
        )