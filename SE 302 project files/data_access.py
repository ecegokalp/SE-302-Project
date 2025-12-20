import re
from models import Course, Classroom

def read_classrooms_from_file(filepath):
    """
    Reads classrooms from a file where each line contains a classroom code
    followed by its capacity. Supports flexible naming (e.g., "M201;40", "C203 50").
    Returns a list of Classroom objects.
    """
    classrooms = []
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
        if not line:
            continue
        
        # Skip common header patterns
        if line.upper().startswith('ALL OF THE') or line.startswith('#'):
            continue
        
        # Parse classroom code and capacity
        # Format: "ClassroomCode;Capacity" or "ClassroomCode Capacity"
        # Check for semicolon or colon separator first
        if ';' in line or ':' in line:
            sep = ';' if ';' in line else ':'
            parts = line.split(sep, 1)
            code = parts[0].strip()
            capacity = parts[1].strip() if len(parts) > 1 else None
        else:
            # Try splitting by whitespace
            parts = line.split()
            if len(parts) >= 2:
                # Last part should be capacity if it's numeric
                if parts[-1].isdigit():
                    capacity = parts[-1]
                    code = ' '.join(parts[:-1])
                else:
                    # No clear capacity, use whole line as code
                    code = line
                    capacity = None
            else:
                code = line
                capacity = None
        
        if code and capacity and capacity.isdigit():
            classrooms.append(Classroom(code, capacity))

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
    one or more lines containing student ids in list format: ['ID1', 'ID2', ...]
    Course codes can be in any format (e.g., "SE 302", "MATH 101", "CourseCode_01").
    Student IDs can be in any format (e.g., "Std_ID_001", "20210702", etc.).
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

        # Check if line contains a list structure with student IDs
        # Format: ['...', '...', ...] or similar
        if '[' in line and ']' in line:
            if current_code:
                # Extract all items from the list
                # Match anything inside quotes within brackets
                students_in_line = re.findall(r"['\"]([^'\"]+)['\"]", line)
                
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
    """
    Reads all student IDs from a file. Supports two formats:
    1. Line-by-line: Each line contains one student ID
    2. List format: ['ID1', 'ID2', ...]
    Supports any ID format (e.g., "Std_ID_001", "20210702", etc.).
    This is mainly for statistics, not critical for scheduling.
    """
    all_students_list = set()
    content = ""
    for enc in ['utf-8', 'cp1254', 'latin-1']:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
                break
        except:
            continue

    # First, try to extract from list structures ['...', '...']
    list_matches = re.findall(r"['\"]([^'\"]+)['\"]", content)
    if list_matches:
        for s_id in list_matches:
            all_students_list.add(s_id)
    else:
        # If no list format found, try line-by-line format
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            # Skip empty lines and common headers
            if not line or line.upper().startswith('ALL OF THE') or line.startswith('#'):
                continue
            # Each non-empty line is a student ID
            all_students_list.add(line)

    return all_students_list