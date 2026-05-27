import os
import random
import csv
# pyrefly: ignore [missing-import]
import numpy as np
import database

random.seed(42)
np.random.seed(42)

# ── Indian Names ──────────────────────────────────────────────────────────────
FIRST_NAMES_MALE = [
    "Aarav", "Vihaan", "Vivaan", "Kabir", "Rohan", "Rahul", "Amit", "Arjun", "Aditya", "Dev",
    "Sai", "Rohit", "Vikram", "Akash", "Manish", "Sunil", "Sanjay", "Sandeep", "Ajay", "Vijay",
    "Anand", "Deepak", "Rajesh", "Harish", "Suresh", "Dinesh", "Anil", "Vikas", "Manoj", "Karan",
    "Ishaan", "Dhruv", "Pranav", "Rudra", "Reyansh", "Shaurya", "Ayush", "Atharv", "Yash", "Krishna",
    "Madhav", "Ganesh", "Abhishek", "Vivek", "Alok", "Piyush", "Rishi", "Samarth", "Nikhil", "Utkarsh"
]
FIRST_NAMES_FEMALE = [
    "Ananya", "Diya", "Saanvi", "Priya", "Pooja", "Sneha", "Shruti", "Riya", "Neha", "Kavita",
    "Jyoti", "Sunita", "Geeta", "Meena", "Rekha", "Anita", "Pinky", "Seema", "Ritu", "Komal",
    "Aadhya", "Aanya", "Aaradhya", "Myra", "Ira", "Avani", "Kiara", "Prisha", "Riddhima", "Tanya",
    "Kriti", "Shreya", "Nisha", "Swati", "Divya", "Preeti", "Suman", "Megha", "Shalini", "Rashmi",
    "Bhavna", "Kiran", "Sapna", "Sheetal", "Poonam", "Mamta", "Anjali", "Aditi", "Payal", "Garima"
]
LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Patel", "Mehta", "Joshi", "Shah", "Trivedi", "Nair", "Pillai",
    "Iyer", "Iyengar", "Reddy", "Rao", "Kumar", "Singh", "Kaur", "Sen", "Das", "Banerjee",
    "Mukherjee", "Chatterjee", "Bose", "Roy", "Bhat", "Kulkarni", "Deshpande", "Patil", "Shinde",
    "Yadav", "Choudhary", "Mishra", "Pandey", "Shukla", "Tiwari", "Dubey", "Dwivedi", "Prasad",
    "Lal", "Saxena", "Chawla", "Bhasin", "Malhotra", "Kapoor", "Khanna", "Grover", "Mehra", "Gill"
]

# ── Class / Stream / Subject config ──────────────────────────────────────────
CLASS_LEVELS = ["Class 11", "Class 12"]
STREAMS      = ["Medical", "Non-Medical", "Commerce", "Arts"]

STREAM_SUBJECTS = {
    "Medical":     ["Physics", "Chemistry", "Biology", "English", "Physical Education"],
    "Non-Medical": ["Physics", "Chemistry", "Mathematics", "English", "Computer Science"],
    "Commerce":    ["Accountancy", "Business Studies", "Economics", "English", "Mathematics"],
    "Arts":        ["History", "Political Science", "Geography", "English", "Hindi"],
}

PARENTAL_INVOLVEMENT_OPTIONS = ["Low", "Medium", "High"]
EXTRACURRICULAR_OPTIONS      = ["Yes", "No"]

# ── Score difficulty modifiers per subject ───────────────────────────────────
SUBJECT_OFFSET = {
    "Physics":            -5,
    "Chemistry":          -4,
    "Biology":            -2,
    "Mathematics":        -4,
    "Computer Science":    3,
    "English":             2,
    "Physical Education":  5,
    "Accountancy":        -3,
    "Business Studies":    1,
    "Economics":          -2,
    "History":             0,
    "Political Science":   1,
    "Geography":           0,
    "Hindi":               3,
}


def generate_student_data(num_students: int = 500):
    print(f"Generating mock data for {num_students} students…")

    students = []
    performance_records = []

    # Generate unique full names
    names_pool: set[tuple] = set()
    attempts = 0
    while len(names_pool) < num_students and attempts < num_students * 10:
        attempts += 1
        gender = random.choice(["M", "F"])
        first  = random.choice(FIRST_NAMES_MALE if gender == "M" else FIRST_NAMES_FEMALE)
        last   = random.choice(LAST_NAMES)
        names_pool.add((f"{first} {last}", first, last))

    names_list = list(names_pool)[:num_students]

    for i, (full_name, first, last) in enumerate(names_list):
        student_id  = f"STD{1000 + i}"
        class_level = random.choice(CLASS_LEVELS)
        stream      = random.choice(STREAMS)
        email       = f"{first.lower()}.{last.lower()}{random.randint(10, 99)}@scorelytics.edu.in"

        students.append((student_id, full_name, class_level, stream, email))

        # Student-level parameters (consistent across all subjects for this student)
        attendance  = float(np.clip(np.random.normal(82, 10), 60, 100))
        study_hours = float(np.clip(np.random.normal(10, 4), 2, 22))
        parental    = random.choices(PARENTAL_INVOLVEMENT_OPTIONS, weights=[0.20, 0.60, 0.20])[0]
        extra       = random.choices(EXTRACURRICULAR_OPTIONS, weights=[0.40, 0.60])[0]

        for subject in STREAM_SUBJECTS[stream]:
            # Base score formula (consistent with original correlation logic)
            score = 40.0
            score += study_hours * 1.5
            score += (attendance - 60) * 0.4
            score += {"High": 6, "Medium": 0, "Low": -6}[parental]
            score += 2 if extra == "Yes" else 0
            score += SUBJECT_OFFSET.get(subject, 0)
            score += float(np.random.normal(0, 4.5))   # noise
            score  = round(float(np.clip(score, 30, 100)), 1)

            performance_records.append((
                student_id, subject, score,
                round(attendance, 1), round(study_hours, 1),
                parental, extra
            ))

    return students, performance_records


def save_to_csv(students, performance_records, filename="sample_data.csv"):
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    print(f"Saving dataset to CSV: {csv_path}")

    student_map = {s[0]: {"Name": s[1], "ClassLevel": s[2], "Stream": s[3], "Email": s[4]}
                   for s in students}

    headers = [
        "StudentID", "Name", "ClassLevel", "Stream", "Email",
        "Subject", "Score", "AttendanceRate", "StudyHoursPerWeek",
        "ParentalInvolvement", "Extracurricular"
    ]

    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for r in performance_records:
            sid  = r[0]
            meta = student_map[sid]
            writer.writerow([
                sid, meta["Name"], meta["ClassLevel"], meta["Stream"], meta["Email"],
                r[1], r[2], r[3], r[4], r[5], r[6]
            ])

    print("CSV saved successfully.")


def populate_database(students, performance_records):
    print("Populating SQLite database…")
    database.reset_db()
    database.insert_students_bulk(students)
    database.insert_performance_records_bulk(performance_records)
    print("Database populated successfully.")


if __name__ == "__main__":
    students, performance_records = generate_student_data(500)
    save_to_csv(students, performance_records)
    populate_database(students, performance_records)
    print("Mock data generation pipeline completed!")
