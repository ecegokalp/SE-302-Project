# db.py
import sqlite3


class DB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as con:
            cur = con.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS classrooms (
                    slot INTEGER NOT NULL,
                    code TEXT NOT NULL,
                    capacity INTEGER NOT NULL,
                    PRIMARY KEY (slot, code)
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    slot INTEGER NOT NULL,
                    code TEXT NOT NULL,
                    PRIMARY KEY (slot, code)
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS course_students (
                    slot INTEGER NOT NULL,
                    course_code TEXT NOT NULL,
                    student_id TEXT NOT NULL,
                    PRIMARY KEY (slot, course_code, student_id)
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    slot INTEGER NOT NULL,
                    id TEXT NOT NULL,
                    PRIMARY KEY (slot, id)
                )
            """)

            con.commit()

    # ---------- CLEAR SLOT ----------
    def clear_slot(self, slot: int):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("DELETE FROM classrooms WHERE slot=?", (slot,))
            cur.execute("DELETE FROM courses WHERE slot=?", (slot,))
            cur.execute("DELETE FROM course_students WHERE slot=?", (slot,))
            cur.execute("DELETE FROM students WHERE slot=?", (slot,))
            con.commit()

    # ---------- CLASSROOMS ----------
    def save_classrooms(self, slot: int, classrooms):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("DELETE FROM classrooms WHERE slot=?", (slot,))
            cur.executemany(
                "INSERT INTO classrooms(slot, code, capacity) VALUES (?,?,?)",
                [(slot, code, cap) for code, cap in classrooms]
            )
            con.commit()

    def load_classrooms(self, slot: int):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT code, capacity FROM classrooms WHERE slot=? ORDER BY code",
                (slot,)
            )
            return cur.fetchall()

    # ---------- COURSES + STUDENTS ----------
    def save_courses_and_students(self, slot: int, courses):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("DELETE FROM courses WHERE slot=?", (slot,))
            cur.execute("DELETE FROM course_students WHERE slot=?", (slot,))

            cur.executemany(
                "INSERT INTO courses(slot, code) VALUES (?,?)",
                [(slot, code) for code, _ in courses]
            )

            rows = []
            for code, students in courses:
                for sid in students:
                    rows.append((slot, code, sid))

            if rows:
                cur.executemany(
                    "INSERT INTO course_students(slot, course_code, student_id) VALUES (?,?,?)",
                    rows
                )
            con.commit()

    def load_courses_with_students(self, slot: int):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT code FROM courses WHERE slot=? ORDER BY code", (slot,))
            course_codes = [r[0] for r in cur.fetchall()]

            result = []
            for code in course_codes:
                cur.execute("""
                    SELECT student_id FROM course_students
                    WHERE slot=? AND course_code=?
                    ORDER BY student_id
                """, (slot, code))
                students = [r[0] for r in cur.fetchall()]
                result.append((code, students))
            return result

    # ---------- STUDENTS ----------
    def save_students(self, slot: int, students):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("DELETE FROM students WHERE slot=?", (slot,))
            cur.executemany(
                "INSERT INTO students(slot, id) VALUES (?,?)",
                [(slot, sid) for sid in sorted(students)]
            )
            con.commit()

    def load_students(self, slot: int):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT id FROM students WHERE slot=? ORDER BY id", (slot,))
            return [r[0] for r in cur.fetchall()]

    # ---------- INFO ----------
    def get_slot_counts(self, slot: int):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT COUNT(*) FROM classrooms WHERE slot=?", (slot,))
            cls = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM courses WHERE slot=?", (slot,))
            crs = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM students WHERE slot=?", (slot,))
            sts = cur.fetchone()[0]
            return cls, crs, sts

    def get_slot_snapshot(self, slot: int):
        """
        Returns a structured snapshot of one slot in DB:
          classrooms: {code: capacity}
          students: set([...])
          courses: {course_code: set(student_ids)}
        """
        cls = self.load_classrooms(slot)  # list[(code, capacity)]
        students = self.load_students(slot)  # list[id]
        crs = self.load_courses_with_students(slot)  # list[(course_code, [student_ids])]

        return {
            "classrooms": {code: cap for code, cap in cls},
            "students": set(students),
            "courses": {code: set(studs) for code, studs in crs},
        }

