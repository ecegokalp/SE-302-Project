class Course:
    def __init__(self, code, student_ids=None, duration=None):
        self.code = code
        self.students = list(set(student_ids or []))
        # duration in minutes. Defaults to None (will use slot duration)
        # _explicit_duration tracks if duration was explicitly set in course file
        self._explicit_duration = duration is not None
        self.duration = int(duration) if duration is not None else 60  # Default to 60 min if not specified

    def __repr__(self):
        return f"{self.code} ({len(self.students)})"

class Classroom:
    def __init__(self, code, capacity):
        self.code = code
        self.capacity = int(capacity)

    def __repr__(self):
        return f"{self.code} [{self.capacity}]"