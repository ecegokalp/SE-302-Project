import re
from models import Course, Classroom

def read_classrooms_from_file(filepath):
    classrooms = []
    content = ""
    for enc in ['utf-8', 'cp1254', 'latin-1']:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
                break
        except:
            continue

    matches = re.findall(r"(Classroom_\d+)[^0-9]+(\d+)", content)
    for name, cap in matches:
        classrooms.append(Classroom(name, cap))

    return classrooms

def read_courses_from_file(filepath):
    """
    Reads a simple courses file containing one course code per line optionally
    followed by a separator and duration in minutes. Example lines:
      CourseCode_01
      CourseCode_02;90
    Returns a list of Course objects with empty student lists and optional durations.
    """
    courses = []
    content = ""
    for enc in ['utf-8', 'cp1254', 'latin-1']:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
                break
        except:
            continue

    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if not line: continue
        # Accept separators ; , or whitespace
        parts = re.split(r'[;,\s]+', line)
        code = next((p for p in parts if 'CourseCode_' in p), None)
        if code:
            # try to find a numeric duration
            duration = None
            for p in parts:
                if p.isdigit():
                    duration = int(p)
                    break
            courses.append(Course(code.strip(), [], duration))
    return courses


def read_attendance_from_file(filepath):
    """
    Reads attendance lists where a course code line (CourseCode_XX) is followed by
    one or more lines containing student ids like ['Std_ID_001', 'Std_ID_002'] or
    plain lists. Returns Course objects populated with student lists.
    """
    courses = []
    content = ""
    for enc in ['utf-8', 'cp1254', 'latin-1']:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
                break
        except:
            continue

    # Satır satır oku
    lines = content.split('\n')
    current_code = None

    for line in lines:
        line = line.strip()
        if not line: continue

        # Ders kodunu bul (Örn: CourseCode_01)
        if "CourseCode_" in line:
            parts = re.split(r'[;:,\s]+', line)
            for p in parts:
                if "CourseCode_" in p:
                    current_code = p.strip()
            continue

        # Öğrencileri bul (Std_ID_01)
        if current_code and "Std_ID_" in line:
            students_in_line = re.findall(r"(Std_ID_\d+)", line)
            if students_in_line:
                existing = next((c for c in courses if c.code == current_code), None)
                if existing:
                    existing.students.extend(students_in_line)
                    existing.students = list(set(existing.students))
                else:
                    courses.append(Course(current_code, students_in_line))

    return courses

def read_students_from_file(filepath):
    # Bu sadece istatistik için, hesaplamada kritik değil
    all_students_list = set()
    content = ""
    for enc in ['utf-8', 'cp1254', 'latin-1']:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
                break
        except:
            continue

    matches = re.findall(r"(Std_ID_\d+)", content)
    for s_id in matches:
        all_students_list.add(s_id)

    return all_students_list