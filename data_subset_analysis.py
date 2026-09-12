#!/usr/bin/env python3

import sqlite3
import pandas as pd
from pathlib import Path


def get_baseline_melanoma_miraclib_data(db_path):
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        p.project_code,
        su.subject_code,
        su.response,
        su.sex,
        s.sample_code,
        s.time_from_treatment_start,
        s.sample_type
    FROM samples s
    JOIN subjects su ON s.subject_id = su.subject_id
    JOIN projects p ON su.project_id = p.project_id
    JOIN conditions c ON su.condition_id = c.condition_id
    JOIN treatments t ON su.treatment_id = t.treatment_id
    WHERE c.condition_name = 'melanoma'
        AND t.treatment_name = 'miraclib'
        AND s.time_from_treatment_start = 0
        AND s.sample_type = 'PBMC'
    ORDER BY p.project_code, su.subject_code
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df


def analyze_baseline_data(df):
    print("=" * 80)
    print("DATA SUBSET ANALYSIS: BASELINE MELANOMA MIRACLIB SAMPLES")
    print("Filter: melanoma + miraclib + baseline (time=0) + PBMC samples")
    print("=" * 80)
    
    total_samples = len(df)
    total_subjects = df['subject_code'].nunique()
    
    print(f"\nOverall Summary:")
    print(f"  Total baseline samples: {total_samples}")
    print(f"  Total subjects: {total_subjects}")
    
    print(f"\n1. SAMPLES BY PROJECT:")
    print("-" * 40)
    project_counts = df.groupby('project_code').size().reset_index(name='sample_count')
    for _, row in project_counts.iterrows():
        print(f"  {row['project_code']}: {row['sample_count']} samples")
    
    print(f"\n2. SUBJECTS BY RESPONSE:")
    print("-" * 40)
    response_counts = df.groupby('response')['subject_code'].nunique().reset_index(name='subject_count')
    for _, row in response_counts.iterrows():
        response_label = "Responders" if row['response'] == 'yes' else "Non-responders"
        print(f"  {response_label}: {row['subject_count']} subjects")
    
    print(f"\n3. SUBJECTS BY SEX:")
    print("-" * 40)
    sex_counts = df.groupby('sex')['subject_code'].nunique().reset_index(name='subject_count')
    for _, row in sex_counts.iterrows():
        sex_label = "Males" if row['sex'] == 'M' else "Females"
        print(f"  {sex_label}: {row['subject_count']} subjects")
    
    print(f"\n4. DETAILED BREAKDOWN:")
    print("-" * 40)
    
    print(f"\nBy Project and Response:")
    project_response = df.groupby(['project_code', 'response'])['subject_code'].nunique().unstack(fill_value=0)
    project_response.columns = ['Non-responders', 'Responders']
    print(project_response.to_string())
    
    print(f"\nBy Project and Sex:")
    project_sex = df.groupby(['project_code', 'sex'])['subject_code'].nunique().unstack(fill_value=0)
    project_sex.columns = ['Females', 'Males']
    print(project_sex.to_string())
    
    print(f"\nBy Response and Sex:")
    response_sex = df.groupby(['response', 'sex'])['subject_code'].nunique().unstack(fill_value=0)
    response_sex.columns = ['Females', 'Males']
    response_sex.index = ['Non-responders', 'Responders']
    print(response_sex.to_string())
    
    return {
        'total_samples': total_samples,
        'total_subjects': total_subjects,
        'project_counts': project_counts,
        'response_counts': response_counts,
        'sex_counts': sex_counts,
        'project_response': project_response,
        'project_sex': project_sex,
        'response_sex': response_sex
    }


def save_summary_data(df, summary_stats, script_dir):
    baseline_output_path = script_dir / "baseline_melanoma_miraclib_samples.csv"
    df.to_csv(baseline_output_path, index=False)
    
    summary_output_path = script_dir / "baseline_summary_stats.csv"
    with open(summary_output_path, 'w') as f:
        f.write("Analysis,Category,Count\n")
        
        for _, row in summary_stats['project_counts'].iterrows():
            f.write(f"Samples by Project,{row['project_code']},{row['sample_count']}\n")
        
        for _, row in summary_stats['response_counts'].iterrows():
            response_label = "Responders" if row['response'] == 'yes' else "Non-responders"
            f.write(f"Subjects by Response,{response_label},{row['subject_count']}\n")
        
        for _, row in summary_stats['sex_counts'].iterrows():
            sex_label = "Males" if row['sex'] == 'M' else "Females"
            f.write(f"Subjects by Sex,{sex_label},{row['subject_count']}\n")
    
    print(f"\nBaseline sample data saved to: {baseline_output_path}")
    print(f"Summary statistics saved to: {summary_output_path}")


def main():
    script_dir = Path(__file__).parent
    db_path = script_dir / "cell_count.db"
    
    if not db_path.exists():
        print(f"Error: Database file not found at {db_path}")
        print("Please run load_data.py first to create the database.")
        return 1
    
    print("Loading baseline melanoma miraclib data...")
    df = get_baseline_melanoma_miraclib_data(db_path)
    
    if len(df) == 0:
        print("No data found matching the criteria!")
        return 1
    
    summary_stats = analyze_baseline_data(df)
    
    save_summary_data(df, summary_stats, script_dir)
    
    print("\n" + "=" * 80)
    print("BASELINE DATA ANALYSIS COMPLETE")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    exit(main())