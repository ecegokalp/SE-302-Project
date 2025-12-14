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

    matches = re.findall(r"(Classroom_\d+)\D+(\d+)", content)
    for name, cap in matches:
        classrooms.append(Classroom(name, cap))

    return classrooms

def read_courses_from_file(filepath):
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
    current_code = None
    for line in lines:
        line = line.strip()
        if not line:
            continue

        course_match = re.search(r"(CourseCode_\d+)", line)
        if course_match:
            current_code = course_match.group(1)
            continue

        students_in_line = re.findall(r"(Std_ID_\d+)", line)
        if current_code and students_in_line:
            courses.append(Course(current_code, students_in_line))
            current_code = None

    return courses

def read_students_from_file(filepath):
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