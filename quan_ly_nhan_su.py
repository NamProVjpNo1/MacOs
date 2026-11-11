import csv, os, shutil, sqlite3, subprocess, sys, time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date, timezone, timedelta

BASE = os.path.join(os.path.expanduser("~"), "QuanLyNhanSu")
os.makedirs(os.path.join(BASE, "tailieu"), exist_ok=True)
db = sqlite3.connect(os.path.join(BASE, "nhansu.db"))

# kind: text | date | choice | emp (chọn nhân viên) | file | long
EMP = [
    ("so_hieu", "Số hiệu *", "text", None), ("ho_ten", "Họ tên *", "text", None),
    ("ngay_sinh", "Ngày sinh", "date", None),
    ("gioi_tinh", "Giới tính", "choice", ["Nam", "Nữ", "Khác"]),
    ("cccd", "CCCD", "text", None), ("sdt", "Điện thoại", "text", None),
    ("email", "Email", "text", None), ("que_quan", "Quê quán", "text", None),
    ("cho_o", "Chỗ ở", "text", None), ("chuc_danh", "Chức danh", "text", None),
    ("chuc_vu", "Chức vụ", "text", None), ("cap_bac", "Cấp bậc", "text", None),
    ("ngay_vao_nganh", "Ngày vào nghành", "date", None),
    ("hoc_van", "Học vấn / chứng chỉ", "text", None),
    ("trinh_do_llct", "Trình độ LLCT", "text", None),
    ("ma_bhxh", "Mã BHXH", "text", None),
]
DOC = [
    ("nv", "Nhân viên *", "emp", None),
    ("loai", "Loại giấy tờ *", "choice", ["Đơn xin việc", "Sơ yếu lý lịch", "CCCD", "Bằng cấp",
        "Giấy khám sức khỏe", "Xác nhận cư trú", "Quyết định bổ nhiệm/điều chuyển", "Sổ BHXH", "Khác"]),
    ("so", "Số công văn", "text", None), ("van_ban_den", "Văn bản đến", "date", None),
    ("ngay_trien_khai", "Hạn thực hiện", "date", None),
    ("nguoi_ky", "Người ký", "text", None), ("ban_thuc_hien", "Ban thực hiện", "text", None),
    ("tep", "Tệp scan", "file", None),
    ("noi_gui", "Nơi gửi", "text", None), ("noi_nhan", "Nơi nhận", "text", None), ("ghi_chu", "Ghi chú", "text", None),
]
CON = [
    ("nv", "Nhân viên *", "emp", None),
    ("loai", "Loại hợp đồng *", "choice", ["Thử việc", "Xác định thời hạn", "Không xác định thời hạn", "Phụ lục"]),
    ("so", "Số hợp đồng", "text", None), ("tu_ngay", "Từ ngày", "date", None),
    ("den_ngay", "Đến ngày", "date", None), ("luong", "Lương cơ bản (VNĐ)", "text", None),
    ("phu_cap", "Phụ cấp", "text", None), ("tep", "Tệp hợp đồng", "file", None),
]
LEAVE = [
    ("nv", "Nhân viên *", "emp", None),
    ("loai", "Loại *", "choice", ["Phép năm", "Nghỉ ốm", "Việc riêng", "Không lương","Đi công tác"]),
    ("tu_ngay", "Từ ngày", "date", None), ("den_ngay", "Đến ngày", "date", None),
    ("ly_do", "Lý do", "text", None),
    ("duyet", "Trạng thái duyệt", "choice", ["Chờ duyệt", "Đã duyệt", "Từ chối"]),
]
ATT = [
    ("nv", "Nhân viên *", "emp", None),
    ("thang", "Tháng *", "text", None),
    ("xep_loai", "Xếp loại", "choice", ["Hoàn thành xuất sắc nhiệm vụ", "Hoàn thành tốt nhiệm vụ", "Hoàn thành nhiệm vụ", "Chưa hoàn thành nhiệm vụ"]),
]
TABLES = {"nhan_vien": EMP, "giay_to": DOC, "hop_dong": CON, "nghi_phep": LEAVE, "phan_loai_thang": ATT}

