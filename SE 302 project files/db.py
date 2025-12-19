# db.py
import sqlite3
from typing import List, Tuple


class DB:
    def __init__(self, path: str = "examtable.db"):
        self.path = path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.path)

    def _init_db(self):
        with self._connect() as con:
            cur = con.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS classrooms(
                    code TEXT PRIMARY KEY,
                    capacity INTEGER NOT NULL
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS courses(
                    code TEXT PRIMARY KEY
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS course_students(
                    course_code TEXT NOT NULL,
                    student_id TEXT NOT NULL,
                    PRIMARY KEY(course_code, student_id),
                    FOREIGN KEY(course_code) REFERENCES courses(code)
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS students(
                    id TEXT PRIMARY KEY
                )
            """)

            # İsteğe bağlı: schedule’ı DB’ye basmak istersen
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schedule(
                    course_code TEXT PRIMARY KEY,
                    day INTEGER NOT NULL,
                    slot INTEGER NOT NULL,
                    rooms TEXT NOT NULL,
                    FOREIGN KEY(course_code) REFERENCES courses(code)
                )
            """)

            con.commit()

    # ---------- SAVE ----------
    def save_classrooms(self, classrooms: List[Tuple[str, int]]):
        with self._connect() as con:
            cur = con.cursor()
            cur.executemany(
                "INSERT OR REPLACE INTO classrooms(code, capacity) VALUES(?,?)",
                classrooms
            )
            con.commit()

    def save_courses_and_students(self, courses: List[Tuple[str, List[str]]]):
        with self._connect() as con:
            cur = con.cursor()

            # courses
            cur.executemany(
                "INSERT OR REPLACE INTO courses(code) VALUES(?)",
                [(c,) for c, _ in courses]
            )

            # relation table
            cur.execute("DELETE FROM course_students")
            rows = []
            for c, studs in courses:
                for sid in set(studs):
                    rows.append((c, sid))

            cur.executemany(
                "INSERT OR REPLACE INTO course_students(course_code, student_id) VALUES(?,?)",
                rows
            )
            con.commit()

    def save_students(self, students):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("DELETE FROM students")
            cur.executemany(
                "INSERT INTO students(id) VALUES(?)",
                [(s,) for s in students]
            )
            con.commit()

    # ---------- LOAD ----------
    def load_classrooms(self) -> List[Tuple[str, int]]:
        with self._connect() as con:
            cur = con.cursor()
            return cur.execute(
                "SELECT code, capacity FROM classrooms ORDER BY code"
            ).fetchall()

    def load_students(self) -> List[str]:
        with self._connect() as con:
            cur = con.cursor()
            rows = cur.execute("SELECT id FROM students ORDER BY id").fetchall()
            return [r[0] for r in rows]

    def load_courses_with_students(self) -> List[Tuple[str, List[str]]]:
        with self._connect() as con:
            cur = con.cursor()
            courses = [r[0] for r in cur.execute("SELECT code FROM courses ORDER BY code").fetchall()]

            result = []
            for c in courses:
                studs = [r[0] for r in cur.execute(
                    "SELECT student_id FROM course_students WHERE course_code=? ORDER BY student_id",
                    (c,)
                ).fetchall()]
                result.append((c, studs))

            return result
