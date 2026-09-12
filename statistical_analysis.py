#!/usr/bin/env python3

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from pathlib import Path


def get_melanoma_miraclib_data(db_path):
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        s.sample_code as sample,
        su.response,
        sa.sample_type,
        cc.cell_type as population,
        cc.count,
        SUM(cc.count) OVER (PARTITION BY s.sample_id) as total_count
    FROM samples s
    JOIN subjects su ON s.subject_id = su.subject_id
    JOIN cell_counts cc ON s.sample_id = cc.sample_id
    JOIN conditions c ON su.condition_id = c.condition_id
    JOIN treatments t ON su.treatment_id = t.treatment_id
    JOIN samples sa ON s.sample_id = sa.sample_id
    WHERE c.condition_name = 'melanoma'
        AND t.treatment_name = 'miraclib'
        AND su.response IN ('yes', 'no')
        AND sa.sample_type = 'PBMC'
    ORDER BY s.sample_code, cc.cell_type
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    df['percentage'] = (df['count'] / df['total_count'] * 100).round(2)
    
    return df


def perform_statistical_tests(df):
    results = []
    cell_types = df['population'].unique()
    
    for cell_type in cell_types:
        cell_data = df[df['population'] == cell_type]
        responders = cell_data[cell_data['response'] == 'yes']['percentage']
        non_responders = cell_data[cell_data['response'] == 'no']['percentage']
        
        stat, p_value = stats.mannwhitneyu(responders, non_responders, alternative='two-sided')
        
        results.append({
            'population': cell_type,
            'responders_mean': responders.mean(),
            'responders_std': responders.std(),
            'responders_n': len(responders),
            'non_responders_mean': non_responders.mean(),
            'non_responders_std': non_responders.std(),
            'non_responders_n': len(non_responders),
            'statistic': stat,
            'p_value': p_value,
            'significant': 'Yes' if p_value < 0.05 else 'No'
        })
    
    return pd.DataFrame(results)


def create_boxplot(df, output_path):
    plt.figure(figsize=(14, 8))
    
    cell_order = ['b_cell', 'cd4_t_cell', 'cd8_t_cell', 'nk_cell', 'monocyte']
    
    sns.boxplot(data=df, x='population', y='percentage', hue='response', 
                order=cell_order, palette={'yes': '#2ecc71', 'no': '#e74c3c'})
    
    plt.xlabel('Cell Population', fontsize=12, fontweight='bold')
    plt.ylabel('Relative Frequency (%)', fontsize=12, fontweight='bold')
    plt.title('Cell Population Frequencies: Responders vs Non-Responders\n(Melanoma Patients Receiving Miraclib - PBMC Samples)', 
              fontsize=14, fontweight='bold', pad=20)
    plt.legend(title='Response', labels=['Non-Responders', 'Responders'], fontsize=10)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Boxplot saved to: {output_path}")
    plt.close()


def main():
    script_dir = Path(__file__).parent
    db_path = script_dir / "cell_count.db"
    
    if not db_path.exists():
        print(f"Error: Database file not found at {db_path}")
        print("Please run load_data.py first to create the database.")
        return 1
    
    print("=" * 80)
    print("STATISTICAL ANALYSIS: MELANOMA PATIENTS RECEIVING MIRACLIB")
    print("Comparing Responders vs Non-Responders (PBMC Samples Only)")
    print("=" * 80)
    
    print("\nLoading data...")
    df = get_melanoma_miraclib_data(db_path)
    
    total_samples = df['sample'].nunique()
    responders = df[df['response'] == 'yes']['sample'].nunique()
    non_responders = df[df['response'] == 'no']['sample'].nunique()
    
    print(f"\nDataset Summary:")
    print(f"  Total samples: {total_samples}")
    print(f"  Responders: {responders}")
    print(f"  Non-responders: {non_responders}")
    
    print("\nPerforming statistical tests (Mann-Whitney U test)...")
    stats_results = perform_statistical_tests(df)
    
    print("\n" + "=" * 80)
    print("STATISTICAL TEST RESULTS")
    print("=" * 80)
    print("\nMean Relative Frequencies (%) by Response Group:")
    print("-" * 80)
    
    for _, row in stats_results.iterrows():
        print(f"\n{row['population'].upper()}:")
        print(f"  Responders:     {row['responders_mean']:6.2f}% ± {row['responders_std']:5.2f}% (n={row['responders_n']})")
        print(f"  Non-responders: {row['non_responders_mean']:6.2f}% ± {row['non_responders_std']:5.2f}% (n={row['non_responders_n']})")
        print(f"  Difference:     {row['responders_mean'] - row['non_responders_mean']:+6.2f}%")
        print(f"  p-value:        {row['p_value']:.4e}")
        print(f"  Significant:    {row['significant']} (α=0.05)")
    
    print("\n" + "=" * 80)
    print("SUMMARY OF SIGNIFICANT DIFFERENCES")
    print("=" * 80)
    
    significant = stats_results[stats_results['significant'] == 'Yes']
    if len(significant) > 0:
        print(f"\nCell populations with significant differences (p < 0.05):")
        for _, row in significant.iterrows():
            direction = "higher" if row['responders_mean'] > row['non_responders_mean'] else "lower"
            print(f"  • {row['population']}: Responders have {direction} frequencies (p={row['p_value']:.4e})")
    else:
        print("\nNo cell populations show significant differences at α=0.05 level.")
    
    not_significant = stats_results[stats_results['significant'] == 'No']
    if len(not_significant) > 0:
        print(f"\nCell populations without significant differences (p ≥ 0.05):")
        for _, row in not_significant.iterrows():
            print(f"  • {row['population']} (p={row['p_value']:.4e})")
    
    print("\n" + "=" * 80)
    
    comparison_output_path = script_dir / "melanoma_miraclib_comparison.csv"
    df.to_csv(comparison_output_path, index=False)
    print(f"\nComparison data saved to: {comparison_output_path}")
    
    stats_output_path = script_dir / "statistical_results.csv"
    stats_results.to_csv(stats_output_path, index=False)
    print(f"Statistical test results saved to: {stats_output_path}")
    
    print("\nGenerating boxplot visualization...")
    plot_output_path = script_dir / "response_comparison_boxplot.png"
    create_boxplot(df, plot_output_path)
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    exit(main())