# Migration: rename columns in nhan_vien table
try:
    cursor = db.execute("PRAGMA table_info(nhan_vien)")
    cols = [row[1] for row in cursor.fetchall()]
    if "ma" in cols:  # Old schema detected
        # Rename columns
        db.execute("ALTER TABLE nhan_vien RENAME COLUMN ma TO so_hieu")
        db.execute("ALTER TABLE nhan_vien RENAME COLUMN dia_chi TO que_quan")
        db.execute("ALTER TABLE nhan_vien RENAME COLUMN ngay_vao TO ngay_vao_nganh")
        # Add new columns
        db.execute("ALTER TABLE nhan_vien ADD COLUMN cho_o TEXT")
        db.execute("ALTER TABLE nhan_vien ADD COLUMN chuc_vu TEXT")
        db.execute("ALTER TABLE nhan_vien ADD COLUMN cap_bac TEXT")
        db.execute("ALTER TABLE nhan_vien ADD COLUMN trinh_do_llct TEXT")
        db.execute("ALTER TABLE nhan_vien ADD COLUMN ma_bhxh TEXT")
        # Drop old columns by recreating table
        db.execute("""CREATE TABLE nhan_vien_new (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      so_hieu TEXT, ho_ten TEXT, ngay_sinh TEXT, gioi_tinh TEXT, cccd TEXT,
                      sdt TEXT, email TEXT, que_quan TEXT, cho_o TEXT, chuc_danh TEXT,
                      chuc_vu TEXT, cap_bac TEXT, ngay_vao_nganh TEXT, hoc_van TEXT,
                      trinh_do_llct TEXT, ma_bhxh TEXT)""")
        db.execute("""INSERT INTO nhan_vien_new (id, so_hieu, ho_ten, ngay_sinh, gioi_tinh,
                      cccd, sdt, email, que_quan, chuc_danh, ngay_vao_nganh, hoc_van)
                      SELECT id, so_hieu, ho_ten, ngay_sinh, gioi_tinh, cccd, sdt, email,
                      que_quan, chuc_danh, ngay_vao_nganh, hoc_van FROM nhan_vien""")
        db.execute("DROP TABLE nhan_vien")
        db.execute("ALTER TABLE nhan_vien_new RENAME TO nhan_vien")
        db.commit()
except sqlite3.OperationalError:
    pass

for t, f in TABLES.items():
    db.execute(f"CREATE TABLE IF NOT EXISTS {t} (id INTEGER PRIMARY KEY AUTOINCREMENT, "
               + ", ".join(k for k, *_ in f) + ")")
# Bổ sung các trường công văn cho cơ sở dữ liệu đã tạo từ phiên bản trước.
for column in ("nguoi_ky", "ban_thuc_hien"):
    try:
        db.execute(f"ALTER TABLE giay_to ADD COLUMN {column} TEXT")
    except sqlite3.OperationalError:
        pass
db.commit()


def parse(s):
    try:
        return datetime.strptime(s.strip(), "%d/%m/%Y").date()
    except Exception:
        return None


def emp_map():
    return {str(i): f"{m} - {n}" for i, m, n in db.execute("SELECT id, so_hieu, ho_ten FROM nhan_vien")}


def open_file(path):
    full = os.path.join(BASE, "tailieu", path)
    if not path or not os.path.exists(full):
        return messagebox.showinfo("Tệp", "Chưa có tệp đính kèm.")
    if sys.platform.startswith("win"):
        os.startfile(full)
    else:
        subprocess.call(["open" if sys.platform == "darwin" else "xdg-open", full])


