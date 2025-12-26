import json
import random

# Load data
with open('students.json', 'r') as f:
    students = json.load(f)

with open('courses.json', 'r') as f:
    courses = json.load(f)

# Course limits and current enrollments
course_limits = {c['course_id']: c['max_students'] for c in courses}
current_enrollments = {cid: 0 for cid in course_limits}

for s in students:
    for cid in s['registered_courses']:
        if cid in current_enrollments:
            current_enrollments[cid] += 1

course_ids = list(course_limits.keys())

# Assign 2 courses per student, keeping existing and checking limits
for s in students:
    current = s['registered_courses']
    available = [cid for cid in course_ids if cid not in current and current_enrollments[cid] < course_limits[cid]]
    num_to_add = min(2 - len(current), len(available))
    if num_to_add > 0:
        new_courses = random.sample(available, num_to_add)
        s['registered_courses'].extend(new_courses)
        for cid in new_courses:
            current_enrollments[cid] += 1

# Save updated students.json
with open('students.json', 'w') as f:
    json.dump(students, f, indent=4)

print("Students assigned to courses randomly and reasonably.")
