import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import csv
import re
import time
from datetime import datetime, timedelta

# PDF Export Imports (Code 2'den alındı)
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
        self.root.title("Examtable Manager")
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

        self.build_layout()
        # start watching fullscreen state to show/hide scrollbars
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

        # Slightly smaller accent button used for primary actions
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

        # help button
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
        # Bottom Action Area
        bottom_area = tk.Frame(self.tab_config, bg=self.colors["bg_white"], pady=15)
        bottom_area.pack(side='bottom', fill='x')

        self.btn_start = ttk.Button(bottom_area, text="GENERATE SCHEDULE", style="Big.Accent.TButton", command=self.start_process)
        self.btn_start.pack(side='left', padx=8, ipadx=14, ipady=6)

        self.btn_stop = ttk.Button(bottom_area, text="STOP", command=self.stop_process, state='disabled')
        self.btn_stop.pack(side='left', padx=8, ipadx=8, ipady=6)

        self.btn_find_min = ttk.Button(bottom_area, text="FIND MIN SLOTS", style="Big.Accent.TButton", command=self.find_minimum_slots)
        self.btn_find_min.pack(side='left', padx=8, ipadx=14, ipady=6)

        self.lbl_log = tk.Label(self.tab_config, text="", bg=self.colors["bg_white"], fg=self.colors["primary"])
        self.lbl_log.pack(side='bottom', pady=(0, 5))

        # --- SCROLLABLE SETTINGS AREA ---
        container_canvas = tk.Canvas(self.tab_config, bg=self.colors["bg_white"], highlightthickness=0)
        container_frame = tk.Frame(container_canvas, bg=self.colors["bg_white"])

        scrollbar_y = ttk.Scrollbar(self.tab_config, orient="vertical", command=container_canvas.yview)

        # Canvas Window Creation
        canvas_window = container_canvas.create_window((0, 0), window=container_frame, anchor='nw')

        def _on_frame_configure(event):
            # Update scrollregion to encompass the inner frame
            container_canvas.configure(scrollregion=container_canvas.bbox("all"))

        def _on_canvas_configure(event):
            # FULL SCREEN FIX: Force the inner frame to match the canvas width
            container_canvas.itemconfig(canvas_window, width=event.width)

        container_frame.bind("<Configure>", _on_frame_configure)
        container_canvas.bind("<Configure>", _on_canvas_configure)

        container_canvas.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar_y.pack(side='right', fill='y')
        container_canvas.configure(yscrollcommand=scrollbar_y.set)

        lf_style = {"font": ('Segoe UI', 10, 'bold'), "bg": self.colors["bg_white"],
                    "fg": "#546e7a", "padx": 15, "pady": 15}

        # Two-column layout
        columns_frame = tk.Frame(container_frame, bg=self.colors["bg_white"])
        # Removed extra padding to maximize space
        columns_frame.pack(fill='both', expand=True, pady=0)

        # Left Column: Settings (Give it weight)
        left_col = tk.Frame(columns_frame, bg=self.colors["bg_white"])
        left_col.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # Right Column: Logs (Give it weight)
        right_col = tk.Frame(columns_frame, bg=self.colors["bg_white"])
        right_col.pack(side='right', fill='both', expand=True, padx=(10, 0))

        # --- 1. Data Management (Files & Database) ---
        frame_files = tk.LabelFrame(left_col, text="1. Data Management (Files & Database)", **lf_style)
        frame_files.pack(side='top', fill='both', pady=(0, 5), anchor='n')

        # Split into Left (Files) and Right (DB Actions) - Use grid for better control or pack with expand
        files_inner = tk.Frame(frame_files, bg=self.colors["bg_white"])
        files_inner.pack(fill='both', expand=True)

        files_col = tk.Frame(files_inner, bg=self.colors["bg_white"])
        files_col.pack(side='left', fill='both', expand=True)
        
        # Vertical Separator
        ttk.Separator(files_inner, orient='vertical').pack(side='left', fill='y', padx=10, pady=5)
        
        db_col = tk.Frame(files_inner, bg=self.colors["bg_white"])
        db_col.pack(side='right', fill='both', padx=(0, 10), anchor='n')
        
        # Files Column (Anchor w to keep left aligned)
        self.create_file_row(files_col, "Classrooms & Caps:", self.imp_rooms)
        self.create_file_row(files_col, "Attendance Lists:", self.imp_attendance)
        self.create_file_row(files_col, "All Courses:", self.imp_courses)
        self.create_file_row(files_col, "All Students:", self.imp_students)

        # DB Column Actions
        tk.Label(db_col, text="Database Actions", bg=self.colors["bg_white"], fg="#90a4ae", font=('Segoe UI', 8, 'bold')).pack(pady=(0,5))
        
        db_btn_frame = tk.Frame(db_col, bg=self.colors["bg_white"])
        db_btn_frame.pack(anchor='center')
        
        # 2x2 Grid for DB buttons - Fixed width and padding
        # Use ipadx inside button style if needed, or just rely on width
        btn_w = 11  # Increased from 9 to 11 to fit "Comp 1"
        pad_x = 5
        pad_y = 5
        
        ttk.Button(db_btn_frame, text="💾 Save 1", width=btn_w, command=lambda: self.save_to_db_slot(1)).grid(row=0, column=0, padx=pad_x, pady=pad_y)
        ttk.Button(db_btn_frame, text="📥 Load 1", width=btn_w, command=lambda: self.load_from_db_slot(1)).grid(row=0, column=1, padx=pad_x, pady=pad_y)
        ttk.Button(db_btn_frame, text="💾 Save 2", width=btn_w, command=lambda: self.save_to_db_slot(2)).grid(row=1, column=0, padx=pad_x, pady=pad_y)
        ttk.Button(db_btn_frame, text="📥 Load 2", width=btn_w, command=lambda: self.load_from_db_slot(2)).grid(row=1, column=1, padx=pad_x, pady=pad_y)
        
        ttk.Button(db_btn_frame, text="📌 Comp 1", width=btn_w, command=lambda: self.compare_with_save(1)).grid(row=2, column=0, padx=pad_x, pady=pad_y)
        ttk.Button(db_btn_frame, text="📌 Comp 2", width=btn_w, command=lambda: self.compare_with_save(2)).grid(row=2, column=1, padx=pad_x, pady=pad_y)


        # --- 2. Exam Calendar Settings ---
        frame_time = tk.LabelFrame(left_col, text="2. Exam Calendar Settings", **lf_style)
        frame_time.pack(side='top', fill='both', expand=True, pady=(0, 10))

        # Use Grid for frame_time to ensure footer stays at bottom
        frame_time.grid_columnconfigure(0, weight=1)
        frame_time.grid_rowconfigure(3, weight=1) # Listbox row gets all space

        # Date & Duration Row
        row_date = tk.Frame(frame_time, bg=self.colors["bg_white"])
        row_date.grid(row=0, column=0, sticky='ew', pady=5)
        
        tk.Label(row_date, text="Start Date:", bg=self.colors["bg_white"], width=10, anchor='w').pack(side='left')
        if HAS_CALENDAR:
            self.ent_date = DateEntry(row_date, width=13, background=self.colors["primary"], foreground='white', date_pattern='yyyy-mm-dd')
            self.ent_date.pack(side='left', padx=(0, 20))
        else:
            self.ent_date = ttk.Entry(row_date, width=13)
            self.ent_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
            self.ent_date.pack(side='left', padx=(0, 20))

        tk.Label(row_date, text="Duration:", bg=self.colors["bg_white"], width=8, anchor='w').pack(side='left')
        self.ent_days = ttk.Entry(row_date, width=5)
        self.ent_days.insert(0, "7")
        self.ent_days.pack(side='left')

        # Generator Section
        tk.Label(frame_time, text="Exam Slots Generator:", bg=self.colors["bg_white"], font=('Segoe UI', 9, 'bold')).grid(row=1, column=0, pady=(5, 2))
        
        auto_frame = tk.Frame(frame_time, bg="#eceff1", pady=5, padx=10)
        auto_frame.grid(row=2, column=0, sticky='ew')

        tk.Label(auto_frame, text="Start:", bg="#eceff1").pack(side='left', padx=5)
        self.ent_start_hour = ttk.Entry(auto_frame, width=6)
        self.ent_start_hour.insert(0, "09:00")
        self.ent_start_hour.pack(side='left')

        tk.Label(auto_frame, text="End:", bg="#eceff1").pack(side='left', padx=(10, 5))
        self.ent_end_hour = ttk.Entry(auto_frame, width=6)
        self.ent_end_hour.insert(0, "17:00")
        self.ent_end_hour.pack(side='left')

        tk.Label(auto_frame, text="Min:", bg="#eceff1").pack(side='left', padx=(10, 5))
        self.ent_duration_min = ttk.Entry(auto_frame, width=4)
        self.ent_duration_min.insert(0, "60")
        self.ent_duration_min.pack(side='left')

        ttk.Button(auto_frame, text="⚡ Generate", command=self.generate_auto_slots).pack(side='left', padx=15)

        # Listbox for Slots (Fill remaining space)
        list_container = tk.Frame(frame_time, bg=self.colors["bg_white"])
        list_container.grid(row=3, column=0, sticky='nsew', pady=5)

        scrollbar = ttk.Scrollbar(list_container, orient="vertical")
        # Drastically reduced default height to prevent push-off, it will expand anyway
        self.lst_slots = tk.Listbox(list_container, borderwidth=1, relief="solid", height=6,
                                    font=('Consolas', 11), yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.lst_slots.yview)

        scrollbar.pack(side='right', fill='y')
        self.lst_slots.pack(side='left', fill='both', expand=True)
        
        default_times = ["09:00-11:00", "11:00-13:00", "13:30-15:30", "15:30-17:30"]
        for t in default_times: self.lst_slots.insert(tk.END, t)

        # Remove Button - Row 4
        bottom_ctrl = tk.Frame(frame_time, bg=self.colors["bg_white"])
        bottom_ctrl.grid(row=4, column=0, sticky='ew', pady=5)
        
        btn_remove = tk.Button(bottom_ctrl, text="Remove Selected (-)", bg="#e53935", fg="white", 
                               font=('Segoe UI', 9, 'bold'), relief='flat', padx=10, command=self.remove_slot)
        btn_remove.pack(side='right')

        # --- Activity Log ---
        log_frame = tk.LabelFrame(right_col, text="Activity Log", **lf_style)
        log_frame.pack(side='top', fill='both', expand=True)

        # Container for text with padding to show white border
        log_inner = tk.Frame(log_frame, bg=self.colors["bg_white"])
        log_inner.pack(fill='both', expand=True, padx=10, pady=10)

        self.txt_log = tk.Text(log_inner, height=15, bg="black", fg="#00ff00",
                               font=('Consolas', 9), wrap='word', state='disabled', padx=8, pady=6)
        log_scroll = ttk.Scrollbar(log_inner, orient='vertical', command=self.txt_log.yview)
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
        f.pack(fill='x', pady=2)
        tk.Label(f, text=label_text, width=20, anchor='w', bg=self.colors["bg_white"]).pack(side='left')
        ttk.Button(f, text="Select File...", command=command_func).pack(side='left')
        lbl_status = tk.Label(f, text="Not Selected", fg="#95a5a6", bg=self.colors["bg_white"], font=('Segoe UI', 9, 'italic'))
        lbl_status.pack(side='left', padx=10)
        command_func.__func__.status_label = lbl_status

    def imp_rooms(self): self.load_file(self.imp_rooms, self.system.load_classrooms_regex)
    def imp_courses(self): self.load_file(self.imp_courses, self.system.load_courses_regex)
    def imp_attendance(self): self.load_file(self.imp_attendance, self.system.load_attendance_regex)
    def imp_students(self): self.load_file(self.imp_students, self.system.load_all_students_regex)

    def load_file(self, func_ref, system_method):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("Text Files", "*.txt"), ("All Files", "*.*")])
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
            # Append to activity log
            try:
                fname = path.split('/')[-1]
            except:
                fname = path
            self.append_log(f"Import {fname}: {msg}")

    # --- DB Methods from Code 2 ---
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

    def save_to_db_slot(self, slot: int):
        try:
            self.system.save_data_to_db(slot)
            messagebox.showinfo("Database", f"Saved to Save {slot} ✅")
            self.append_log(f"Data saved to DB (Save {slot})")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            self.append_log(f"DB Save Error (Save {slot}): {str(e)}")

    def load_from_db_slot(self, slot: int):
        try:
            self.system.load_data_from_db(slot)

            c = len(self.system.classrooms)
            crs = len(self.system.courses)
            st = len(self.system.all_students_list)

            if c == 0 or crs == 0:
                messagebox.showwarning("Database", f"Save {slot} loaded but empty!")
                return

            messagebox.showinfo(
                "Database",
                f"Loaded from Save {slot} ✅\n"
                f"Classrooms: {c}\nCourses: {crs}\nStudents: {st}"
            )
            self.append_log(f"Loaded DB Save {slot}: {c} rooms, {crs} courses, {st} students")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            self.append_log(f"DB Load Error (Save {slot}): {str(e)}")

    def compare_with_save(self, slot: int):
        try:
            result = self.system.compare_with_slot_detailed(slot)
            messagebox.showinfo(f"Compare with Save {slot}", result)
            self.append_log(f"Compared current data with Save {slot}")
        except Exception as e:
            messagebox.showerror("Compare Error", str(e))
            self.append_log(f"Compare Error (Save {slot}): {str(e)}")

    def start_process(self):
        # Required for scheduling: classrooms and attendance (course->students)
        if not self.system.classrooms or not self.system.courses:
            return messagebox.showerror("Missing Data", "Please upload required files: Classroom List and Attendance List.")
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

            # Calculate slot duration in minutes from first slot
            try:
                parts = self.slot_times[0].split('-')
                start = datetime.strptime(parts[0].strip(), "%H:%M")
                end = datetime.strptime(parts[1].strip(), "%H:%M")
                slot_duration_minutes = int((end - start).total_seconds() / 60)
            except:
                slot_duration_minutes = 60  # default

            try:
                days_val = int(self.ent_days.get())
            except:
                days_val = 7

            self.system.num_days = days_val
            self.system.slots_per_day = len(self.slot_times)
            self.system.slot_duration_minutes = slot_duration_minutes

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

    def find_minimum_slots(self):
        """Find the minimum number of slots needed to generate a schedule"""
        if not self.system.classrooms or not self.system.courses:
            return messagebox.showerror("Missing Data", "Please upload required files: Classroom List and Attendance List.")
        
        try:
            # Validate inputs
            if HAS_CALENDAR: 
                self.start_date = self.ent_date.get_date()
            else: 
                self.start_date = datetime.strptime(self.ent_date.get(), "%Y-%m-%d").date()

            raw_slots = list(self.lst_slots.get(0, tk.END))
            if not raw_slots: 
                return messagebox.showerror("Error", "Add at least one time slot.")

            def parse_slot(s):
                start_time_str = s.split('-')[0].strip()
                return datetime.strptime(start_time_str, "%H:%M")

            self.slot_times = sorted(raw_slots, key=parse_slot)

            # Calculate slot duration
            try:
                parts = self.slot_times[0].split('-')
                start = datetime.strptime(parts[0].strip(), "%H:%M")
                end = datetime.strptime(parts[1].strip(), "%H:%M")
                slot_duration_minutes = int((end - start).total_seconds() / 60)
            except:
                slot_duration_minutes = 60

            try:
                days_val = int(self.ent_days.get())
            except:
                days_val = 7

            # Get initial total slots (days * slots_per_day)
            slots_per_day = len(self.slot_times)
            initial_total_slots = days_val * slots_per_day

            self.append_log("Finding minimum slots needed...")
            self.lbl_log.config(text="Finding minimum slots...")
            self.btn_start.config(state='disabled')
            self.btn_stop.config(state='disabled')
            self.btn_find_min.config(state='disabled')
            
            # Start the process in a thread
            threading.Thread(target=self.run_find_min_slots, args=(initial_total_slots, slots_per_day, slot_duration_minutes), daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.append_log(f"Error in find_minimum_slots: {str(e)}")

    def run_find_min_slots(self, initial_total_slots, slots_per_day, slot_duration_minutes):
        """Thread function to iteratively find minimum slots"""
        current_total_slots = initial_total_slots
        found = False
        attempt = 0
        
        while not found:
            attempt += 1
            # Calculate days needed for current total slots
            current_days = (current_total_slots + slots_per_day - 1) // slots_per_day  # Ceiling division
            
            # Update system parameters
            self.system.num_days = current_days
            self.system.slots_per_day = slots_per_day
            self.system.slot_duration_minutes = slot_duration_minutes
            
            # Log the attempt
            log_msg = f"Attempt {attempt}: Trying {current_total_slots} total slots ({current_days} days × {slots_per_day} slots/day)"
            self.root.after(0, lambda msg=log_msg: self.append_log(msg))
            self.root.after(0, lambda: self.lbl_log.config(text=f"Testing {current_total_slots} slots..."))
            
            # Try to solve with current configuration
            success, msg = self.system.solve(time_limit_sec=5)
            
            if success:
                found = True
                result_msg = f"✓ RECOMMENDED SLOTS: {current_total_slots} ({current_days} days × {slots_per_day} slots/day)"
                self.root.after(0, lambda: self.finish_find_min_slots(True, result_msg, current_total_slots, current_days))
                return
            
            # Increase slots by 20
            current_total_slots += 20
            
            # Safety limit to prevent infinite loop
            if current_total_slots > 500:
                result_msg = "Could not find feasible schedule within reasonable limits (max 500 slots tested)"
                self.root.after(0, lambda: self.finish_find_min_slots(False, result_msg, 0, 0))
                return
            
            # Wait 0.5 seconds before next attempt
            time.sleep(0.5)

    def finish_find_min_slots(self, success, msg, total_slots, days):
        """Callback when find_minimum_slots completes"""
        self.lbl_log.config(text=msg)
        self.btn_start.config(state='normal')
        self.btn_stop.config(state='normal')
        self.btn_find_min.config(state='normal')
        
        if success:
            self.append_log(msg)
            messagebox.showinfo("Minimum Slots Found", 
                               f"Recommended configuration:\n\n"
                               f"Total Slots: {total_slots}\n"
                               f"Days: {days}\n"
                               f"Slots per day: {self.system.slots_per_day}\n\n"
                               f"A schedule has been successfully generated with this configuration!")
            
            # Show the generated schedule
            self.notebook.select(self.tab_schedule)
            self.refresh_table()
        else:
            self.append_log(f"Find minimum slots failed: {msg}")
            messagebox.showerror("Failed", msg)

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
                          values=["General Schedule", "Daily Plan", "Student Based", "Classroom Based", "Exam Attendance"],
                          state='readonly', width=20)
        cb.pack(side='left', padx=10)
        cb.bind("<<ComboboxSelected>>", self.refresh_table)

        # Export Buttons
        ttk.Button(top_bar, text="Export CSV", command=self.export_to_csv).pack(side='right')
        ttk.Button(top_bar, text="Export PDF", command=self.export_to_pdf).pack(side='right', padx=(10, 0))

        # Main container - each view gets completely isolated frames
        self.views_container = tk.Frame(self.tab_schedule, bg=self.colors["bg_white"])
        self.views_container.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        self.views_container.grid_rowconfigure(0, weight=1)
        self.views_container.grid_columnconfigure(0, weight=1)

        # 1. General Schedule View (tree-based)
        self.general_frame = tk.Frame(self.views_container, bg=self.colors["bg_white"])
        self.general_frame.grid(row=0, column=0, sticky='nsew')
        scrolly_gen = ttk.Scrollbar(self.general_frame, orient="vertical")
        scrollx_gen = ttk.Scrollbar(self.general_frame, orient="horizontal")
        self.tree_general = ttk.Treeview(self.general_frame, show='headings', yscrollcommand=scrolly_gen.set, xscrollcommand=scrollx_gen.set)
        scrolly_gen.config(command=self.tree_general.yview)
        scrollx_gen.config(command=self.tree_general.xview)
        scrolly_gen.pack(side="right", fill="y")
        scrollx_gen.pack(side="bottom", fill="x")
        self.tree_general.pack(side="left", fill="both", expand=True)
        self.set_columns_general_tree(self.tree_general)

        # 2. Classroom Based View (tree-based)
        self.classroom_frame = tk.Frame(self.views_container, bg=self.colors["bg_white"])
        self.classroom_frame.grid(row=0, column=0, sticky='nsew')
        scrolly_cls = ttk.Scrollbar(self.classroom_frame, orient="vertical")
        scrollx_cls = ttk.Scrollbar(self.classroom_frame, orient="horizontal")
        self.tree_classroom = ttk.Treeview(self.classroom_frame, show='headings', yscrollcommand=scrolly_cls.set, xscrollcommand=scrollx_cls.set)
        scrolly_cls.config(command=self.tree_classroom.yview)
        scrollx_cls.config(command=self.tree_classroom.xview)
        scrolly_cls.pack(side="right", fill="y")
        scrollx_cls.pack(side="bottom", fill="x")
        self.tree_classroom.pack(side="left", fill="both", expand=True)
        self.set_columns_classroom_tree(self.tree_classroom)

        # 3. Daily Plan View (custom frame)
        self.daily_frame = tk.Frame(self.views_container, bg=self.colors["bg_white"])
        self.daily_frame.grid(row=0, column=0, sticky='nsew')

        # 4. Student Based View (custom frame)
        self.student_view_frame = tk.Frame(self.views_container, bg=self.colors["bg_white"])
        self.student_view_frame.grid(row=0, column=0, sticky='nsew')

        # 5. Exam Attendance View (custom frame)
        self.attendance_view_frame = tk.Frame(self.views_container, bg=self.colors["bg_white"])
        self.attendance_view_frame.grid(row=0, column=0, sticky='nsew')

    def get_real_datetime(self, d, s, course_code=None):
        date = self.start_date + timedelta(days=d)
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        # If course_code is provided and has explicit duration, calculate actual exam duration
        if course_code:
            course = next((c for c in self.system.courses if c.code == course_code), None)
            if course and s < len(self.slot_times):
                # Check if course has explicit duration from file
                if hasattr(course, '_explicit_duration') and course._explicit_duration:
                    # Get start time from slot
                    start_time_str = self.slot_times[s].split('-')[0].strip()
                    try:
                        start_time = datetime.strptime(start_time_str, "%H:%M")
                        end_time = start_time + timedelta(minutes=course.duration)
                        end_time_str = end_time.strftime("%H:%M")
                        time = f"{start_time_str}-{end_time_str}"
                    except:
                        # Fallback to slot-based calculation
                        slots_needed = self.system.get_slots_needed(course)
                        end_slot_index = s + slots_needed - 1
                        if end_slot_index < len(self.slot_times):
                            end_time_str = self.slot_times[end_slot_index].split('-')[1].strip()
                            start_time_str = self.slot_times[s].split('-')[0].strip()
                            time = f"{start_time_str}-{end_time_str}"
                        else:
                            time = self.slot_times[s]
                else:
                    # No explicit duration - use slot time directly
                    time = self.slot_times[s]
            else:
                time = self.slot_times[s] if s < len(self.slot_times) else "??"
        else:
            time = self.slot_times[s] if s < len(self.slot_times) else "??"
        
        return f"{date.strftime('%Y-%m-%d')} ({days[date.weekday()]}) {time}"

    def get_day_and_date(self, d):
        date = self.start_date + timedelta(days=d)
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return f"{date.strftime('%Y-%m-%d')} ({days[date.weekday()]})"

    def set_columns_general_tree(self, tree):
        cols = ["Course", "Time", "Count", "Classroom", "Capacity"]
        tree['columns'] = cols
        for c in cols: tree.heading(c, text=c)
        tree.column("Course", width=200, anchor='center')
        tree.column("Time", width=300)
        tree.column("Count", width=100, anchor='center')
        tree.column("Classroom", width=200)
        tree.column("Capacity", width=120, anchor='center')

    def set_columns_classroom_tree(self, tree):
        cols = ["Classroom", "Time", "Course", "Status"]
        tree['columns'] = cols
        for c in cols: tree.heading(c, text=c)
        tree.column("Classroom", width=150, anchor='center')
        tree.column("Time", width=300, anchor='w')
        tree.column("Course", width=200, anchor='center')
        tree.column("Status", width=120, anchor='center')

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
        
        # Hide all view frames first
        self.general_frame.grid_remove()
        self.classroom_frame.grid_remove()
        self.daily_frame.grid_remove()
        self.student_view_frame.grid_remove()
        self.attendance_view_frame.grid_remove()
        
        # Clear all frames completely
        for widget in self.daily_frame.winfo_children():
            widget.destroy()
        for widget in self.student_view_frame.winfo_children():
            widget.destroy()
        for widget in self.attendance_view_frame.winfo_children():
            widget.destroy()
        
        # Clear tree views
        for item in self.tree_general.get_children():
            self.tree_general.delete(item)
        for item in self.tree_classroom.get_children():
            self.tree_classroom.delete(item)
        
        self.full_data = []
        
        if mode == "General Schedule":
            # Populate general schedule tree
            for c_code, (d, s, rooms) in self.system.assignments.items():
                c = next((x for x in self.system.courses if x.code == c_code), None)
                st_cnt = len(c.students) if c else 0
                r_names = ", ".join([r.code for r in rooms])
                cap = f"{st_cnt} / {sum(r.capacity for r in rooms)}"
                self.full_data.append((c_code, self.get_real_datetime(d, s, c_code), st_cnt, r_names, cap))
            
            for row in self.full_data:
                self.tree_general.insert('', 'end', values=row)
            self.general_frame.grid()
            
        elif mode == "Classroom Based":
            # Populate classroom based tree
            for c_code, (d, s, rooms) in self.system.assignments.items():
                for r in rooms:
                    self.full_data.append((r.code, self.get_real_datetime(d, s, c_code), c_code, "OCCUPIED"))
            self.full_data.sort()
            
            for row in self.full_data:
                self.tree_classroom.insert('', 'end', values=row)
            self.classroom_frame.grid()
            
        elif mode == "Daily Plan":
            # Build daily plan view with date picker
            from collections import defaultdict
            day_groups = defaultdict(list)
            for c_code, (d, s, rooms) in self.system.assignments.items():
                date = (self.start_date + timedelta(days=d)).strftime('%Y-%m-%d')
                c = next((x for x in self.system.courses if x.code == c_code), None)
                
                if c and s < len(self.slot_times):
                    if hasattr(c, '_explicit_duration') and c._explicit_duration:
                        start_time_str = self.slot_times[s].split('-')[0].strip()
                        try:
                            start_time = datetime.strptime(start_time_str, "%H:%M")
                            end_time = start_time + timedelta(minutes=c.duration)
                            end_time_str = end_time.strftime("%H:%M")
                            time_str = f"{start_time_str}-{end_time_str}"
                        except:
                            slots_needed = self.system.get_slots_needed(c)
                            end_slot = s + slots_needed - 1
                            if end_slot < len(self.slot_times):
                                end_time_str = self.slot_times[end_slot].split('-')[1].strip()
                                time_str = f"{start_time_str}-{end_time_str}"
                            else:
                                time_str = self.slot_times[s]
                    else:
                        time_str = self.slot_times[s]
                else:
                    time_str = self.slot_times[s] if s < len(self.slot_times) else '??'
                
                st_cnt = len(c.students) if c else 0
                r_names = ", ".join([r.code for r in rooms])
                day_groups[date].append((time_str, c_code, r_names, st_cnt))
            
            self.day_groups = {k: sorted(v, key=lambda x: x[0]) for k, v in day_groups.items()}
            
            # Build daily plan UI
            search_frame = tk.Frame(self.daily_frame, bg=self.colors["bg_white"])
            search_frame.pack(fill='x', padx=6, pady=(6,4))
            tk.Label(search_frame, text="Select Date:", bg=self.colors["bg_white"]).pack(side='left')
            
            if HAS_CALENDAR:
                dp = DateEntry(search_frame, width=12, background=self.colors["primary"], foreground='white', date_pattern='yyyy-mm-dd')
            else:
                dp = ttk.Entry(search_frame, width=12)
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
                self._show_day_schedule(sel, self.daily_frame)
            
            pick_btn = ttk.Button(search_frame, text="Search", command=_do_pick)
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
                self._show_day_schedule(default_day, self.daily_frame)
            else:
                lbl = tk.Label(self.daily_frame, text="No schedule data available.", bg=self.colors["bg_white"], fg=self.colors["text_body"])
                lbl.pack(pady=20)
            
            self.daily_frame.grid()
            
        elif mode == "Student Based":
            # Build student based view
            temp_data = []
            for (sid, c_code), r_code in self.system.student_room_map.items():
                if c_code in self.system.assignments:
                    d, s, _ = self.system.assignments[c_code]
                    temp_data.append((sid, c_code, self.get_real_datetime(d, s, c_code), r_code))
            temp_data.sort(key=lambda x: (x[0], x[2]))
            self.full_data = temp_data
            
            from collections import defaultdict
            groups = defaultdict(list)
            for sid, c_code, time_str, r_code in temp_data:
                groups[sid].append((c_code, time_str, r_code))
            self.student_groups = groups
            self.student_list_sorted = sorted(groups.keys())
            
            # Build student search UI
            search_frame = tk.Frame(self.student_view_frame, bg=self.colors["bg_white"])
            search_frame.pack(fill='x', padx=6, pady=(6,4))
            tk.Label(search_frame, text="Student ID:", bg=self.colors["bg_white"]).pack(side='left')
            
            self.search_var = tk.StringVar()
            search_entry = ttk.Combobox(search_frame, textvariable=self.search_var, width=20, values=self.student_list_sorted)
            search_entry.pack(side='left', padx=(6,4))
            
            def _do_search(event=None):
                sid = self.search_var.get().strip()
                if not sid and self.student_list_sorted:
                    sid = self.student_list_sorted[0]
                if sid not in self.student_groups:
                    messagebox.showwarning("Not found", f"Student ID '{sid}' not found.")
                    return
                self._show_student_schedule(sid, self.student_view_frame)
            
            search_btn = ttk.Button(search_frame, text="Search", command=_do_search)
            search_btn.pack(side='left', padx=(4,0))
            search_entry.bind('<Return>', _do_search)
            search_entry.bind('<<ComboboxSelected>>', _do_search)
            
            default_sid = self.student_list_sorted[0] if self.student_list_sorted else None
            if default_sid:
                self.search_var.set(default_sid)
                self._show_student_schedule(default_sid, self.student_view_frame)
            else:
                lbl = tk.Label(self.student_view_frame, text="No student assignments available.", bg=self.colors["bg_white"], fg=self.colors["text_body"])
                lbl.pack(pady=20)
            
            self.student_view_frame.grid()
            
        elif mode == "Exam Attendance":
            # Build exam attendance view
            self.course_list_sorted = ["📋 All Students Overview"] + sorted([c.code for c in self.system.courses])
            
            search_frame = tk.Frame(self.attendance_view_frame, bg=self.colors["bg_white"])
            search_frame.pack(fill='x', padx=6, pady=(6,4))
            tk.Label(search_frame, text="Select View:", bg=self.colors["bg_white"]).pack(side='left')
            
            self.course_var = tk.StringVar()
            course_combo = ttk.Combobox(search_frame, textvariable=self.course_var,
                                        values=self.course_list_sorted, state='readonly', width=30)
            course_combo.pack(side='left', padx=(6,4))
            
            def _show_course_attendance(event=None):
                selected = self.course_var.get()
                if not selected:
                    messagebox.showwarning("Select View", "Please choose an option.")
                    return
                # Clear previous attendance display
                for widget in self.attendance_view_frame.winfo_children():
                    if widget != search_frame:
                        widget.destroy()
                if selected == "📋 All Students Overview":
                    self._show_all_students_attendance(self.attendance_view_frame)
                else:
                    self._show_exam_attendance(selected, self.attendance_view_frame)
            
            course_combo.bind("<<ComboboxSelected>>", _show_course_attendance)
            show_btn = ttk.Button(search_frame, text="Show", command=_show_course_attendance)
            show_btn.pack(side='left', padx=(4,0))
            
            if self.course_list_sorted:
                self.course_var.set(self.course_list_sorted[0])
                self._show_all_students_attendance(self.attendance_view_frame)
            else:
                lbl = tk.Label(self.attendance_view_frame, text="No data available.", bg=self.colors["bg_white"], fg=self.colors["text_body"])
                lbl.pack(pady=20)
            
            self.attendance_view_frame.grid()

    def export_to_csv(self):
        view_name = self.view_var.get()

        # If Exam Attendance view, export the attendance data
        if view_name == "Exam Attendance":
            all_students = self.system.all_students_list
            if not all_students:
                return messagebox.showwarning("Warning", "No 'All Students' data loaded.")
            
            default_name = "Exam_Attendance_AllStudents.csv"
            path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default_name, filetypes=[("CSV Files", "*.csv")])
            if not path:
                return
            
            try:
                with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f, delimiter=';')
                    cols = ["Student ID", "Enrolled Courses", "Exam Count", "Status"]
                    writer.writerow(cols)
                    
                    # Get all students who are enrolled in any course (from attendance)
                    enrolled_students = set()
                    for course in self.system.courses:
                        for student in course.students:
                            enrolled_students.add(student)
                    
                    students_sorted = sorted(all_students)
                    for student_id in students_sorted:
                        # Find courses this student is enrolled in
                        student_courses = []
                        for course in self.system.courses:
                            if student_id in course.students:
                                student_courses.append(course.code)
                        
                        exam_count = len(student_courses)
                        if exam_count > 0:
                            courses_str = ", ".join(sorted(student_courses))
                            status = f"Enrolled ({exam_count} Exams)"
                        else:
                            courses_str = "No enrollment"
                            status = "No Exam"
                        
                        writer.writerow([student_id, courses_str, exam_count, status])
                
                messagebox.showinfo("Success", f"Exam Attendance exported successfully!")
                self.append_log(f"Exported CSV for Exam Attendance: {path}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed:\n{str(e)}")
                self.append_log(f"Export failed: {str(e)}")
            return

        # If Daily Plan view, ask whether to export current day or all days
        if view_name == "Daily Plan":
            if not hasattr(self, 'day_groups') or not self.day_groups:
                return messagebox.showwarning("Warning", "No data to export.")

            export_choice = messagebox.askyesnocancel("Export Options",
                                                      "Export current day (Yes) or all days (No)?")
            if export_choice is None:
                return

            if export_choice:  # Export current day only
                # Get current selected date from day_search_frame
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
            else:  # Export all days
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

        if not self.full_data: return messagebox.showwarning("Warning", "No data to export.")

        # If Student Based view, ask whether to export only the currently shown student
        if view_name == "Student Based":
            only_one = messagebox.askyesno("Export Options", "Export only the currently shown student (Yes) or all students (No)?")
            if only_one:
                # determine current student id from search_var or fallback
                sid = None
                if hasattr(self, 'search_var') and getattr(self, 'search_var'):
                    sid = self.search_var.get().strip()
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

        # Default: export full view data
        view_name_fname = view_name.replace(" ", "_")
        default_name = f"Schedule_{view_name_fname}.csv"
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default_name, filetypes=[("CSV Files", "*.csv")])
        if not path:
            return
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                # Determine columns based on view type
                if view_name == "General Schedule":
                    cols = ["Course", "Time", "Count", "Classroom", "Capacity"]
                elif view_name == "Classroom Based":
                    cols = ["Classroom", "Time", "Course", "Status"]
                else:
                    cols = []
                
                if cols:
                    writer.writerow(cols)
                    writer.writerows(self.full_data)
                else:
                    writer.writerows(self.full_data)
            messagebox.showinfo("Success", f"Data exported successfully!\nPlan: {self.view_var.get()}")
            self.append_log(f"Exported CSV: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed:\n{str(e)}")
            self.append_log(f"Export failed: {str(e)}")

    def export_to_pdf(self):
        # Merge of Block 2's PDF export logic
        if not self.full_data and self.view_var.get() not in ["Daily Plan", "Exam Attendance"]:
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

            # Special handling for Daily Plan in PDF (since full_data is empty in that view in Code 1's logic)
            if self.view_var.get() == "Daily Plan":
                if not hasattr(self, 'day_groups') or not self.day_groups:
                    return messagebox.showwarning("Warning", "No data to export.")
                # Flatten daily groups for PDF
                cols = ["Date", "Time", "Course", "Classroom", "Students"]
                data_rows = []
                for date_str in sorted(self.day_groups.keys()):
                    for row in self.day_groups[date_str]:
                        # row = (time_str, c_code, r_names, st_cnt)
                        data_rows.append([date_str] + list(row))
                headers = cols
                table_data = [headers] + data_rows
            elif self.view_var.get() == "Exam Attendance":
                # Special handling for Exam Attendance
                all_students = self.system.all_students_list
                if not all_students:
                    return messagebox.showwarning("Warning", "No 'All Students' data loaded.")
                
                headers = ["Student ID", "Enrolled Courses", "Exam Count", "Status"]
                data_rows = []
                
                students_sorted = sorted(all_students)
                for student_id in students_sorted:
                    student_courses = []
                    for course in self.system.courses:
                        if student_id in course.students:
                            student_courses.append(course.code)
                    
                    exam_count = len(student_courses)
                    if exam_count > 0:
                        courses_str = ", ".join(sorted(student_courses)[:4])
                        if len(student_courses) > 4:
                            courses_str += f" (+{len(student_courses) - 4})"
                        status = f"Enrolled"
                    else:
                        courses_str = "No enrollment"
                        status = "No Exam"
                    
                    data_rows.append([student_id, courses_str, str(exam_count), status])
                
                table_data = [headers] + data_rows
            elif self.view_var.get() == "Student Based":
                # Special handling for Student Based
                headers = ["Student", "Course", "Date/Time", "Classroom"]
                table_data = [headers] + [list(r) for r in self.full_data]
            else:
                # General Schedule or Classroom Based
                if self.view_var.get() == "General Schedule":
                    headers = ["Course", "Time", "Count", "Classroom", "Capacity"]
                elif self.view_var.get() == "Classroom Based":
                    headers = ["Classroom", "Time", "Course", "Status"]
                else:
                    headers = ["Data"]
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

        # Help content pages
        help_pages = {
            
   

    "index": {
        "title": "Help Menu",
        "content":
            "EXAMTABLE MANAGER – HELP MENU\n\n"
            "Select a topic below to learn how to use the system.\n\n"
            "1. How to Use\n"
            "2. Input File Information\n"
            "3. Rules and Constraints\n"
            "4. About\n",
        "links": [
            ("How to Use", "howto"),
            ("Input File Information", "input"),
            ("Rules and Constraints", "rules"),
            ("About", "about")
        ]
    },

    "howto": {
        "title": "How to Use",
        "content":
            "HOW TO USE THE SYSTEM\n\n"

            "STEP 1 – DATA MANAGEMENT (Files & Database)\n"
            "- Use the 'Select File...' buttons to upload:\n"
            "  • Classrooms & Capacities\n"
            "  • Attendance Lists\n"
            "  • All Courses\n"
            "  • All Students\n"
            "- After a file is loaded successfully, its status will turn green.\n"
            "- Database buttons (Save / Load / Compare) allow storing and comparing data states.\n\n"

            "STEP 2 – EXAM CALENDAR SETTINGS\n"
            "- Select the exam Start Date.\n"
            "- Enter the total exam Duration (number of days).\n\n"

            "STEP 3 – EXAM SLOTS GENERATOR\n"
            "- Enter daily Start and End times.\n"
            "- Specify the minimum exam duration (minutes).\n"
            "- Click 'Generate' to automatically create time slots.\n"
            "- Slots can be manually removed using 'Remove Selected (-)'.\n\n"

            "STEP 4 – GENERATE SCHEDULE\n"
            "- Click 'GENERATE SCHEDULE' to start automatic scheduling.\n"
            "- The system assigns exams while respecting all constraints.\n"
            "- You may stop the process at any time using the STOP button.\n\n"

            "STEP 5 – VIEW RESULTS\n"
            "- Switch to the 'SCHEDULE (RESULT)' tab.\n"
            "- Choose different views:\n"
            "  • General Schedule\n"
            "  • Daily Plan\n"
            "  • Student Based\n"
            "  • Classroom Based\n"
            "  • Exam Attendance\n\n"

            "STEP 6 – EXPORT\n"
            "- Export the generated schedule as CSV or PDF.\n"
            "- Export options change depending on the selected view.\n",
        "links": []
    },

    "input": {
        "title": "Input File Information",
        "content":
            "INPUT FILE FORMAT INFORMATION\n\n"

            "Classroom List:\n"
            "- classroom_code, capacity\n\n"

            "Attendance List:\n"
            "- course_code, student_id\n\n"

            "All Courses:\n"
            "- course_code, duration (optional)\n\n"

            "All Students:\n"
            "- student_id\n\n"

            "Supported file format: CSV\n",
        "links": []
    },

    "rules": {
        "title": "Rules and Constraints",
        "content":
            "RULES AND CONSTRAINTS\n\n"
            "- A student cannot have more than one exam at the same time.\n"
            "- A classroom cannot host multiple exams in the same slot.\n"
            "- Classroom capacity must be sufficient for enrolled students.\n"
            "- Each course is scheduled exactly once.\n"
            "- The system stops automatically if no valid solution is found.\n",
        "links": []
    },

    "about": {
        "title": "About",
        "content":
            "ABOUT EXAMTABLE MANAGER\n\n"
            "Examtable Manager is an automatic exam scheduling system\n"
            "developed for the SE-302 Software Engineering course.\n\n"
            "The system generates conflict-free exam timetables\n"
            "using constraint-based scheduling logic.\n",
        "links": []
    }
}



        # Current page tracking
        current_page = {"page": "index"}

        # Title
        title_label = tk.Label(help_window, text="Help Menu", font=('Segoe UI', 16, 'bold'),
                               bg=self.colors["bg_white"], fg=self.colors["primary"])
        title_label.pack(fill='x', padx=20, pady=15)

        # Content frame
        content_frame = tk.Frame(help_window, bg=self.colors["bg_white"])
        content_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))

        scrollbar = ttk.Scrollbar(content_frame)
        scrollbar.pack(side='right', fill='y')

        help_text = tk.Text(content_frame, wrap='word', font=('Segoe UI', 10),
                            bg=self.colors["bg_white"], fg=self.colors["text_body"],
                            yscrollcommand=scrollbar.set, relief='flat', borderwidth=0, height=20)
        scrollbar.config(command=help_text.yview)
        help_text.pack(fill='both', expand=True)

        # Configure tags
        help_text.tag_configure("link", foreground="blue", underline=True)
        help_text.tag_bind("link", "<Enter>", lambda e: help_text.config(cursor="hand2"))
        help_text.tag_bind("link", "<Leave>", lambda e: help_text.config(cursor="arrow"))

        # Navigation frame
        nav_frame = tk.Frame(help_window, bg=self.colors["bg_white"])
        nav_frame.pack(fill='x', padx=20, pady=10)

        btn_back = ttk.Button(nav_frame, text="← Back to Index")
        btn_back.pack(side='left', padx=5)

        close_btn = ttk.Button(nav_frame, text="Close", command=help_window.destroy)
        close_btn.pack(side='right', padx=5)

        # Load page function
        def load_page(page_key):
            help_text.config(state='normal')
            help_text.delete('1.0', tk.END)

            page = help_pages.get(page_key, help_pages["index"])
            current_page["page"] = page_key

            # Update title
            title_label.config(text=page["title"])

            # Add content
            help_text.insert('end', page["content"] + "\n\n")

            # Add links if any
            if page["links"]:
                help_text.insert('end', "\n--- Related Topics ---\n\n")
                for link_text, link_page in page["links"]:
                    # Create unique tag for each link
                    unique_tag = f"link_{link_page}"
                    help_text.tag_configure(unique_tag, foreground="blue", underline=True)
                    help_text.tag_bind(unique_tag, "<Enter>", lambda e: help_text.config(cursor="hand2"))
                    help_text.tag_bind(unique_tag, "<Leave>", lambda e: help_text.config(cursor="arrow"))
                    help_text.tag_bind(unique_tag, "<Button-1>", lambda e, lp=link_page: load_page(lp))

                    help_text.insert('end', f"• {link_text}\n", unique_tag)

            help_text.config(state='disabled')

            # Update navigation buttons
            btn_back.config(state='normal' if page_key != "index" else 'disabled')

        # Set back button command
        btn_back.config(command=lambda: load_page("index"))

        # Load initial page
        load_page("index")

    def append_log(self, text):
        """Append a timestamped entry to the activity log (read-only Text widget)."""
        try:
            ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            entry = f"[{ts}] {text}\n"
            self.txt_log.config(state='normal')
            self.txt_log.insert('end', entry)
            self.txt_log.see('end')
            self.txt_log.config(state='disabled')
        except Exception:
            # If log widget isn't available, fallback to status label
            try:
                self.lbl_log.config(text=text)
            except Exception:
                pass

    def _show_student_schedule(self, sid, parent_frame):
        """Display a single student's schedule in the parent frame."""
        # Clear previous student schedule display (but keep search frame)
        for widget in parent_frame.winfo_children():
            # Keep the search frame (first child), destroy everything else
            if widget != parent_frame.winfo_children()[0]:
                widget.destroy()
        
        # container for one student's schedule (no vertical scrollbar)
        student_frame = tk.Frame(parent_frame, bg=self.colors["bg_white"])
        student_frame.pack(fill='both', expand=False, padx=6, pady=6)

        # header
        hdr = tk.Frame(student_frame, bg="#cfd8dc")
        hdr.pack(padx=5, pady=(6,0))
        lbl = tk.Label(hdr, text=f"Student ID: {sid}", bg="#cfd8dc", fg=self.colors["text_header"], font=('Segoe UI', 12, 'bold'))
        lbl.pack(side='left', padx=6, pady=6)

        # build student's table (height = number of exams so no empty space below)
        courses = self.student_groups.get(sid, [])
        cols = ["Course", "Date", "Time", "Classroom"]
        tbl_frame = tk.Frame(student_frame, bg=self.colors["bg_white"])
        # don't force the frame to stretch horizontally; let the tree's column widths define table width
        tbl_frame.pack(fill='both', expand=False, padx=10, pady=8)

        tbl_height = max(1, min(len(courses), 40))
        tbl = ttk.Treeview(tbl_frame, columns=cols, show='headings', height=tbl_height)
        for c in cols:
            tbl.heading(c, text=c)
        # Fixed column widths chosen so the total table width is consistent across views
        tbl.column("Course", width=300)
        tbl.column("Date", width=140, anchor='center')
        tbl.column("Time", width=140, anchor='center')
        tbl.column("Classroom", width=160, anchor='center')

        for c_code, time_str, r_code in courses:
            # time_str format: 'YYYY-MM-DD (Weekday) HH:MM-...'
            parts = time_str.split()
            date_part = parts[0] if parts else ""
            time_part = parts[-1] if len(parts) > 1 else ""
            tbl.insert('', 'end', values=(c_code, date_part, time_part, r_code))

        # pack table so its vertical size matches rows and it stays centered horizontally
        tbl.pack(anchor='n')

        # ensure visible top
        try:
            tbl.yview_moveto(0)
        except Exception:
            pass

    def _show_day_schedule(self, date_str, parent_frame):
        """Display a single day's schedule in the parent frame."""
        # Clear previous day schedule display (but keep search frame)
        for widget in parent_frame.winfo_children():
            # Keep the search frame (first child), destroy everything else
            if widget != parent_frame.winfo_children()[0]:
                widget.destroy()
        
        day_frame = tk.Frame(parent_frame, bg=self.colors["bg_white"])
        day_frame.pack(fill='both', expand=False, padx=6, pady=6)

        hdr = tk.Frame(day_frame, bg="#cfd8dc")
        hdr.pack(padx=5, pady=(6,0))
        lbl = tk.Label(hdr, text=f"Date: {date_str}", bg="#cfd8dc", fg=self.colors["text_header"], font=('Segoe UI', 12, 'bold'))
        lbl.pack(side='left', padx=6, pady=6)

        # build table for day
        rows = self.day_groups.get(date_str, [])
        cols = ["Time", "Course", "Classroom", "Students"]
        tbl_frame = tk.Frame(day_frame, bg=self.colors["bg_white"])
        # do not force horizontal stretch; the tree will use the sum of its column widths
        tbl_frame.pack(fill='both', expand=False, padx=10, pady=8)

        tbl_height = max(1, min(len(rows), 40))
        tbl = ttk.Treeview(tbl_frame, columns=cols, show='headings', height=tbl_height)
        for c in cols:
            tbl.heading(c, text=c)
        # Match the student table total width (300+140+140+160 = 740)
        tbl.column("Time", width=140, anchor='center')
        tbl.column("Course", width=300, anchor='center')
        tbl.column("Classroom", width=160, anchor='center')
        tbl.column("Students", width=140, anchor='center')

        for time_str, c_code, r_names, st_cnt in rows:
            tbl.insert('', 'end', values=(time_str, c_code, r_names, st_cnt))

        # anchor at top-center; height is controlled by number of rows so there is no extra space below
        tbl.pack(anchor='n')
        try:
            tbl.yview_moveto(0)
        except Exception:
            pass

    def _show_exam_attendance(self, course_code, parent_frame):
        """Display exam attendance for a specific course - shows which students are enrolled and their room assignment."""
        attendance_frame = tk.Frame(parent_frame, bg=self.colors["bg_white"])
        attendance_frame.pack(fill='both', expand=True, padx=6, pady=6)

        # Find the course
        course = next((c for c in self.system.courses if c.code == course_code), None)
        if not course:
            lbl = tk.Label(attendance_frame, text=f"Course '{course_code}' not found.", 
                          bg=self.colors["bg_white"], fg=self.colors["text_body"])
            lbl.pack(pady=20)
            return

        # Header with course info
        hdr = tk.Frame(attendance_frame, bg="#cfd8dc")
        hdr.pack(fill='x', padx=5, pady=(6,0))
        
        # Get exam info if scheduled
        exam_info = ""
        scheduled_room = ""
        if course_code in self.system.assignments:
            d, s, rooms = self.system.assignments[course_code]
            exam_info = f" | Exam: {self.get_real_datetime(d, s, course_code)}"
            scheduled_room = ", ".join([r.code for r in rooms])
        
        lbl = tk.Label(hdr, text=f"Course: {course_code} | Students: {len(course.students)}{exam_info}", 
                      bg="#cfd8dc", fg=self.colors["text_header"], font=('Segoe UI', 12, 'bold'))
        lbl.pack(side='left', padx=6, pady=6)
        
        if scheduled_room:
            room_lbl = tk.Label(hdr, text=f"Room(s): {scheduled_room}", 
                              bg="#cfd8dc", fg=self.colors["primary"], font=('Segoe UI', 10))
            room_lbl.pack(side='right', padx=6, pady=6)

        # Summary stats
        stats_frame = tk.Frame(attendance_frame, bg=self.colors["bg_white"])
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        # Count students with room assignments
        assigned_count = 0
        for student in course.students:
            if (student, course_code) in self.system.student_room_map:
                assigned_count += 1
        not_assigned_count = len(course.students) - assigned_count
        
        stats_text = f"✓ Assigned: {assigned_count}  |  ✗ Not Assigned: {not_assigned_count}"
        stats_lbl = tk.Label(stats_frame, text=stats_text, bg=self.colors["bg_white"], 
                            fg=self.colors["text_body"], font=('Segoe UI', 10))
        stats_lbl.pack(side='left')

        # Student list table with scrollbar
        tbl_container = tk.Frame(attendance_frame, bg=self.colors["bg_white"])
        tbl_container.pack(fill='both', expand=True, padx=10, pady=8)

        cols = ["Student ID", "Room Assignment", "Status"]
        
        scrollbar = ttk.Scrollbar(tbl_container, orient="vertical")
        tbl = ttk.Treeview(tbl_container, columns=cols, show='headings', 
                          yscrollcommand=scrollbar.set, height=20)
        scrollbar.config(command=tbl.yview)
        
        for c in cols:
            tbl.heading(c, text=c)
        tbl.column("Student ID", width=250, anchor='center')
        tbl.column("Room Assignment", width=250, anchor='center')
        tbl.column("Status", width=180, anchor='center')

        # Populate table with students
        students_sorted = sorted(course.students)
        for student_id in students_sorted:
            room = self.system.student_room_map.get((student_id, course_code), None)
            if room:
                status = "✓ Assigned"
                status_tag = "assigned"
            else:
                room = "Not Assigned"
                status = "✗ Not Assigned"
                status_tag = "not_assigned"
            tbl.insert('', 'end', values=(student_id, room, status), tags=(status_tag,))
        
        # Configure row colors
        tbl.tag_configure("assigned", background="#e8f5e9")  # light green
        tbl.tag_configure("not_assigned", background="#ffebee")  # light red

        scrollbar.pack(side='right', fill='y')
        tbl.pack(side='left', fill='both', expand=True)
        
        try:
            tbl.yview_moveto(0)
        except Exception:
            pass

    def _show_all_students_attendance(self, parent_frame):
        """Display all students from 'All Students' file and show which ones are enrolled in exams."""
        attendance_frame = tk.Frame(parent_frame, bg=self.colors["bg_white"])
        attendance_frame.pack(fill='both', expand=True, padx=6, pady=6)

        # Check if All Students data is loaded
        all_students = self.system.all_students_list
        if not all_students:
            lbl = tk.Label(attendance_frame, 
                          text="⚠️ 'All Students' file not loaded!\n\nPlease upload 'All Students' file in the Settings tab.", 
                          bg=self.colors["bg_white"], fg=self.colors["danger"], font=('Segoe UI', 12))
            lbl.pack(pady=40)
            return

        # Get all students who are enrolled in any course (from attendance)
        enrolled_students = set()
        for course in self.system.courses:
            for student in course.students:
                enrolled_students.add(student)

        # Calculate stats
        enrolled_count = len(enrolled_students)
        not_enrolled_count = len(all_students) - len(enrolled_students & all_students)
        students_in_all = all_students
        
        # Header
        hdr = tk.Frame(attendance_frame, bg="#cfd8dc")
        hdr.pack(fill='x', padx=5, pady=(6,0))
        
        lbl = tk.Label(hdr, text=f"📋 All Students Overview | Total: {len(all_students)} students", 
                      bg="#cfd8dc", fg=self.colors["text_header"], font=('Segoe UI', 12, 'bold'))
        lbl.pack(side='left', padx=6, pady=6)

        # Summary stats
        stats_frame = tk.Frame(attendance_frame, bg=self.colors["bg_white"])
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        enrolled_in_all = enrolled_students & all_students
        not_enrolled_in_all = all_students - enrolled_students
        
        stats_text = f"✓ Enrolled in Exams: {len(enrolled_in_all)}  |  ✗ No Exam Enrollment: {len(not_enrolled_in_all)}"
        stats_lbl = tk.Label(stats_frame, text=stats_text, bg=self.colors["bg_white"], 
                            fg=self.colors["text_body"], font=('Segoe UI', 10))
        stats_lbl.pack(side='left')

        # Student list table with scrollbar
        tbl_container = tk.Frame(attendance_frame, bg=self.colors["bg_white"])
        tbl_container.pack(fill='both', expand=True, padx=10, pady=8)

        cols = ["Student ID", "Enrolled Courses", "Exam Count", "Status"]
        
        scrollbar = ttk.Scrollbar(tbl_container, orient="vertical")
        tbl = ttk.Treeview(tbl_container, columns=cols, show='headings', 
                          yscrollcommand=scrollbar.set, height=20)
        scrollbar.config(command=tbl.yview)
        
        for c in cols:
            tbl.heading(c, text=c)
        tbl.column("Student ID", width=180, anchor='center')
        tbl.column("Enrolled Courses", width=350, anchor='w')
        tbl.column("Exam Count", width=100, anchor='center')
        tbl.column("Status", width=150, anchor='center')

        # Populate table with all students
        students_sorted = sorted(all_students)
        for student_id in students_sorted:
            # Find courses this student is enrolled in
            student_courses = []
            for course in self.system.courses:
                if student_id in course.students:
                    student_courses.append(course.code)
            
            exam_count = len(student_courses)
            if exam_count > 0:
                courses_str = ", ".join(sorted(student_courses)[:3])
                if len(student_courses) > 3:
                    courses_str += f" (+{len(student_courses) - 3} more)"
                status = f"✓ {exam_count} Exam(s)"
                status_tag = "enrolled"
            else:
                courses_str = "No enrollment"
                status = "✗ No Exam"
                status_tag = "not_enrolled"
            
            tbl.insert('', 'end', values=(student_id, courses_str, exam_count, status), tags=(status_tag,))
        
        # Configure row colors
        tbl.tag_configure("enrolled", background="#e8f5e9")  # light green
        tbl.tag_configure("not_enrolled", background="#ffebee")  # light red

        scrollbar.pack(side='right', fill='y')
        tbl.pack(side='left', fill='both', expand=True)
        
        try:
            tbl.yview_moveto(0)
        except Exception:
            pass