class Crud(ttk.Frame):
    def __init__(self, parent, table, fields, tree_cols, hint=""):
        super().__init__(parent, padding=8)
        self.t, self.f, self.sel = table, fields, None
        self.vars, self.widgets = {}, {}
        form = ttk.LabelFrame(self, text=hint or "Thông tin", padding=8)
        form.pack(fill="x")
        for n, (k, lab, kind, opt) in enumerate(fields):
            r, c = divmod(n, 3)
            ttk.Label(form, text=lab).grid(row=r, column=c * 3, sticky="e", padx=(8, 3), pady=3)
            v = tk.StringVar()
            self.vars[k] = v
            if kind in ("choice", "emp"):
                w = ttk.Combobox(form, textvariable=v, width=24, values=opt or [],
                                 state="readonly" if kind == "choice" else "normal")
            elif kind == "file":
                w = ttk.Entry(form, textvariable=v, width=24, state="readonly")
            else:
                w = ttk.Entry(form, textvariable=v, width=26)
            w.grid(row=r, column=c * 3 + 1, pady=3)
            if kind == "date":
                ttk.Label(form, text="dd/mm/yyyy", foreground="#888").grid(row=r, column=c * 3 + 2, sticky="w")
            if kind == "file":
                ttk.Button(form, text="Chọn…", width=6, command=lambda k=k: self.pick(k)).grid(row=r, column=c * 3 + 2)
            self.widgets[k] = w
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=6)
        for txt, cmd in [("Thêm mới", self.add), ("Lưu sửa", self.update), ("Xóa", self.delete),
                         ("Xóa nhiều", self.delete_selected), ("Xóa toàn bộ", self.delete_all),
                         ("Làm mới form", self.clear), ("Xuất CSV", self.export)]:
            ttk.Button(bar, text=txt, command=cmd).pack(side="left", padx=2)
        if any(f[2] == "file" for f in fields):
            ttk.Button(bar, text="Mở tệp", command=lambda: open_file(self.vars["tep"].get())).pack(side="left", padx=2)

        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", pady=3)
        ttk.Label(search_frame, text="Tìm:").pack(side="left", padx=(0, 3))
        self.q = tk.StringVar()
        self.q.trace_add("write", lambda *a: self.refresh())
        ttk.Entry(search_frame, textvariable=self.q, width=28).pack(side="left", padx=(0, 15))

        if self.t == "phan_loai_thang":
            ttk.Label(search_frame, text="Xếp loại:").pack(side="left", padx=(0, 3))
            self.rating_filter = tk.StringVar(value="Tất cả")
            self.rating_filter.trace_add("write", lambda *a: self.refresh())
            ttk.Combobox(
                search_frame,
                textvariable=self.rating_filter,
                values=["Tất cả"] + [value for value in ATT[2][3]],
                state="readonly",
                width=32,
            ).pack(side="left", padx=(0, 10))

        ttk.Label(search_frame, text="Từ ngày:").pack(side="left", padx=(0, 3))
        self.date_from = tk.StringVar()
        self.date_from.trace_add("write", lambda *a: self.refresh())
        ttk.Entry(search_frame, textvariable=self.date_from, width=12).pack(side="left")
        ttk.Label(search_frame, text="dd/mm/yyyy", foreground="#888").pack(side="left", padx=(2, 8))

        ttk.Label(search_frame, text="Đến ngày:").pack(side="left", padx=(0, 3))
        self.date_to = tk.StringVar()
        self.date_to.trace_add("write", lambda *a: self.refresh())
        ttk.Entry(search_frame, textvariable=self.date_to, width=12).pack(side="left")
        ttk.Label(search_frame, text="dd/mm/yyyy", foreground="#888").pack(side="left", padx=2)
        self.cols = tree_cols
        labels = {k: l.replace(" *", "") for k, l, *_ in fields}
        self.tree = ttk.Treeview(self, columns=tree_cols, show="tree headings", height=14, selectmode="extended")
        WIDTHS = {"tep": 70, "so": 80, "ma": 80, "so_hieu": 80, "loai": 150, "nv": 180,
          "noi_gui": 130, "noi_nhan": 130}
        self.tree.column("#0", width=30, stretch=False)
        for c in tree_cols:
            self.tree.heading(c, text=labels[c])
            self.tree.column(c, width=WIDTHS.get(c, 110), anchor="w", stretch=(c != "tep"))
        sb = ttk.Scrollbar(self, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.refresh()

    def pick(self, k):
        p = filedialog.askopenfilename()
        if p:
            name = f"{int(time.time())}_{os.path.basename(p)}"
            shutil.copy(p, os.path.join(BASE, "tailieu", name))
            self.vars[k].set(name)

    def values(self):
        d = {}
        for k, lab, kind, _ in self.f:
            v = self.vars[k].get().strip()
            if kind == "emp" and v:
                v = v.split(" - ")[0]
            d[k] = v
        return d

    def valid(self, d):
        for k, lab, kind, _ in self.f:
            if lab.endswith("*") and not d[k]:
                messagebox.showwarning("Thiếu thông tin", f"Vui lòng nhập: {lab.replace(' *', '')}")
                return False
            if kind == "date" and d[k] and not parse(d[k]):
                messagebox.showwarning("Sai ngày", f"{lab}: nhập theo dd/mm/yyyy")
                return False
        return True

    def add(self):
        d = self.values()
        if not self.valid(d):
            return
        db.execute(f"INSERT INTO {self.t} ({','.join(d)}) VALUES ({','.join('?' * len(d))})", list(d.values()))
        db.commit()
        self.clear()
        self.refresh()

    def update(self):
        if not self.sel:
            return messagebox.showinfo("Chọn dòng", "Chọn một dòng trong bảng để sửa.")
        d = self.values()
        if not self.valid(d):
            return
        db.execute(f"UPDATE {self.t} SET {','.join(k + '=?' for k in d)} WHERE id=?", list(d.values()) + [self.sel])
        db.commit()
        self.refresh()

    def delete(self):
        if self.sel and messagebox.askyesno("Xóa", "Xóa bản ghi đã chọn?"):
            db.execute(f"DELETE FROM {self.t} WHERE id=?", (self.sel,))
            db.commit()
            self.clear()
            self.refresh()

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return messagebox.showinfo("Chọn dòng", "Vui lòng chọn ít nhất một dòng để xóa.")
        if messagebox.askyesno("Xóa nhiều", f"Xóa {len(selected)} bản ghi đã chọn?"):
            for item_id in selected:
                db.execute(f"DELETE FROM {self.t} WHERE id=?", (int(item_id),))
            db.commit()
            self.clear()
            self.refresh()
            messagebox.showinfo("Hoàn tất", f"Đã xóa {len(selected)} bản ghi.")

    def delete_all(self):
        count = db.execute(f"SELECT COUNT(*) FROM {self.t}").fetchone()[0]
        if count == 0:
            return messagebox.showinfo("Trống", "Bảng không có dữ liệu.")
        if messagebox.askyesno("Cảnh báo", f"Xóa toàn bộ {count} bản ghi trong bảng?\nThao tác này KHÔNG THỂ hoàn tác!"):
            if messagebox.askyesno("Xác nhận lần 2", "Bạn chắc chắn muốn xóa TOÀN BỘ dữ liệu?"):
                db.execute(f"DELETE FROM {self.t}")
                db.commit()
                self.clear()
                self.refresh()
                messagebox.showinfo("Hoàn tất", f"Đã xóa toàn bộ {count} bản ghi.")

    def clear(self):
        self.sel = None
        for v in self.vars.values():
            v.set("")

    def on_select(self, _):
        s = self.tree.selection()
        if not s:
            return
        self.sel = int(s[0])
        row = db.execute(f"SELECT * FROM {self.t} WHERE id=?", (self.sel,)).fetchone()
        em = emp_map()
        for (k, _, kind, _), val in zip(self.f, row[1:]):
            self.vars[k].set(em.get(str(val), val) if kind == "emp" else (val or ""))

    def display(self, row):
        em, out = emp_map(), []
        names = [k for k, *_ in self.f]
        for c in self.cols:
            val = row[names.index(c) + 1]
            out.append(em.get(str(val), "") if c == "nv" else (val or ""))
        return out

    def refresh(self):
        for w in self.f:
            if w[2] == "emp":
                self.widgets[w[0]]["values"] = list(emp_map().values())
        self.tree.delete(*self.tree.get_children())
        q = self.q.get().lower()
        rating_filter = getattr(self, "rating_filter", None)
        rating_filter = rating_filter.get() if rating_filter else "Tất cả"
        date_from = parse(self.date_from.get())
        date_to = parse(self.date_to.get())
        date_fields = [k for k, _, kind, _ in self.f if kind == "date"]

        for row in db.execute(f"SELECT * FROM {self.t} ORDER BY id DESC"):
            vals = self.display(row)
            if q and q not in " ".join(map(str, vals)).lower():
                continue
            if rating_filter != "Tất cả" and row[[k for k, *_ in self.f].index("xep_loai") + 1] != rating_filter:
                continue

            if date_from or date_to:
                names = [k for k, *_ in self.f]
                match = False
                for date_field in date_fields:
                    date_val = parse(row[names.index(date_field) + 1] or "")
                    if date_val:
                        if date_from and date_val < date_from:
                            continue
                        if date_to and date_val > date_to:
                            continue
                        match = True
                        break
                if not match and (date_from or date_to):
                    continue

            self.tree.insert("", "end", iid=row[0], values=vals)

    def export(self):
        p = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if p:
            with open(p, "w", newline="", encoding="utf-8-sig") as fh:
                w = csv.writer(fh)
                w.writerow([l.replace(" *", "") for _, l, *_ in self.f])
                em = emp_map()
                for row in db.execute(f"SELECT * FROM {self.t}"):
                    w.writerow([em.get(str(v), v) if self.f[i][2] == "emp" else v for i, v in enumerate(row[1:])])
            messagebox.showinfo("Xuất CSV", "Đã xuất file (mở được bằng Excel).")


class CrudWithEmpInfo(Crud):
    """Extended Crud that shows employee info when employee is selected"""
    def __init__(self, parent, table, fields, tree_cols, hint=""):
        super().__init__(parent, table, fields, tree_cols, hint)
        # Add employee info display frame
        self.info_frame = ttk.LabelFrame(self, text="Thông tin nhân viên", padding=8)
        self.info_frame.pack(fill="x", pady=(0, 6))

        self.info_labels = {}
        info_fields = [("ho_ten", "Họ tên:"), ("chuc_danh", "Chức danh:"),
                       ("cap_bac", "Cấp bậc:"), ("chuc_vu", "Chức vụ:")]
        for idx, (key, label) in enumerate(info_fields):
            ttk.Label(self.info_frame, text=label).grid(row=0, column=idx*2, sticky="e", padx=(8, 3))
            lbl = ttk.Label(self.info_frame, text="", foreground="#0066cc", font=("", 9, "bold"))
            lbl.grid(row=0, column=idx*2+1, sticky="w", padx=(0, 15))
            self.info_labels[key] = lbl

        # Bind employee selection to update info
        if "nv" in self.vars:
            self.vars["nv"].trace_add("write", lambda *a: self.update_emp_info())

    def update_emp_info(self):
        nv_val = self.vars["nv"].get().strip()
        if nv_val and " - " in nv_val:
            emp_id = nv_val.split(" - ")[0]
            try:
                row = db.execute("SELECT ho_ten, chuc_danh, cap_bac, chuc_vu FROM nhan_vien WHERE so_hieu=?",
                                (emp_id,)).fetchone()
                if row:
                    self.info_labels["ho_ten"].config(text=row[0] or "")
                    self.info_labels["chuc_danh"].config(text=row[1] or "")
                    self.info_labels["cap_bac"].config(text=row[2] or "")
                    self.info_labels["chuc_vu"].config(text=row[3] or "")
                else:
                    self.clear_emp_info()
            except:
                self.clear_emp_info()
        else:
            self.clear_emp_info()

    def clear_emp_info(self):
        for lbl in self.info_labels.values():
            lbl.config(text="")

    def clear(self):
        super().clear()
        self.clear_emp_info()


class Alerts(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=8)
        top = ttk.Frame(self)
        top.pack(fill="x")
        ttk.Label(top, text="Công văn có hạn thực hiện trong").pack(side="left")
        self.days = tk.IntVar(value=60)
        ttk.Spinbox(top, from_=7, to=365, width=5, textvariable=self.days, command=self.refresh).pack(side="left", padx=4)
        ttk.Label(top, text="ngày tới").pack(side="left")
        ttk.Button(top, text="Làm mới", command=self.refresh).pack(side="left", padx=10)
        self.clock = ttk.Label(top, text="")
        self.clock.pack(side="right")
        cols = ("so", "han", "nguoi_ky", "ban_thuc_hien", "con")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=18)
        for c, t, w in zip(cols, ["Số công văn", "Hạn thực hiện", "Người ký", "Ban thực hiện", "Ghi chú"], [150, 130, 190, 240, 120]):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w)
        self.tree.tag_configure("over", foreground="#b00020")
        self.tree.tag_configure("today", foreground="#b00020", background="#ffe6e6")
        self.tree.tag_configure("soon", foreground="#b36b00")
        self.tree.pack(fill="both", expand=True, pady=6)
        self.refresh()
        self.refresh_clock()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        now_vn = datetime.now(timezone(timedelta(hours=7)))
        today_vn = now_vn.date()
        self.clock.config(text=f"Giờ Việt Nam: {now_vn:%d/%m/%Y %H:%M:%S}")
        lim = self.days.get()
        rows = []
        for so, han, nguoi_ky, ban_thuc_hien in db.execute(
                "SELECT so, ngay_trien_khai, nguoi_ky, ban_thuc_hien FROM giay_to"):
            due = parse(han or "")
            if due is None:
                continue
            left = (due - today_vn).days
            if left <= lim:
                rows.append((left, so or "", han or "", nguoi_ky or "", ban_thuc_hien or ""))
        # Số ngày còn lại là tiêu chí ưu tiên chính: càng gần hạn càng đứng đầu.
        for left, so, han, nguoi_ky, ban_thuc_hien in sorted(rows, key=lambda item: (item[0], item[2], item[1])):
            if left < 0:
                txt = f"Quá hạn {-left} ngày"
                tag = "over"
            elif left == 0:
                txt = "Đến hạn hôm nay"
                tag = "today"
            else:
                txt = f"Còn {left} ngày"
                tag = "soon"
            self.tree.insert("", "end", values=(so, han, nguoi_ky, ban_thuc_hien, txt), tags=(tag,))
    def refresh_clock(self):
        now_vn = datetime.now(timezone(timedelta(hours=7)))
        self.clock.config(text=f"Giờ Việt Nam: {now_vn:%d/%m/%Y %H:%M:%S}")
        self.after(1000, self.refresh_clock)


