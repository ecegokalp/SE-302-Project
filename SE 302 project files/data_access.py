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
      SE 302
      MATH 101;90
      CS 210 120
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
        
        # Skip common header patterns
        if line.upper().startswith('ALL OF THE') or line.startswith('#'):
            continue
        
        # Check if there's a semicolon-separated duration
        duration = None
        code = line
        
        if ';' in line:
            parts = line.split(';', 1)
            code = parts[0].strip()
            if len(parts) > 1 and parts[1].strip().isdigit():
                duration = int(parts[1].strip())
        
        if code:
            courses.append(Course(code, [], duration))
    return courses


def read_attendance_from_file(filepath):
    """
    Reads attendance lists where a course code line is followed by
    one or more lines containing student ids like ['Std_ID_001', 'Std_ID_002'] or
    plain lists. Course codes can be in any format (e.g., "SE 302", "MATH 101", "CourseCode_01").
    Returns Course objects populated with student lists.
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
    current_duration = None

    for line in lines:
        line = line.strip()
        if not line: continue

        # If line contains student IDs, it's a student list
        if "Std_ID_" in line:
            if current_code:
                students_in_line = re.findall(r"(Std_ID_\d+)", line)
                if students_in_line:
                    existing = next((c for c in courses if c.code == current_code), None)
                    if existing:
                        existing.students.extend(students_in_line)
                        existing.students = list(set(existing.students))
                        # Update duration if specified
                        if current_duration is not None:
                            existing.duration = current_duration
                    else:
                        courses.append(Course(current_code, students_in_line, current_duration))
        else:
            # This line doesn't contain student IDs, so it's a course code line
            # Skip common header patterns
            if line.upper().startswith('ALL OF THE') or line.startswith('#'):
                continue
            
            # Parse course code and optional duration
            current_duration = None
            current_code = line
            
            # Check if there's a semicolon or colon-separated duration
            if ';' in line or ':' in line:
                # Try semicolon first
                sep = ';' if ';' in line else ':'
                parts = line.split(sep, 1)
                current_code = parts[0].strip()
                if len(parts) > 1 and parts[1].strip().isdigit():
                    current_duration = int(parts[1].strip())
            
            current_code = current_code.strip()

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