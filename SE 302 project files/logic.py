# logic.py
import threading
import time
import random
from collections import defaultdict
import data_access

class ScheduleSystem:
    def __init__(self):
        self.reset_data()

    def reset_data(self):
        self.courses = []
        self.classrooms = []
        self.all_students_list = set()

        # Parametreler
        self.num_days = 7
        self.slots_per_day = 5
        self.timeout_seconds = 300

        self.assignments = {}
        self.student_room_map = {}
        self.room_schedule = defaultdict(set)
        self.stop_event = threading.Event()
        self.conflict_matrix = defaultdict(set)
        self.room_usage_count = defaultdict(int)
        self.slot_usage_count = defaultdict(int)


    def load_classrooms_regex(self, filepath):
        self.classrooms = data_access.read_classrooms_from_file(filepath)
        if self.classrooms:
            return f"BAŞARILI: {len(self.classrooms)} sınıf kapasitesi."
        return "HATA: Sınıf bulunamadı."

    def load_courses_regex(self, filepath):
        self.courses = data_access.read_courses_from_file(filepath)
        if self.courses:
            return f"BAŞARILI: {len(self.courses)} ders."
        return "HATA: Ders bulunamadı."

    def load_all_students_regex(self, filepath):
        self.all_students_list = data_access.read_students_from_file(filepath)
        if self.all_students_list:
            return f"BAŞARILI: {len(self.all_students_list)} öğrenci."
        return "HATA: Liste boş."

    # --- MANTIK ---
    def build_conflict_matrix(self):
        self.conflict_matrix.clear()
        n = len(self.courses)
        for i in range(n):
            for j in range(i + 1, n):
                if not set(self.courses[i].students).isdisjoint(set(self.courses[j].students)):
                    self.conflict_matrix[self.courses[i].code].add(self.courses[j].code)
                    self.conflict_matrix[self.courses[j].code].add(self.courses[i].code)

    def check_student_constraints(self, course, day, slot, student_agenda):
        for student in course.students:
            if student not in student_agenda:
                continue

            # max 2 exams in a day for each student
            exams_today = sum(1 for (d, s) in student_agenda[student] if d == day)
            if exams_today >= 2:
                return False

            # consecutive slot control for each student
            for (d, s) in student_agenda[student]:
                if d == day and abs(s - slot) == 1:
                    return False
        return True

    def find_rooms_for_course(self, course, day, slot):
        used_rooms = self.room_schedule[(day, slot)]
        available = [r for r in self.classrooms if r.code not in used_rooms]

        available.sort(key=lambda r: (
            self.room_usage_count[r.code] / max(r.capacity, 1),
            -r.capacity
        ))

        needed = len(course.students)
        selected = []
        current_cap = 0

        for room in available:
            selected.append(room)
            current_cap += room.capacity
            if current_cap >= needed:
                return selected
        return None

    def distribute_students_to_rooms(self):
        self.student_room_map = {}
        for c_code, (d, s, rooms) in self.assignments.items():
            course_obj = next((c for c in self.courses if c.code == c_code), None)
            if not course_obj: continue

            students_to_seat = list(course_obj.students)
            student_idx = 0

            for room in rooms:
                remaining_students = len(students_to_seat) - student_idx
                take_count = min(room.capacity, remaining_students)
                seated_students = students_to_seat[student_idx : student_idx + take_count]
                student_idx += take_count

                for student_id in seated_students:
                    self.student_room_map[(student_id, c_code)] = room.code

                if student_idx >= len(students_to_seat): break

    def solve(self):
        self.assignments = {}
        self.room_schedule = defaultdict(set)
        self.student_room_map = {}
        self.room_usage_count = defaultdict(int)
        self.slot_usage_count = defaultdict(int)
        self.stop_event.clear()

        if not self.courses: return False, "Veri yok!"

        self.build_conflict_matrix()

        
        sorted_courses = sorted(
            self.courses,
            key=lambda c: (len(self.conflict_matrix[c.code]), len(c.students)),
            reverse=True
        )

        student_agenda = defaultdict(list)
        start_time = time.time()

        if self._backtrack(sorted_courses, 0, student_agenda, start_time):
            self.distribute_students_to_rooms()
            return True, f"Tamamlandı! ({round(time.time() - start_time, 2)} sn)"
        elif self.stop_event.is_set():
            return False, "Süre Yetersiz (Timeout)."
        else:
            return False, "Çözüm YOK. Gün/slot sayısını artırın."

    def _backtrack(self, course_list, index, student_agenda, start_time):
        if index % 10 == 0:
            if time.time() - start_time > self.timeout_seconds:
                self.stop_event.set()
                return False
            if self.stop_event.is_set(): return False

        if index == len(course_list): return True

        course = course_list[index]
        days_to_try = list(range(self.num_days))
        slots_to_try = list(range(self.slots_per_day))

        all_slots = [(d, s) for d in days_to_try for s in slots_to_try]

        all_slots.sort(key=lambda x: (self.slot_usage_count[x], random.random()))

        slot_order = all_slots

        for (d, s) in slot_order:
            if not self.check_student_constraints(course, d, s, student_agenda):
                continue

            selected_rooms = self.find_rooms_for_course(course, d, s)

            if selected_rooms:
                self.assignments[course.code] = (d, s, selected_rooms)
                self.slot_usage_count[(d, s)] += 1

                for r in selected_rooms:
                    self.room_schedule[(d, s)].add(r.code)
                    self.room_usage_count[r.code] += 1

                for student in course.students: student_agenda[student].append((d, s))

                if self._backtrack(course_list, index + 1, student_agenda, start_time): return True

                del self.assignments[course.code]
                self.slot_usage_count[(d, s)] -= 1

                for r in selected_rooms:
                    self.room_schedule[(d, s)].remove(r.code)
                    self.room_usage_count[r.code] -= 1

                for student in course.students:
                    student_agenda[student].remove((d, s))
                    if not student_agenda[student]: del student_agenda[student]

        return False