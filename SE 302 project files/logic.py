import threading
import time
import random
from collections import defaultdict
import data_access
import os
from db import DB
from models import Course, Classroom




class ScheduleSystem:
    def __init__(self):
        self.reset_data()
        db_path = os.path.join(os.path.dirname(__file__), "examtable.db")
        self.db = DB(db_path)

    def reset_data(self):
        self.courses = []
        self.classrooms = []
        self.all_students_list = set()

        self.num_days = 7
        self.slots_per_day = 4
        self.slot_duration_minutes = 60  # Default slot duration in minutes (can be set from GUI)

        self.assignments = {}
        self.student_room_map = {}

        self.room_schedule = defaultdict(set)
        self.conflict_matrix = defaultdict(set)

        self.room_usage_count = defaultdict(int)
        self.slot_usage_count = defaultdict(int)

        self.iteration_count = 0
        self.MAX_ITERATIONS = 200_000

        self.stop_event = threading.Event()
        self.deadline = None

        self.progress_callback = None  # GUI için

    # ---------------- FILE LOADERS ----------------
    def load_classrooms_regex(self, filepath):
        try:
            self.classrooms = data_access.read_classrooms_from_file(filepath)
            return f"SUCCESS: {len(self.classrooms)} classrooms."
        except Exception as e:
            return f"ERROR: {e}"

    def load_courses_regex(self, filepath):
        try:
            # Load optional courses file (may include durations). These Course objects
            # will usually have empty student lists; attendance upload is the primary
            # way to populate student lists.
            loaded = data_access.read_courses_from_file(filepath)
            # Merge or replace existing course entries' duration info
            for c in loaded:
                existing = next((x for x in self.courses if x.code == c.code), None)
                if existing:
                    if c.duration is not None:
                        existing.duration = c.duration
                else:
                    # keep as course with no students (attendance may be loaded later)
                    self.courses.append(c)
            return f"SUCCESS: {len(loaded)} courses (durations optional)."
        except Exception as e:
            return f"ERROR: {e}"

    def load_attendance_regex(self, filepath):
        try:
            # Attendance file is mandatory for scheduling: it provides per-course student lists
            loaded = data_access.read_attendance_from_file(filepath)
            # Merge durations from any previously loaded simple courses
            for c in loaded:
                existing = next((x for x in self.courses if x.code == c.code), None)
                if existing and getattr(existing, 'duration', None) is not None:
                    c.duration = existing.duration
            # replace current courses with loaded attendance data
            self.courses = loaded
            return f"SUCCESS: {len(self.courses)} attendance entries loaded."
        except Exception as e:
            return f"ERROR: {e}"

    def load_all_students_regex(self, filepath):
        try:
            self.all_students_list = data_access.read_students_from_file(filepath)
            return f"SUCCESS: {len(self.all_students_list)} students."
        except Exception as e:
            return f"ERROR: {e}"

    # ---------------- CONTROL ----------------
    def stop(self):
        self.stop_event.set()

    def set_progress_callback(self, func):
        """
        func(iteration_count, elapsed_time)
        """
        self.progress_callback = func

    # --------------- MULTI-SLOT DURATION HELPERS ----------------
    def get_slots_needed(self, course):
        """
        Calculate how many consecutive slots are needed for an exam.
        If exam duration > slot duration, multiple slots are needed.
        If exam duration < slot duration, it occupies 1 slot (with unused time).
        """
        import math
        return max(1, math.ceil(course.duration / self.slot_duration_minutes))

    # ---- VALIDATION ----------------
    def validate_feasibility(self):
        # Account for multi-slot exams when computing total slot availability
        total_time_slots = self.num_days * self.slots_per_day
        total_capacity = sum(r.capacity for r in self.classrooms)
        
        # Sum of (students per exam * slots needed per exam)
        total_slot_demand = sum(len(c.students) * self.get_slots_needed(c) for c in self.courses)
        
        if total_slot_demand > total_time_slots * total_capacity:
            return False, "IMPOSSIBLE: capacity insufficient for exam durations"
        return True, "OK"

    def build_conflict_matrix(self):
        self.conflict_matrix.clear()
        for i in range(len(self.courses)):
            for j in range(i + 1, len(self.courses)):
                if not set(self.courses[i].students).isdisjoint(self.courses[j].students):
                    self.conflict_matrix[self.courses[i].code].add(self.courses[j].code)
                    self.conflict_matrix[self.courses[j].code].add(self.courses[i].code)

    # ---- CONSTRAINTS ----------------
    def check_constraints(self, course, day, slot, student_agenda):
        """
        Check if a course can be assigned to a specific starting slot on a day.
        The exam spans multiple slots if needed.
        Respects:
          - No back-to-back exams (adjacent slots)
          - Max 2 exams per student per day
          - No overlapping exams
        """
        slots_needed = self.get_slots_needed(course)
        
        # Verify all needed slots fit within the day
        if slot + slots_needed > self.slots_per_day:
            return False
        
        # New exam occupies slots [slot, slot + slots_needed)
        new_exam_slots = set(range(slot, slot + slots_needed))
        
        # Check for student conflicts across all slots this exam will occupy
        for student in course.students:
            exam_list = student_agenda[student][day]
            
            # exam_list now contains tuples: (start_slot, num_slots)
            # Student can have at most 1 other exam on the same day
            if len(exam_list) >= 2:
                return False
            
            # Check no overlap or adjacency with existing exams
            for existing_start, existing_slots in exam_list:
                existing_slots_set = set(range(existing_start, existing_start + existing_slots))
                
                # Check overlap
                if new_exam_slots & existing_slots_set:
                    return False
                
                # Check adjacency (no back-to-back): must have gap of at least 1 slot
                existing_end = existing_start + existing_slots - 1
                new_end = slot + slots_needed - 1
                
                # Back-to-back means the exams touch or are 1 slot apart
                if abs(existing_start - new_end) <= 1 or abs(slot - existing_end) <= 1:
                    return False
        
        return True

    # ---- ROOMS ----------------
    def find_rooms(self, course, day, slot):
        """Find classrooms for the course. Rooms must be available for all slots the exam occupies."""
        slots_needed = self.get_slots_needed(course)
        
        # Check which rooms are available for all slots this exam needs
        available = []
        for r in self.classrooms:
            available_for_all = True
            for s in range(slot, slot + slots_needed):
                if r.code in self.room_schedule[(day, s)]:
                    available_for_all = False
                    break
            if available_for_all:
                available.append(r)

        available.sort(key=lambda r: (self.room_usage_count[r.code], -r.capacity))

        selected, cap = [], 0
        for r in available:
            selected.append(r)
            cap += r.capacity
            if cap >= len(course.students):
                return selected
        return None

    # ---- DISTRIBUTION ----------------
    def distribute_students(self):
        self.student_room_map.clear()

        for c_code, (d, s, rooms) in self.assignments.items():
            course = next((c for c in self.courses if c.code == c_code), None)
            if not course:
                continue

            idx = 0
            for room in rooms:
                for _ in range(room.capacity):
                    if idx >= len(course.students):
                        break
                    self.student_room_map[(course.students[idx], c_code)] = room.code
                    idx += 1

    # ---------------- SOLVER ----------------
    def solve(self, time_limit_sec=10):
        try:
            self.stop_event.clear()
            self.iteration_count = 0
            self.deadline = time.time() + time_limit_sec

            self.assignments.clear()
            self.room_schedule.clear()
            self.room_usage_count.clear()
            self.slot_usage_count.clear()

            if not self.courses:
                return False, "No Data"

            feasible, msg = self.validate_feasibility()
            if not feasible:
                return False, msg

            self.build_conflict_matrix()

            random.shuffle(self.courses)
            courses = sorted(
                self.courses,
                key=lambda c: (len(c.students), len(self.conflict_matrix[c.code])),
                reverse=True
            )

            student_agenda = defaultdict(lambda: defaultdict(list))
            start = time.time()

            success = self._backtrack(courses, 0, student_agenda, start)

            if success:
                self.distribute_students()
                return True, f"Found Solution ({round(time.time()-start,2)} s)"

            if self.stop_event.is_set():
                return False, "Stopped (timeout / user)"

            reasons = []

            if self.num_days * self.slots_per_day < len(self.courses):
                reasons.append("Not enough time slots")

            if any(len(c.students) > sum(r.capacity for r in self.classrooms) for c in self.courses):
                reasons.append("Some courses exceed classroom capacity")

            if not reasons:
                reasons.append("High student conflict density")

            return False, "No Solution Found.\nReasons:\n- " + "\n- ".join(reasons)


        except Exception as e:
            return False, f"CRASH PREVENTED: {e}"

    def save_data_to_db(self):
        # classrooms
        cls = [(r.code, r.capacity) for r in self.classrooms]
        self.db.save_classrooms(cls)

        # courses + course_students
        crs = [(c.code, c.students) for c in self.courses]
        self.db.save_courses_and_students(crs)

        # students (AYRI TABLO)
        if self.all_students_list:
            self.db.save_students(self.all_students_list)

    def load_data_from_db(self):
        # classrooms
        cls = self.db.load_classrooms()
        self.classrooms = [Classroom(code, cap) for code, cap in cls]

        # students
        students = self.db.load_students()
        self.all_students_list = set(students)

        # courses + students
        crs = self.db.load_courses_with_students()
        self.courses = [Course(code, studs) for code, studs in crs]

    def _backtrack(self, course_list, index, student_agenda, start_time):
        if self.stop_event.is_set():
            return False

        if time.time() > self.deadline:
            self.stop_event.set()
            return False

        self.iteration_count += 1
        if self.iteration_count > self.MAX_ITERATIONS:
            return False

        if self.progress_callback and self.iteration_count % 500 == 0:
            self.progress_callback(self.iteration_count, time.time() - start_time)

        if index == len(course_list):
            return True

        course = course_list[index]
        slots_needed = self.get_slots_needed(course)
        slots = [(d, s) for d in range(self.num_days) for s in range(self.slots_per_day - slots_needed + 1)]
        slots.sort(key=lambda x: self.slot_usage_count[x])

        for d, s in slots:
            if not self.check_constraints(course, d, s, student_agenda):
                continue

            rooms = self.find_rooms(course, d, s)
            if not rooms:
                continue

            self.assignments[course.code] = (d, s, rooms)
            
            # Mark all slots occupied by this multi-slot exam
            for slot_offset in range(slots_needed):
                self.slot_usage_count[(d, s + slot_offset)] += 1

            for r in rooms:
                for slot_offset in range(slots_needed):
                    self.room_schedule[(d, s + slot_offset)].add(r.code)
                self.room_usage_count[r.code] += slots_needed

            for st in course.students:
                student_agenda[st][d].append((s, slots_needed))

            if self._backtrack(course_list, index + 1, student_agenda, start_time):
                return True

            del self.assignments[course.code]
            for slot_offset in range(slots_needed):
                self.slot_usage_count[(d, s + slot_offset)] -= 1
            for r in rooms:
                for slot_offset in range(slots_needed):
                    self.room_schedule[(d, s + slot_offset)].remove(r.code)
                self.room_usage_count[r.code] -= slots_needed
            for st in course.students:
                student_agenda[st][d].remove((s, slots_needed))
