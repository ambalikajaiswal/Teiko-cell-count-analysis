import sqlite3
import csv
from pathlib import Path


def create_schema(conn):
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            project_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_code TEXT UNIQUE NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conditions (
            condition_id INTEGER PRIMARY KEY AUTOINCREMENT,
            condition_name TEXT UNIQUE NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS treatments (
            treatment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            treatment_name TEXT UNIQUE NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_code TEXT UNIQUE NOT NULL,
            project_id INTEGER NOT NULL,
            condition_id INTEGER,
            age INTEGER,
            sex TEXT CHECK(sex IN ('M', 'F')),
            treatment_id INTEGER,
            response TEXT CHECK(response IN ('yes', 'no', '')),
            FOREIGN KEY (project_id) REFERENCES projects(project_id),
            FOREIGN KEY (condition_id) REFERENCES conditions(condition_id),
            FOREIGN KEY (treatment_id) REFERENCES treatments(treatment_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS samples (
            sample_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_code TEXT UNIQUE NOT NULL,
            subject_id INTEGER NOT NULL,
            sample_type TEXT NOT NULL,
            time_from_treatment_start INTEGER NOT NULL,
            FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cell_counts (
            count_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id INTEGER NOT NULL,
            cell_type TEXT NOT NULL CHECK(cell_type IN (
                'b_cell', 'cd8_t_cell', 'cd4_t_cell', 'nk_cell', 'monocyte'
            )),
            count INTEGER NOT NULL,
            FOREIGN KEY (sample_id) REFERENCES samples(sample_id),
            UNIQUE(sample_id, cell_type)
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_subjects_project ON subjects(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_subjects_condition ON subjects(condition_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_subjects_treatment ON subjects(treatment_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_samples_subject ON samples(subject_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_samples_time ON samples(time_from_treatment_start)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cell_counts_sample ON cell_counts(sample_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cell_counts_type ON cell_counts(cell_type)")
    
    conn.commit()


def load_data(conn, csv_path):
    cursor = conn.cursor()
    projects = {}
    conditions = {}
    treatments = {}
    subjects = {}
    samples = {}
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            project_code = row['project']
            if project_code not in projects:
                cursor.execute("INSERT INTO projects (project_code) VALUES (?)", (project_code,))
                projects[project_code] = cursor.lastrowid
            project_id = projects[project_code]
            
            condition_name = row['condition']
            if condition_name and condition_name not in conditions:
                cursor.execute("INSERT INTO conditions (condition_name) VALUES (?)", (condition_name,))
                conditions[condition_name] = cursor.lastrowid
            condition_id = conditions.get(condition_name)
            
            treatment_name = row['treatment']
            if treatment_name and treatment_name not in treatments:
                cursor.execute("INSERT INTO treatments (treatment_name) VALUES (?)", (treatment_name,))
                treatments[treatment_name] = cursor.lastrowid
            treatment_id = treatments.get(treatment_name)
            
            subject_code = row['subject']
            if subject_code not in subjects:
                cursor.execute(
                    """INSERT INTO subjects 
                    (subject_code, project_id, condition_id, age, sex, treatment_id, response)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (subject_code, project_id, condition_id, 
                     int(row['age']) if row['age'] else None,
                     row['sex'] if row['sex'] else None,
                     treatment_id, row['response'] if row['response'] else '')
                )
                subjects[subject_code] = cursor.lastrowid
            subject_id = subjects[subject_code]
            
            sample_code = row['sample']
            if sample_code not in samples:
                cursor.execute(
                    """INSERT INTO samples 
                    (sample_code, subject_id, sample_type, time_from_treatment_start)
                    VALUES (?, ?, ?, ?)""",
                    (sample_code, subject_id, row['sample_type'], int(row['time_from_treatment_start']))
                )
                samples[sample_code] = cursor.lastrowid
            sample_id = samples[sample_code]
            
            cell_types = ['b_cell', 'cd8_t_cell', 'cd4_t_cell', 'nk_cell', 'monocyte']
            for cell_type in cell_types:
                cursor.execute(
                    "INSERT INTO cell_counts (sample_id, cell_type, count) VALUES (?, ?, ?)",
                    (sample_id, cell_type, int(row[cell_type]))
                )
    
    conn.commit()
    print(f"Data loaded successfully!")
    print(f"  Projects: {len(projects)}")
    print(f"  Conditions: {len(conditions)}")
    print(f"  Treatments: {len(treatments)}")
    print(f"  Subjects: {len(subjects)}")
    print(f"  Samples: {len(samples)}")


def main():
    script_dir = Path(__file__).parent
    csv_path = script_dir / "cell-count.csv"
    db_path = script_dir / "cell_count.db"
    
    if not csv_path.exists():
        print(f"Error: CSV file not found at {csv_path}")
        return 1
    
    if db_path.exists():
        print(f"Removing existing database: {db_path}")
        db_path.unlink()
    
    print(f"Creating database: {db_path}")
    conn = sqlite3.connect(db_path)
    
    try:
        print("Creating database schema...")
        create_schema(conn)
        
        print(f"Loading data from {csv_path}...")
        load_data(conn, csv_path)
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM samples")
        sample_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM cell_counts")
        count_records = cursor.fetchone()[0]
        
        print(f"\nDatabase created successfully!")
        print(f"  Total samples: {sample_count}")
        print(f"  Total cell count records: {count_records}")
        
    finally:
        conn.close()
    
    return 0


if __name__ == "__main__":
    exit(main())
