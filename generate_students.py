import json
import random
from datetime import datetime

def calculate_grade(marks):
    if marks >= 90:
        return "A"
    elif marks >= 80:
        return "B"
    elif marks >= 70:
        return "C"
    elif marks >= 60:
        return "D"
    else:
        return "F"

# Fake names
first_names = ["John", "Jane", "Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Henry",
               "Ivy", "Jack", "Kate", "Liam", "Mia", "Noah", "Olivia", "Peter", "Quinn", "Ryan",
               "Sophia", "Tyler", "Uma", "Victor", "Wendy", "Xander", "Yara", "Zoe", "Aaron", "Bella",
               "Caleb", "Daisy", "Ethan", "Fiona", "Gabriel", "Hannah", "Isaac", "Julia", "Kevin", "Lily",
               "Mason", "Nora", "Owen", "Piper", "Quinn", "Riley", "Samuel", "Tessa", "Ulysses", "Violet",
               "William", "Xena", "Yusuf", "Zara", "Adam", "Beth", "Carter", "Diana", "Eli", "Faith"]

last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
              "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
              "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
              "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts",
              "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker", "Cruz", "Edwards", "Collins", "Reyes"]

students = []
for i in range(1, 71):
    roll_no = f"S{i:03d}"
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    name = f"{first_name} {last_name}"
    marks = round(random.uniform(0, 100), 2)
    grade = calculate_grade(marks)
    email = f"{first_name.lower()}.{last_name.lower()}@example.com"
    phone = f"+1{random.randint(1000000000, 9999999999)}"
    enrollment_status = "active"
    enrollment_date = datetime.now().strftime("%Y-%m-%d")

    student = {
        "name": name,
        "roll_no": roll_no,
        "marks": marks,
        "grade": grade,
        "email": email,
        "phone": phone,
        "enrollment_status": enrollment_status,
        "enrollment_date": enrollment_date
    }
    students.append(student)

with open("students.json", "w") as f:
    json.dump(students, f, indent=4)

print("Generated 70 student records.")
