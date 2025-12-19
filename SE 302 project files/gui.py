import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import csv
import re
from datetime import datetime, timedelta

# PDF Export Imports
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

try:
    from tkcalendar import DateEntry
    HAS_CALENDAR = True
except ImportError:
    HAS_CALENDAR = False

from logic import ScheduleSystem

class ExamSchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Examtable Manager - Auto & Remove Only")
        self.root.geometry("1280x900")

        self.colors = {
            "primary": "#546e7a",
            "primary_light": "#78909c",
            "bg_main": "#eceff1",
            "bg_white": "#ffffff",
            "text_header": "#37474f",
            "text_body": "#455a64",
            "selection": "#cfd8dc",
            "accent_line": "#b0bec5",
            "success": "#27ae60",
            "danger": "#e74c3c"
        }

        self.root.configure(bg=self.colors["bg_main"])
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()

        self.system = ScheduleSystem()
        self.start_date = datetime.now().date()
        self.slot_times = []
        self.full_data = []

        # Öğrenci listesi takibi için gerekli değişkenler
        self.student_groups = {}
        self.student_list_sorted = []

        self.build_layout()
        try:
            self.root.after(500, self.monitor_fullscreen)
        except Exception:
            pass

    def configure_styles(self):
        self.style.configure("Treeview", background=self.colors["bg_white"],
                             fieldbackground=self.colors["bg_white"], foreground=self.colors["text_body"],
                             rowheight=35, font=('Segoe UI', 10))
        self.style.configure("Treeview.Heading", font=('Segoe UI', 10, 'bold'),
                             background=self.colors["primary"], foreground=self.colors["bg_white"], relief="flat")
        self.style.map("Treeview", background=[('selected', self.colors["primary_light"])],
                       foreground=[('selected', self.colors["bg_white"])])

        self.style.configure("Big.Accent.TButton", font=('Segoe UI', 10, 'bold'),
                             background=self.colors["primary"], foreground=self.colors["bg_white"], borderwidth=0)
        self.style.map("Big.Accent.TButton", background=[('active', self.colors["primary_light"])])

        self.style.configure("Danger.TButton", font=('Segoe UI', 9, 'bold'),
                             background=self.colors["danger"], foreground="white", borderwidth=0)

        self.style.configure("TButton", font=('Segoe UI', 9))
        self.style.configure("TNotebook", background=self.colors["bg_main"], borderwidth=0)
        self.style.configure("TNotebook.Tab", font=('Segoe UI', 10, 'bold'), padding=[20, 10],
                             background="#cfd8dc", foreground=self.colors["text_body"])
        self.style.map("TNotebook.Tab", background=[('selected', self.colors["primary"])],
                       foreground=[('selected', self.colors["bg_white"])])

    def build_layout(self):
        header_frame = tk.Frame(self.root, bg=self.colors["bg_white"], height=56)
        header_frame.pack(fill='x', side='top')
        tk.Frame(header_frame, bg=self.colors["accent_line"], height=2).pack(side='bottom', fill='x')

        title_holder = tk.Frame(header_frame, bg=self.colors["bg_white"])
        title_holder.pack(fill='both', expand=True)
        lbl_title = tk.Label(title_holder, text="EXAMTABLE MANAGER", font=('Segoe UI', 18, 'bold'),bg=self.colors["bg_white"], fg=self.colors["primary"])
        lbl_title.pack(side='left', padx=12, pady=10)

        help_btn = ttk.Button(title_holder, text="? Help", command=self.show_help)
        help_btn.pack(side='right', padx=12, pady=10)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=20)

        self.tab_config = tk.Frame(self.notebook, bg=self.colors["bg_white"])
        self.tab_schedule = tk.Frame(self.notebook, bg=self.colors["bg_white"])

        self.notebook.add(self.tab_config, text="SETTINGS & DATA")
        self.notebook.add(self.tab_schedule, text="SCHEDULE (RESULT)")

        self.build_config_tab()
        self.build_schedule_tab()

    def build_config_tab(self):
        bottom_area = tk.Frame(self.tab_config, bg=self.colors["bg_white"], pady=15)
        bottom_area.pack(side='bottom', fill='x')

        self.btn_start = ttk.Button(bottom_area, text="GENERATE SCHEDULE", style="Big.Accent.TButton", command=self.start_process)
        self.btn_start.pack(side='left', padx=8, ipadx=14, ipady=6)

        self.btn_stop = ttk.Button(bottom_area, text="STOP", command=self.stop_process, state='disabled')
        self.btn_stop.pack(side='left', padx=8, ipadx=8, ipady=6)

        self.lbl_log = tk.Label(self.tab_config, text="", bg=self.colors["bg_white"], fg=self.colors["primary"])
        self.lbl_log.pack(side='bottom', pady=(0, 5))

        container_canvas = tk.Canvas(self.tab_config, bg=self.colors["bg_white"], highlightthickness=0)
        container_frame = tk.Frame(container_canvas, bg=self.colors["bg_white"])

        scrollbar_y = ttk.Scrollbar(self.tab_config, orient="vertical", command=container_canvas.yview)

        canvas_window = container_canvas.create_window((0, 0), window=container_frame, anchor='nw')

        def _on_frame_configure(event):
            container_canvas.configure(scrollregion=container_canvas.bbox("all"))

        def _on_canvas_configure(event):
            container_canvas.itemconfig(canvas_window, width=event.width)

        container_frame.bind("<Configure>", _on_frame_configure)
        container_canvas.bind("<Configure>", _on_canvas_configure)

        container_canvas.pack(side='left', fill='both', expand=True, padx=40, pady=20)
        scrollbar_y.pack(side='right', fill='y')
        container_canvas.configure(yscrollcommand=scrollbar_y.set)

        lf_style = {"font": ('Segoe UI', 11, 'bold'), "bg": self.colors["bg_white"],
                    "fg": self.colors["primary"], "padx": 20, "pady": 15}

        columns_frame = tk.Frame(container_frame, bg=self.colors["bg_white"])
        columns_frame.pack(fill='both', expand=True)

        left_col = tk.Frame(columns_frame, bg=self.colors["bg_white"])
        left_col.pack(side='left', fill='both', expand=True, padx=(0, 10))

        right_col = tk.Frame(columns_frame, bg=self.colors["bg_white"], width=360)
        right_col.pack(side='right', fill='y', padx=(10, 0))

        frame_files = tk.LabelFrame(left_col, text="1. Data Files (CSV/TXT)", **lf_style)
        frame_files.pack(side='top', fill='x', pady=(0, 20), anchor='n')

        self.create_file_row(frame_files, "Classroom List:", self.imp_rooms)
        self.create_file_row(frame_files, "Course List:", self.imp_courses)
        self.create_file_row(frame_files, "Student List:", self.imp_students)

        sep = ttk.Separator(frame_files, orient="horizontal")
        sep.pack(fill="x", pady=10)
        db_frame = tk.Frame(frame_files, bg=self.colors["bg_white"])
        db_frame.pack(fill='x', pady=2)
        ttk.Button(db_frame, text="💾 Save to Database", command=self.save_to_db).pack(side='left', padx=5)
        ttk.Button(db_frame, text="📥 Load from Database", command=self.load_from_db).pack(side='left', padx=5)

        frame_time = tk.LabelFrame(left_col, text="2. Exam Calendar Settings", **lf_style)
        frame_time.pack(side='top', fill='both', expand=True, pady=(0, 10))

        row_date = tk.Frame(frame_time, bg=self.colors["bg_white"])
        row_date.pack(fill='x', pady=5)

        tk.Label(row_date, text="Start Date:", bg=self.colors["bg_white"], width=10, anchor='w').pack(side='left')
        if HAS_CALENDAR:
            self.ent_date = DateEntry(row_date, width=15, background=self.colors["primary"], foreground='white', date_pattern='yyyy-mm-dd')
            self.ent_date.pack(side='left', padx=(0, 20))
        else:
            self.ent_date = ttk.Entry(row_date, width=15)
            self.ent_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
            self.ent_date.pack(side='left', padx=(0, 20))

        tk.Label(row_date, text="Duration (Days):", bg=self.colors["bg_white"], width=12, anchor='w').pack(side='left')
        self.ent_days = ttk.Entry(row_date, width=5)
        self.ent_days.insert(0, "7")
        self.ent_days.pack(side='left')

        tk.Label(frame_time, text="Exam Slots Generator (Auto):", bg=self.colors["bg_white"], font=('Segoe UI', 9, 'bold'), anchor='w').pack(fill='x', pady=(15, 5))

        auto_frame = tk.Frame(frame_time, bg="#eceff1", pady=10, padx=10)
        auto_frame.pack(fill='x')

        tk.Label(auto_frame, text="Start (HH:MM):", bg="#eceff1").pack(side='left', padx=5)
        self.ent_start_hour = ttk.Entry(auto_frame, width=8)
        self.ent_start_hour.insert(0, "09:00")
        self.ent_start_hour.pack(side='left')

        tk.Label(auto_frame, text="End (HH:MM):", bg="#eceff1").pack(side='left', padx=(15, 5))
        self.ent_end_hour = ttk.Entry(auto_frame, width=8)
        self.ent_end_hour.insert(0, "17:00")
        self.ent_end_hour.pack(side='left')

        tk.Label(auto_frame, text="Slot Min:", bg="#eceff1").pack(side='left', padx=(15, 5))
        self.ent_duration_min = ttk.Entry(auto_frame, width=5)
        self.ent_duration_min.insert(0, "60")
        self.ent_duration_min.pack(side='left')

        ttk.Button(auto_frame, text="⚡ Generate Slots", command=self.generate_auto_slots).pack(side='left', padx=20)

        list_container = tk.Frame(frame_time, bg=self.colors["bg_white"])
        list_container.pack(fill='both', expand=True, pady=10)

        scrollbar = ttk.Scrollbar(list_container, orient="vertical")
        self.lst_slots = tk.Listbox(list_container, borderwidth=1, relief="solid",
                                    font=('Consolas', 11), yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.lst_slots.yview)

        scrollbar.pack(side='right', fill='y')
        self.lst_slots.pack(side='left', fill='both', expand=True)

        bottom_ctrl = tk.Frame(frame_time, bg=self.colors["bg_white"])
        bottom_ctrl.pack(fill='x', pady=5)

        ttk.Button(bottom_ctrl, text="Remove Selected (-)", style="Danger.TButton", command=self.remove_slot).pack(side='right')

        default_times = ["09:00-11:00", "11:00-13:00", "13:30-15:30", "15:30-17:30"]
        for t in default_times: self.lst_slots.insert(tk.END, t)

        log_frame = tk.LabelFrame(right_col, text="Activity Log", **lf_style)
        log_frame.pack(side='top', fill='both', expand=True, padx=(0, 0), pady=(0, 0))

        self.txt_log = tk.Text(log_frame, height=30, bg="#111111", fg="#e6e6e6",
                               font=('Consolas', 10), wrap='word', state='disabled', padx=8, pady=6)
        log_scroll = ttk.Scrollbar(log_frame, orient='vertical', command=self.txt_log.yview)
        self.txt_log['yscrollcommand'] = log_scroll.set
        log_scroll.pack(side='right', fill='y')
        self.txt_log.pack(side='left', fill='both', expand=True)

    def generate_auto_slots(self):
        try:
            start_str = self.ent_start_hour.get().strip()
            end_str = self.ent_end_hour.get().strip()
            duration_min = int(self.ent_duration_min.get().strip())

            start_time = datetime.strptime(start_str, "%H:%M")
            end_time = datetime.strptime(end_str, "%H:%M")

            self.lst_slots.delete(0, tk.END)
            current = start_time
            while True:
                nxt = current + timedelta(minutes=duration_min)
                if nxt > end_time: break
                slot_str = f"{current.strftime('%H:%M')}-{nxt.strftime('%H:%M')}"
                self.lst_slots.insert(tk.END, slot_str)
                current = nxt
            messagebox.showinfo("Auto Fill", "Slots generated successfully.")
            self.append_log(f"Auto slots generated ({len(self.lst_slots.get(0, tk.END))} slots)")
        except ValueError:
            messagebox.showerror("Error", "Check time format (HH:MM) and duration.")
            self.append_log("Auto slots generation failed: invalid input")

    def remove_slot(self):
        selection = self.lst_slots.curselection()
        if selection:
            val = self.lst_slots.get(selection[0])
            self.lst_slots.delete(selection[0])
            self.append_log(f"Removed slot: {val}")
        else:
            messagebox.showwarning("Warning", "Select a slot to remove.")
            self.append_log("Remove slot attempted without selection")

    def create_file_row(self, parent, label_text, command_func):
        f = tk.Frame(parent, bg=self.colors["bg_white"])
        f.pack(fill='x', pady=5)
        tk.Label(f, text=label_text, width=20, anchor='w', bg=self.colors["bg_white"]).pack(side='left')
        ttk.Button(f, text="Select File...", command=command_func).pack(side='left')
        lbl_status = tk.Label(f, text="Not Selected", fg="#95a5a6", bg=self.colors["bg_white"], font=('Segoe UI', 9, 'italic'))
        lbl_status.pack(side='left', padx=10)
        command_func.__func__.status_label = lbl_status

    def imp_rooms(self): self.load_file(self.imp_rooms, self.system.load_classrooms_regex)
    def imp_courses(self): self.load_file(self.imp_courses, self.system.load_courses_regex)
    def imp_students(self): self.load_file(self.imp_students, self.system.load_all_students_regex)

    def load_file(self, func_ref, system_method):
        path = filedialog.askopenfilename(filetypes=[("All Files", "*.*"), ("CSV", "*.csv"), ("TXT", "*.txt")])
        if path:
            msg = system_method(path)
            if hasattr(func_ref, 'status_label'):
                fname = path.split('/')[-1]
                if "SUCCESS" in msg or "BAŞARILI" in msg:
                    color, txt = "#27ae60", f"Loaded ({fname})"
                else:
                    color, txt = "#e74c3c", "Error / Empty"
                func_ref.status_label.config(text=txt, fg=color, font=('Segoe UI', 9, 'bold'))
            self.lbl_log.config(text=msg)
            try:
                fname = path.split('/')[-1]
            except:
                fname = path
            self.append_log(f"Import {fname}: {msg}")

    def save_to_db(self):
        try:
            self.system.save_data_to_db()
            messagebox.showinfo("Database", "Saved classrooms/courses/students to DB ✅")
            self.append_log("Data saved to Database.")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            self.append_log(f"DB Save Error: {str(e)}")

    def load_from_db(self):
        try:
            self.system.load_data_from_db()

            c_count = len(self.system.classrooms)
            crs_count = len(self.system.courses)
            st_count = len(self.system.all_students_list)

            if c_count == 0 or crs_count == 0:
                messagebox.showwarning(
                    "Database",
                    "Database loaded but no usable data found!"
                )
                self.append_log("DB Load: No data found.")
                return

            messagebox.showinfo(
                "Database",
                f"Loaded from DB ✅\n"
                f"Classrooms: {c_count}\n"
                f"Courses: {crs_count}\n"
                f"Students: {st_count}"
            )
            self.append_log(f"DB Loaded: {c_count} rooms, {crs_count} courses, {st_count} students.")

        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            self.append_log(f"DB Load Error: {str(e)}")

    def start_process(self):
        if not self.system.courses or not self.system.classrooms:
            return messagebox.showerror("Missing Data", "Please upload required files.")
        try:
            self.append_log("Schedule generation requested by user")
            if HAS_CALENDAR: self.start_date = self.ent_date.get_date()
            else: self.start_date = datetime.strptime(self.ent_date.get(), "%Y-%m-%d").date()

            raw_slots = list(self.lst_slots.get(0, tk.END))
            if not raw_slots: return messagebox.showerror("Error", "Add at least one time slot.")

            def parse_slot(s):
                start_time_str = s.split('-')[0].strip()
                return datetime.strptime(start_time_str, "%H:%M")

            self.slot_times = sorted(raw_slots, key=parse_slot)

            try:
                days_val = int(self.ent_days.get())
            except:
                days_val = 7

            self.system.num_days = days_val
            self.system.slots_per_day = len(self.slot_times)

            self.lbl_log.config(text="Calculating...")
            self.lbl_log.config(text="Process running...")
            self.btn_start.config(state='disabled')
            self.btn_stop.config(state='normal')
            threading.Thread(target=self.run_logic, daemon=True).start()
        except Exception as e: messagebox.showerror("Error", str(e))

    def stop_process(self):
        self.system.stop_event.set()
        self.lbl_log.config(text="Stopping...")
        self.lbl_log.config(fg="red")
        self.append_log("Stop requested by user")

    def run_logic(self):
        success, msg = self.system.solve()
        self.root.after(0, lambda: self.finish_solver(success, msg))

    def finish_solver(self, success, msg):
        self.lbl_log.config(text=msg)
        self.btn_start.config(state='normal')
        self.btn_stop.config(state='disabled')

        if success:
            messagebox.showinfo("Success", msg)
            self.notebook.select(self.tab_schedule)
            self.refresh_table()
            self.append_log(f"Schedule generation finished: SUCCESS - {msg}")

        else:
            if "timeout" in msg.lower():
                messagebox.showwarning(
                    "Timeout",
                    "⏱️ Schedule generation stopped.\nTime limit (10 seconds) exceeded."
                )

            elif "stopped" in msg.lower() or "durdur" in msg.lower():
                messagebox.showwarning("Cancelled", "⛔ Process stopped by user.")
                self.append_log(f"Schedule generation stopped by user: {msg}")

            else:
                messagebox.showerror("Failed", msg)
                self.append_log(f"Schedule generation failed: {msg}")

    def build_schedule_tab(self):
        top_bar = tk.Frame(self.tab_schedule, bg=self.colors["bg_white"], pady=10)
        top_bar.pack(fill='x', padx=20)
        tk.Label(top_bar, text="View:", bg=self.colors["bg_white"], font=('Segoe UI', 10, 'bold')).pack(side='left')
        self.view_var = tk.StringVar(value="Daily Plan")
        cb = ttk.Combobox(top_bar, textvariable=self.view_var,
                          values=["General Schedule", "Daily Plan", "Student Based", "Classroom Based"],
                          state='readonly', width=20)
        cb.pack(side='left', padx=10)
        cb.bind("<<ComboboxSelected>>", self.refresh_table)

        ttk.Button(top_bar, text="Export CSV", command=self.export_to_csv).pack(side='right')
        ttk.Button(top_bar, text="Export PDF", command=self.export_to_pdf).pack(side='right', padx=(10, 0))

        tree_outer = tk.Frame(self.tab_schedule, bg=self.colors["bg_white"])
        tree_outer.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        tree_outer.grid_rowconfigure(0, weight=1)
        tree_outer.grid_columnconfigure(0, weight=1)
        tree_outer.grid_columnconfigure(1, weight=3)
        tree_outer.grid_columnconfigure(2, weight=1)

        center_frame = tk.Frame(tree_outer, bg=self.colors["bg_white"] )
        center_frame.grid(row=0, column=1, sticky='nsew')

        scrolly = ttk.Scrollbar(center_frame, orient="vertical")
        scrollx = ttk.Scrollbar(center_frame, orient="horizontal")
        self.tree = ttk.Treeview(center_frame, show='headings', yscrollcommand=scrolly.set, xscrollcommand=scrollx.set)
        scrolly.config(command=self.tree.yview)
        scrollx.config(command=self.tree.xview)
        scrolly.pack(side="right", fill="y")
        scrollx.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="y")

        self.schedule_center = center_frame
        self.tree_scrolly = scrolly
        self.tree_scrollx = scrollx
        self.set_columns_daily()

    def get_real_datetime(self, d, s):
        date = self.start_date + timedelta(days=d)
        time = self.slot_times[s] if s < len(self.slot_times) else "??"
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return f"{date.strftime('%Y-%m-%d')} ({days[date.weekday()]}) {time}"

    def get_day_and_date(self, d):
        date = self.start_date + timedelta(days=d)
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return f"{date.strftime('%Y-%m-%d')} ({days[date.weekday()]})"

    def set_columns_general(self):
        cols = ["Course", "Time", "Count", "Classroom", "Capacity"]
        self.tree['columns'] = cols
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("Course", width=200, anchor='center')
        self.tree.column("Time", width=300)
        self.tree.column("Count", width=100, anchor='center')
        self.tree.column("Classroom", width=200)
        self.tree.column("Capacity", width=120, anchor='center')

    def set_columns_daily(self):
        cols = ["Day", "Time", "Course", "Classroom", "Students"]
        self.tree['columns'] = cols
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("Day", width=300, anchor='w')
        self.tree.column("Time", width=120, anchor='center')
        self.tree.column("Course", width=200, anchor='center')
        self.tree.column("Classroom", width=200, anchor='w')
        self.tree.column("Students", width=120, anchor='center')

    def set_columns_student(self):
        cols = ["Student", "Course", "Time", "Classroom"]
        self.tree['columns'] = cols
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("Student", width=200, anchor='center')
        self.tree.column("Course", width=200, anchor='center')
        self.tree.column("Time", width=300, anchor='w')
        self.tree.column("Classroom", width=120, anchor='center')

    def set_columns_classroom(self):
        cols = ["Classroom", "Time", "Course", "Status"]
        self.tree['columns'] = cols
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("Classroom", width=150, anchor='center')
        self.tree.column("Time", width=300, anchor='w')
        self.tree.column("Course", width=200, anchor='center')
        self.tree.column("Status", width=120, anchor='center')

    def refresh_table(self, event=None):
        mode = self.view_var.get()
        # Clean up any per-view widgets from previous view
        for attr in ('student_frame', 'student_search_frame', 'day_frame', 'day_search_frame',
                     'student_calendar_frame', 'student_list_tree', 'student_container'):
            if hasattr(self, attr):
                setattr(self, attr, None)

        # Clear schedule_center frame children for all views
        try:
            for widget in list(self.schedule_center.winfo_children()):
                if widget not in (self.tree, self.tree_scrolly, self.tree_scrollx):
                    widget.destroy()
        except Exception:
            pass

        # Ensure tree is visible by default
        if hasattr(self, 'tree') and not self.tree.winfo_ismapped():
            try:
                self.tree_scrolly.pack(side="right", fill="y")
                self.tree_scrollx.pack(side="bottom", fill="x")
                self.tree.pack(side="left", fill="both", expand=True)
            except Exception:
                pass

        for i in self.tree.get_children(): self.tree.delete(i)
        self.full_data = []

        if mode == "General Schedule":
            self.set_columns_general()
            for c_code, (d, s, rooms) in self.system.assignments.items():
                c = next((x for x in self.system.courses if x.code == c_code), None)
                st_cnt = len(c.students) if c else 0
                r_names = ", ".join([r.code for r in rooms])
                cap = f"{st_cnt} / {sum(r.capacity for r in rooms)}"
                self.full_data.append((c_code, self.get_real_datetime(d,s), st_cnt, r_names, cap))

        elif mode == "Daily Plan":
            from collections import defaultdict
            day_groups = defaultdict(list)
            for c_code, (d, s, rooms) in self.system.assignments.items():
                date = (self.start_date + timedelta(days=d)).strftime('%Y-%m-%d')
                time_str = self.slot_times[s] if s < len(self.slot_times) else '??'
                c = next((x for x in self.system.courses if x.code == c_code), None)
                st_cnt = len(c.students) if c else 0
                r_names = ", ".join([r.code for r in rooms])
                day_groups[date].append((time_str, c_code, r_names, st_cnt))
            self.day_groups = {k: sorted(v, key=lambda x: x[0]) for k, v in day_groups.items()}

            try:
                self.tree.pack_forget()
                self.tree_scrolly.pack_forget()
                self.tree_scrollx.pack_forget()
            except Exception:
                pass

            self.day_search_frame = tk.Frame(self.schedule_center, bg=self.colors["bg_white"])
            self.day_search_frame.pack(fill='x', padx=6, pady=(6,4))
            tk.Label(self.day_search_frame, text="Select Date:", bg=self.colors["bg_white"]).pack(side='left')
            if HAS_CALENDAR:
                dp = DateEntry(self.day_search_frame, width=12, background=self.colors["primary"], foreground='white', date_pattern='yyyy-mm-dd')
            else:
                dp = ttk.Entry(self.day_search_frame, width=12)
                dp.insert(0, self.start_date.strftime('%Y-%m-%d'))
            dp.pack(side='left', padx=(6,4))
            def _do_pick(event=None):
                try:
                    sel = dp.get()
                except Exception:
                    sel = None
                if not sel:
                    messagebox.showwarning("Select Date", "Please choose a date.")
                    return
                if sel not in self.day_groups:
                    messagebox.showwarning("No Data", f"No schedule available for {sel}.")
                    return
                self._show_day_schedule(sel)
            pick_btn = ttk.Button(self.day_search_frame, text="Search", command=_do_pick)
            pick_btn.pack(side='left', padx=(4,0))
            if HAS_CALENDAR:
                dp.bind('<Return>', _do_pick)

            default_day = next(iter(self.day_groups.keys()), None)
            if default_day:
                try:
                    if HAS_CALENDAR:
                        dp.set_date(default_day)
                    else:
                        dp.delete(0, 'end'); dp.insert(0, default_day)
                except Exception:
                    pass
                self._show_day_schedule(default_day)
            else:
                self.day_frame = tk.Frame(self.schedule_center, bg=self.colors["bg_white"])
                self.day_frame.pack(fill='both', expand=True)
                lbl = tk.Label(self.day_frame, text="No schedule data available.", bg=self.colors["bg_white"], fg=self.colors["text_body"])
                lbl.pack(pady=20)

        elif mode == "Student Based":
            # --- START OF MODIFIED STUDENT BASED VIEW ---
            # Use Code 1's logic to build a split pane view
            temp_data = []
            for (sid, c_code), r_code in self.system.student_room_map.items():
                if c_code in self.system.assignments:
                    d, s, _ = self.system.assignments[c_code]
                    temp_data.append((sid, c_code, self.get_real_datetime(d, s), r_code))
            temp_data.sort(key=lambda x: (x[0], x[2]))
            self.full_data = temp_data

            try:
                self.tree.pack_forget()
                self.tree_scrolly.pack_forget()
                self.tree_scrollx.pack_forget()
            except Exception:
                pass

            from collections import defaultdict
            groups = defaultdict(list)
            for sid, c_code, time_str, r_code in temp_data:
                groups[sid].append((c_code, time_str, r_code))
            self.student_groups = groups

            # Count exams logic
            student_exam_counts = defaultdict(int)
            all_students_set = set()
            for (student_id, c_code), r_code in self.system.student_room_map.items():
                if c_code in self.system.assignments:
                    student_exam_counts[student_id] += 1
                    all_students_set.add(student_id)

            self.student_list_sorted = sorted(all_students_set)

            # Create two-column layout
            self.student_container = tk.Frame(self.schedule_center, bg=self.colors["bg_white"])
            self.student_container.pack(fill='both', expand=True, padx=6, pady=6)

            # Left column: Student list table
            left_student_frame = tk.Frame(self.student_container, bg=self.colors["bg_white"], width=350)
            left_student_frame.pack(side='left', fill='both', padx=(0, 10))

            tk.Label(left_student_frame, text="Students", bg=self.colors["bg_white"],
                     font=('Segoe UI', 11, 'bold'), fg=self.colors["primary"]).pack(anchor='w', pady=(0, 5))

            student_list_frame = tk.Frame(left_student_frame, bg=self.colors["bg_white"])
            student_list_frame.pack(fill='both', expand=True)

            student_scroll = ttk.Scrollbar(student_list_frame, orient="vertical")
            self.student_list_tree = ttk.Treeview(student_list_frame, columns=("Student ID", "Exams"),
                                                  show='headings', height=20, yscrollcommand=student_scroll.set)
            student_scroll.config(command=self.student_list_tree.yview)

            self.student_list_tree.heading("Student ID", text="Student ID")
            self.student_list_tree.heading("Exams", text="Exams")
            self.student_list_tree.column("Student ID", width=200)
            self.student_list_tree.column("Exams", width=100, anchor='center')

            student_scroll.pack(side='right', fill='y')
            self.student_list_tree.pack(side='left', fill='both', expand=True)

            # Populate student list
            for sid in self.student_list_sorted:
                exam_count = student_exam_counts.get(sid, 0)
                self.student_list_tree.insert('', 'end', values=(sid, exam_count), tags=(sid,))

            # Right column: Calendar view for selected student
            self.student_calendar_frame = tk.Frame(self.student_container, bg=self.colors["bg_white"])
            self.student_calendar_frame.pack(side='right', fill='both', expand=True)

            # Bind click event
            def on_student_select(event):
                selection = self.student_list_tree.selection()
                if selection:
                    item = self.student_list_tree.item(selection[0])
                    sid = item['values'][0]
                    self._show_student_calendar(sid)

            self.student_list_tree.bind('<ButtonRelease-1>', on_student_select)

            # Show first student by default
            default_sid = self.student_list_sorted[0] if self.student_list_sorted else None
            if default_sid:
                self.student_list_tree.selection_set(self.student_list_tree.get_children()[0])
                self._show_student_calendar(default_sid)
            else:
                lbl = tk.Label(self.student_calendar_frame, text="No student assignments available.",
                               bg=self.colors["bg_white"], fg=self.colors["text_body"])
                lbl.pack(pady=20)
            # --- END OF MODIFIED STUDENT BASED VIEW ---

        elif mode == "Classroom Based":
            self.set_columns_classroom()
            for c_code, (d, s, rooms) in self.system.assignments.items():
                for r in rooms:
                    self.full_data.append((r.code, self.get_real_datetime(d,s), c_code, "OCCUPIED"))
            self.full_data.sort()

        # Insert data to tree for General/Classroom views
        if mode in ["General Schedule", "Classroom Based"]:
            for row in self.full_data: self.tree.insert('', 'end', values=row)

    def _show_student_calendar(self, sid):
        """Display a single student's schedule in weekly grid calendar format."""
        # remove previous calendar widgets if present
        try:
            for widget in self.student_calendar_frame.winfo_children():
                widget.destroy()
        except Exception:
            pass

        # Get student's exams - organize by day and slot
        from collections import defaultdict
        exams_grid = defaultdict(dict)  # {day_index: {slot_index: (course, room)}}

        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        # Count exams to verify
        exam_count = 0

        for (student_id, c_code), r_code in self.system.student_room_map.items():
            if student_id != sid:
                continue
            if c_code not in self.system.assignments:
                continue

            d, s, _ = self.system.assignments[c_code]
            exam_date = self.start_date + timedelta(days=d)
            day_index = exam_date.weekday()  # 0=Monday, 6=Sunday

            # Store exam in grid
            exams_grid[day_index][s] = (c_code, r_code)
            exam_count += 1

        # Header with exam count
        hdr = tk.Frame(self.student_calendar_frame, bg=self.colors["primary"], height=60)
        hdr.pack(fill='x', padx=5, pady=(0, 15))
        lbl = tk.Label(hdr, text=f"{sid} - {exam_count} exam(s)", bg=self.colors["primary"],
                       fg="white", font=('Segoe UI', 16, 'bold'))
        lbl.pack(expand=True)

        if not exams_grid:
            no_data_lbl = tk.Label(self.student_calendar_frame,
                                   text="No exams scheduled for this student.",
                                   bg=self.colors["bg_white"], fg=self.colors["text_body"],
                                   font=('Segoe UI', 12))
            no_data_lbl.pack(pady=40)
            return

        # Create scrollable calendar grid
        scroll_frame = tk.Frame(self.student_calendar_frame, bg=self.colors["bg_white"])
        scroll_frame.pack(fill='both', expand=True, padx=5, pady=5)

        canvas = tk.Canvas(scroll_frame, bg=self.colors["bg_white"], highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(scroll_frame, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        grid_frame = tk.Frame(canvas, bg=self.colors["bg_white"])
        canvas_window = canvas.create_window((0, 0), window=grid_frame, anchor='nw')

        def configure_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            bbox = canvas.bbox("all")
            if bbox:
                grid_width = bbox[2] - bbox[0]
                canvas_width = canvas.winfo_width()
                if grid_width > canvas_width and canvas_width > 1:
                    scrollbar_x.pack(side='bottom', fill='x', before=canvas)
                else:
                    scrollbar_x.pack_forget()

        grid_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind("<Configure>", lambda e: configure_scroll_region())

        if not self.slot_times:
            no_slots_lbl = tk.Label(grid_frame,
                                    text="No time slots defined. Please configure time slots first.",
                                    bg=self.colors["bg_white"], fg=self.colors["danger"])
            no_slots_lbl.pack(pady=20)
        else:
            header_row = tk.Frame(grid_frame, bg=self.colors["primary"])
            header_row.pack(fill='x')

            tk.Label(header_row, text="Time", bg=self.colors["primary"], fg="white",
                     font=('Segoe UI', 9, 'bold'), width=12, anchor='w', padx=5, pady=6).pack(side='left')

            day_short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            for day_idx in range(7):
                day_name = day_short[day_idx]
                cell = tk.Label(header_row, text=day_name, bg=self.colors["primary"], fg="white",
                                font=('Segoe UI', 9, 'bold'), width=10, anchor='center',
                                padx=2, pady=6)
                cell.pack(side='left', fill='x', expand=True)

            for slot_idx, time_str in enumerate(self.slot_times):
                row_frame = tk.Frame(grid_frame, bg=self.colors["bg_white"], relief='solid', borderwidth=1)
                row_frame.pack(fill='x')

                time_lbl = tk.Label(row_frame, text=time_str, bg=self.colors["bg_white"],
                                    font=('Segoe UI', 9), width=12, anchor='w', padx=5, pady=6)
                time_lbl.pack(side='left')

                for day_idx in range(7):
                    cell_frame = tk.Frame(row_frame, bg=self.colors["bg_white"],
                                          relief='solid', borderwidth=1, width=100, height=35)
                    cell_frame.pack(side='left', fill='both', expand=True)
                    cell_frame.pack_propagate(False)

                    if day_idx in exams_grid and slot_idx in exams_grid[day_idx]:
                        course_code, room_code = exams_grid[day_idx][slot_idx]
                        exam_text = f"{course_code}\n{room_code}"
                        cell_lbl = tk.Label(cell_frame, text=exam_text, bg="#e3f2fd",
                                            font=('Segoe UI', 7, 'bold'), fg=self.colors["text_header"],
                                            justify='center', wraplength=90)
                        cell_lbl.pack(expand=True, fill='both')
                    else:
                        tk.Label(cell_frame, text="", bg=self.colors["bg_white"]).pack(expand=True, fill='both')

        scrollbar_y.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

    def _show_day_schedule(self, date_str):
        """Display a single day's schedule in the center area."""
        try:
            if hasattr(self, 'day_frame') and self.day_frame:
                self.day_frame.destroy()
        except Exception:
            pass

        self.day_frame = tk.Frame(self.schedule_center, bg=self.colors["bg_white"])
        self.day_frame.pack(fill='both', expand=False, padx=6, pady=6)

        hdr = tk.Frame(self.day_frame, bg="#cfd8dc")
        hdr.pack(fill='x', padx=5, pady=(6,0))
        lbl = tk.Label(hdr, text=f"Date: {date_str}", bg="#cfd8dc", fg=self.colors["text_header"], font=('Segoe UI', 12, 'bold'))
        lbl.pack(side='left', padx=6, pady=6)

        rows = self.day_groups.get(date_str, [])
        cols = ["Time", "Course", "Classroom", "Students"]
        tbl_frame = tk.Frame(self.day_frame, bg=self.colors["bg_white"])
        tbl_frame.pack(fill='both', expand=False, padx=10, pady=8)

        tbl_height = max(1, min(len(rows), 40))
        tbl = ttk.Treeview(tbl_frame, columns=cols, show='headings', height=tbl_height)
        for c in cols:
            tbl.heading(c, text=c)
        tbl.column("Time", width=140, anchor='center')
        tbl.column("Course", width=300, anchor='center')
        tbl.column("Classroom", width=160, anchor='center')
        tbl.column("Students", width=140, anchor='center')

        for time_str, c_code, r_names, st_cnt in rows:
            tbl.insert('', 'end', values=(time_str, c_code, r_names, st_cnt))

        tbl.pack(anchor='n')
        try:
            tbl.yview_moveto(0)
        except Exception:
            pass

    def export_to_csv(self):
        view_name = self.view_var.get()

        if view_name == "Daily Plan":
            if not hasattr(self, 'day_groups') or not self.day_groups:
                return messagebox.showwarning("Warning", "No data to export.")

            export_choice = messagebox.askyesnocancel("Export Options",
                                                      "Export current day (Yes) or all days (No)?")
            if export_choice is None:
                return

            if export_choice:
                current_date = None
                if hasattr(self, 'day_search_frame'):
                    for widget in self.day_search_frame.winfo_children():
                        if isinstance(widget, tk.Entry):
                            current_date = widget.get()
                            break
                        elif hasattr(widget, 'get'):
                            try:
                                current_date = widget.get()
                                if current_date:
                                    break
                            except:
                                pass

                if not current_date:
                    current_date = next(iter(self.day_groups.keys()), None)

                if not current_date or current_date not in self.day_groups:
                    return messagebox.showwarning("Warning", "No current day selected.")

                default_name = f"Schedule_Daily_{current_date}.csv"
                path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default_name, filetypes=[("CSV Files", "*.csv")])
                if not path:
                    return

                try:
                    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                        writer = csv.writer(f, delimiter=';')
                        cols = ["Time", "Course", "Classroom", "Students"]
                        writer.writerow(cols)
                        rows = self.day_groups.get(current_date, [])
                        for time_str, c_code, r_names, st_cnt in rows:
                            writer.writerow([time_str, c_code, r_names, st_cnt])
                    messagebox.showinfo("Success", f"Daily schedule exported: {current_date}")
                    self.append_log(f"Exported CSV for {current_date}: {path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Export failed:\n{str(e)}")
                    self.append_log(f"Export failed: {str(e)}")
            else:
                default_name = f"Schedule_AllDays.csv"
                path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default_name, filetypes=[("CSV Files", "*.csv")])
                if not path:
                    return

                try:
                    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                        writer = csv.writer(f, delimiter=';')
                        cols = ["Date", "Time", "Course", "Classroom", "Students"]
                        writer.writerow(cols)
                        for date_str in sorted(self.day_groups.keys()):
                            rows = self.day_groups[date_str]
                            for time_str, c_code, r_names, st_cnt in rows:
                                writer.writerow([date_str, time_str, c_code, r_names, st_cnt])
                    messagebox.showinfo("Success", f"All daily schedules exported!")
                    self.append_log(f"Exported CSV for all days: {path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Export failed:\n{str(e)}")
                    self.append_log(f"Export failed: {str(e)}")
            return

        if not self.full_data and not self.student_groups: return messagebox.showwarning("Warning", "No data to export.")

        if view_name == "Student Based":
            only_one = messagebox.askyesno("Export Options", "Export only the currently shown student (Yes) or all students (No)?")
            if only_one:
                sid = None
                # Check selection in the list tree
                if hasattr(self, 'student_list_tree') and self.student_list_tree:
                    selection = self.student_list_tree.selection()
                    if selection:
                        item = self.student_list_tree.item(selection[0])
                        sid = item['values'][0]

                # Fallback to first available if nothing selected
                if not sid and hasattr(self, 'student_list_sorted') and self.student_list_sorted:
                    sid = self.student_list_sorted[0]

                if not sid:
                    return messagebox.showwarning("Warning", "No student selected to export.")

                default_name = f"Schedule_Student_{sid}.csv"
                path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default_name, filetypes=[("CSV Files", "*.csv")])
                if not path:
                    return
                try:
                    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                        writer = csv.writer(f, delimiter=';')
                        cols = ["Course", "Date", "Time", "Classroom"]
                        writer.writerow(cols)
                        groups = getattr(self, 'student_groups', {})
                        for c_code, time_str, r_code in groups.get(sid, []):
                            parts = time_str.split()
                            date_part = parts[0] if parts else ""
                            time_part = parts[-1] if len(parts) > 1 else ""
                            writer.writerow([c_code, date_part, time_part, r_code])
                    messagebox.showinfo("Success", f"Student schedule exported: {sid}")
                    self.append_log(f"Exported CSV for student {sid}: {path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Export failed:\n{str(e)}")
                    self.append_log(f"Export failed: {str(e)}")
                return

        view_name_fname = view_name.replace(" ", "_")
        default_name = f"Schedule_{view_name_fname}.csv"
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default_name, filetypes=[("CSV Files", "*.csv")])
        if not path:
            return
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                try:
                    cols = list(self.tree['columns'])
                    writer.writerow(cols)
                    writer.writerows(self.full_data)
                except Exception:
                    writer.writerows(self.full_data)
            messagebox.showinfo("Success", f"Data exported successfully!\nPlan: {self.view_var.get()}")
            self.append_log(f"Exported CSV: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed:\n{str(e)}")
            self.append_log(f"Export failed: {str(e)}")

    def export_to_pdf(self):
        if not self.full_data and self.view_var.get() != "Daily Plan" and self.view_var.get() != "Student Based":
            return messagebox.showwarning("Warning", "No data to export.")

        view_name = self.view_var.get().replace(" ", "_")
        default_name = f"Schedule_{view_name}.pdf"

        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF Files", "*.pdf")]
        )
        if not path:
            return

        try:
            doc = SimpleDocTemplate(
                path,
                pagesize=landscape(A4),
                leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24
            )

            if self.view_var.get() == "Daily Plan":
                if not hasattr(self, 'day_groups') or not self.day_groups:
                    return messagebox.showwarning("Warning", "No data to export.")
                cols = ["Date", "Time", "Course", "Classroom", "Students"]
                data_rows = []
                for date_str in sorted(self.day_groups.keys()):
                    for row in self.day_groups[date_str]:
                        data_rows.append([date_str] + list(row))
                headers = cols
                table_data = [headers] + data_rows
            elif self.view_var.get() == "Student Based":
                headers = ["Student", "Course", "Date/Time", "Classroom"]
                table_data = [headers] + [list(r) for r in self.full_data]
            else:
                headers = list(self.tree['columns'])
                table_data = [headers] + [list(r) for r in self.full_data]

            tbl = Table(table_data, repeatRows=1)
            tbl.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ]))

            doc.build([tbl])
            messagebox.showinfo("Success", f"PDF exported successfully!\nPlan: {self.view_var.get()}")
            self.append_log(f"Exported PDF: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"PDF export failed:\n{str(e)}")
            self.append_log(f"PDF Export failed: {str(e)}")

    def show_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("Help - Examtable Manager")
        help_window.geometry("700x600")
        help_window.resizable(True, True)

        help_pages = {
            "index": {
                "title": "Help Menu",
                "content": "EXAMTABLE MANAGER - Help Topics\n\nClick on any topic below for detailed help:\n\n1. Uploading Data Files\n2. Setting Exam Calendar\n3. Generating Time Slots\n4. Creating Schedule\n5. Exporting Results",
                "links": [
                    ("Uploading Data Files", "upload"),
                    ("Setting Exam Calendar", "calendar"),
                    ("Generating Time Slots", "slots"),
                    ("Creating Schedule", "schedule"),
                    ("Exporting Results", "export")
                ]
            },
            "upload": {
                "title": "Uploading Data Files",
                "content": "UPLOADING DATA FILES\n\n1. Click 'Select File...' next to Classroom List\n2. Choose your CSV or TXT file\n3. Repeat for Course List and Student List\n4. Green status indicates successful upload\n\nFile Format:\n- Classroom List: classroom_code, capacity\n- Course List: course_code, student_count\n- Student List: student_id, course_code",
                "links": []
            },
            "calendar": {
                "title": "Setting Exam Calendar",
                "content": "SETTING EXAM CALENDAR\n\n1. Choose Start Date using the date picker\n2. Set Duration (number of days for exams)\n3. Click 'Generate Schedule' when ready\n\nTips:\n- Start Date: When your exams begin\n- Duration: Total number of days for all exams",
                "links": []
            },
            "slots": {
                "title": "Generating Time Slots",
                "content": "GENERATING TIME SLOTS\n\n1. Set Start Time (e.g., 09:00)\n2. Set End Time (e.g., 17:00)\n3. Set Slot Duration in minutes (e.g., 60)\n4. Click '⚡ Generate Slots'\n\nExample:\n- Start: 09:00\n- End: 17:00\n- Duration: 60 min\n- Result: 09:00-10:00, 10:00-11:00, etc.",
                "links": []
            },
            "schedule": {
                "title": "Creating Schedule",
                "content": "CREATING SCHEDULE\n\n1. Upload all required data files\n2. Configure calendar and time slots\n3. Click 'GENERATE SCHEDULE'\n\nThe system will automatically:\n- Assign courses to time slots\n- Allocate appropriate classrooms\n- Avoid scheduling conflicts\n- Respect classroom capacity\n\nView results in multiple formats after generation.",
                "links": []
            },
            "export": {
                "title": "Exporting Results",
                "content": "EXPORTING RESULTS\n\n1. Go to 'SCHEDULE (RESULT)' tab\n2. Select desired view format:\n   - General Schedule: Overview of all exams\n   - Daily Plan: Organized by day\n   - Student Based: View by student\n   - Classroom Based: View by classroom\n3. Click 'Export CSV' or 'Export PDF'\n4. Choose location to save",
                "links": []
            }
        }

        current_page = {"page": "index"}

        title_label = tk.Label(help_window, text="Help Menu", font=('Segoe UI', 16, 'bold'),
                               bg=self.colors["bg_white"], fg=self.colors["primary"])
        title_label.pack(fill='x', padx=20, pady=15)

        content_frame = tk.Frame(help_window, bg=self.colors["bg_white"])
        content_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))

        scrollbar = ttk.Scrollbar(content_frame)
        scrollbar.pack(side='right', fill='y')

        help_text = tk.Text(content_frame, wrap='word', font=('Segoe UI', 10),
                            bg=self.colors["bg_white"], fg=self.colors["text_body"],
                            yscrollcommand=scrollbar.set, relief='flat', borderwidth=0, height=20)
        scrollbar.config(command=help_text.yview)
        help_text.pack(fill='both', expand=True)

        help_text.tag_configure("link", foreground="blue", underline=True)
        help_text.tag_bind("link", "<Enter>", lambda e: help_text.config(cursor="hand2"))
        help_text.tag_bind("link", "<Leave>", lambda e: help_text.config(cursor="arrow"))

        nav_frame = tk.Frame(help_window, bg=self.colors["bg_white"])
        nav_frame.pack(fill='x', padx=20, pady=10)

        btn_back = ttk.Button(nav_frame, text="← Back to Index")
        btn_back.pack(side='left', padx=5)

        close_btn = ttk.Button(nav_frame, text="Close", command=help_window.destroy)
        close_btn.pack(side='right', padx=5)

        def load_page(page_key):
            help_text.config(state='normal')
            help_text.delete('1.0', tk.END)

            page = help_pages.get(page_key, help_pages["index"])
            current_page["page"] = page_key

            title_label.config(text=page["title"])
            help_text.insert('end', page["content"] + "\n\n")

            if page["links"]:
                help_text.insert('end', "\n--- Related Topics ---\n\n")
                for link_text, link_page in page["links"]:
                    unique_tag = f"link_{link_page}"
                    help_text.tag_configure(unique_tag, foreground="blue", underline=True)
                    help_text.tag_bind(unique_tag, "<Enter>", lambda e: help_text.config(cursor="hand2"))
                    help_text.tag_bind(unique_tag, "<Leave>", lambda e: help_text.config(cursor="arrow"))
                    help_text.tag_bind(unique_tag, "<Button-1>", lambda e, lp=link_page: load_page(lp))
                    help_text.insert('end', f"• {link_text}\n", unique_tag)

            help_text.config(state='disabled')
            btn_back.config(state='normal' if page_key != "index" else 'disabled')

        btn_back.config(command=lambda: load_page("index"))
        load_page("index")

    def append_log(self, text):
        try:
            ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            entry = f"[{ts}] {text}\n"
            self.txt_log.config(state='normal')
            self.txt_log.insert('end', entry)
            self.txt_log.see('end')
            self.txt_log.config(state='disabled')
        except Exception:
            try:
                self.lbl_log.config(text=text)
            except Exception:
                pass