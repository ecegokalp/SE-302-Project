class Course:
    def __init__(self, code, student_ids):
        self.code = code
        self.students = list(set(student_ids))

    def __repr__(self):
        return f"{self.code} ({len(self.students)})"

class Classroom:
    def __init__(self, code, capacity):
        self.code = code
        self.capacity = int(capacity)

    def __repr__(self):
        return f"{self.code} [{self.capacity}]"