#!/usr/bin/env python3

import sqlite3
import pandas as pd
from pathlib import Path


def calculate_cell_frequencies(db_path):
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        s.sample_code as sample,
        cc.cell_type as population,
        cc.count,
        SUM(cc.count) OVER (PARTITION BY s.sample_id) as total_count
    FROM samples s
    JOIN cell_counts cc ON s.sample_id = cc.sample_id
    ORDER BY s.sample_code, cc.cell_type
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    df['percentage'] = (df['count'] / df['total_count'] * 100).round(2)
    df = df[['sample', 'total_count', 'population', 'count', 'percentage']]
    
    return df


def main():
    script_dir = Path(__file__).parent
    db_path = script_dir / "cell_count.db"
    
    if not db_path.exists():
        print(f"Error: Database file not found at {db_path}")
        print("Please run load_data.py first to create the database.")
        return 1
    
    print("Calculating cell type frequencies for each sample...")
    df = calculate_cell_frequencies(db_path)
    
    print(f"\nCell Type Frequency Analysis")
    print(f"Total samples: {df['sample'].nunique()}")
    print(f"Total records: {len(df)}")
    print(f"\nFirst 20 rows:")
    print(df.head(20).to_string(index=False))
    
    output_path = script_dir / "cell_frequency_summary.csv"
    df.to_csv(output_path, index=False)
    print(f"\nFull results saved to: {output_path}")
    
    return 0


if __name__ == "__main__":
    exit(main())