class Report(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=12)
        self.out = tk.Text(self, height=26, font=("Consolas", 11), relief="flat")
        self.out.pack(fill="both", expand=True)
        ttk.Button(self, text="Cập nhật báo cáo", command=self.refresh).pack(pady=6)
        self.refresh()

    def refresh(self):
        q = lambda s, *a: db.execute(s, a).fetchall()
        total = q("SELECT COUNT(*) FROM nhan_vien")[0][0]
        lines = [f"TỔNG NHÂN SỰ: {total}", ""]
        lines += ["Theo cấp bậc:"]
        lines += [f"  {t or '(trống)'}: {n}" for t, n in q("SELECT cap_bac, COUNT(*) FROM nhan_vien GROUP BY cap_bac")]
        lines += ["", "Theo chức vụ:"]
        lines += [f"  {t or '(trống)'}: {n}" for t, n in q("SELECT chuc_vu, COUNT(*) FROM nhan_vien GROUP BY chuc_vu")]
        lines += ["", "Theo giới tính:"]
        lines += [f"  {t or '(trống)'}: {n}" for t, n in q("SELECT gioi_tinh, COUNT(*) FROM nhan_vien GROUP BY gioi_tinh")]
        pend = q("SELECT COUNT(*) FROM nghi_phep WHERE duyet='Chờ duyệt'")[0][0]
        lines += ["", f"Đơn nghỉ phép chờ duyệt: {pend}"]
        try:
            luong = sum(float(x[0].replace(".", "").replace(",", "")) for x in q("SELECT luong FROM hop_dong") if x[0])
            lines += [f"Tổng lương cơ bản theo hợp đồng: {luong:,.0f} VNĐ"]
        except ValueError:
            lines += ["Tổng lương: (nhập lương dạng số để tính)"]
        self.out.config(state="normal")
        self.out.delete("1.0", "end")
        self.out.insert("end", "\n".join(lines))
        self.out.config(state="disabled")


