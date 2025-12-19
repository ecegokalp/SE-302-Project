class Course:
    def __init__(self, code, student_ids=None, duration=None):
        self.code = code
        self.students = list(set(student_ids or []))
        # duration in minutes. Defaults to 120 (2 hours) if not specified.
        self.duration = int(duration) if duration is not None else 120

    def __repr__(self):
        return f"{self.code} ({len(self.students)})"

class Classroom:
    def __init__(self, code, capacity):
        self.code = code
        self.capacity = int(capacity)

    def __repr__(self):
        return f"{self.code} [{self.capacity}]"