def main():
    root = tk.Tk()
    root.title("Quản lý nhân sự & hồ sơ")
    root.geometry("1180x680")
    ttk.Style().theme_use("clam" if sys.platform.startswith("linux") else ttk.Style().theme_use())
    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True)
    tabs = [
        ("Nhân viên", Crud(nb, "nhan_vien", EMP, ["so_hieu", "ho_ten", "chuc_danh", "chuc_vu", "cap_bac", "sdt", "ngay_vao_nganh"], "Hồ sơ nhân viên")),
        ("Giấy tờ", Crud(nb, "giay_to", DOC, ["nv", "loai", "so", "van_ban_den", "ngay_trien_khai", "tep", "noi_gui", "noi_nhan"], "Giấy tờ nhân viên")),
        ("Hợp đồng", Crud(nb, "hop_dong", CON, ["nv", "loai", "so", "tu_ngay", "den_ngay", "luong"], "Hợp đồng lao động")),
        ("Nghỉ phép", Crud(nb, "nghi_phep", LEAVE, ["nv", "loai", "tu_ngay", "den_ngay", "duyet"], "Đơn nghỉ phép / tăng ca")),
        ("Phân loại tháng", CrudWithEmpInfo(nb, "phan_loai_thang", ATT, ["nv", "thang", "xep_loai"], "Phân loại tháng")),
        ("Cảnh báo hạn", Alerts(nb)),
        ("Cảnh báo hạn", Alerts(nb)),
        ("Báo cáo", Report(nb)),
    ]
    for name, tab in tabs:
        nb.add(tab, text=name)
    nb.bind("<<NotebookTabChanged>>", lambda e: [getattr(nb.nametowidget(nb.select()), "refresh", lambda: None)()])
    root.mainloop()


if __name__ == "__main__":
    main()