#!/usr/bin/env python3

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from pathlib import Path
import os


# Page configuration
st.set_page_config(
    page_title="Cell Count Analysis Dashboard",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_data():
    """Load all analysis results"""
    script_dir = Path(__file__).parent
    
    # Check if files exist
    files = {
        'frequency': script_dir / "cell_frequency_summary.csv",
        'stats': script_dir / "statistical_results.csv",
        'comparison': script_dir / "melanoma_miraclib_comparison.csv",
        'baseline': script_dir / "baseline_melanoma_miraclib_samples.csv",
        'baseline_stats': script_dir / "baseline_summary_stats.csv",
        'db': script_dir / "cell_count.db"
    }
    
    missing_files = [name for name, path in files.items() if not path.exists()]
    if missing_files:
        st.error(f"Missing files: {missing_files}")
        st.info("Please run 'make pipeline' first to generate all required files.")
        return None
    
    try:
        data = {
            'frequency': pd.read_csv(files['frequency']),
            'stats': pd.read_csv(files['stats']),
            'comparison': pd.read_csv(files['comparison']),
            'baseline': pd.read_csv(files['baseline']),
            'baseline_stats': pd.read_csv(files['baseline_stats'])
        }
        return data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


def query_database(query):
    """Execute SQL query on the database"""
    script_dir = Path(__file__).parent
    db_path = script_dir / "cell_count.db"
    
    if not db_path.exists():
        st.error("Database not found. Please run 'make pipeline' first.")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        result = pd.read_sql_query(query, conn)
        conn.close()
        return result
    except Exception as e:
        st.error(f"Database query error: {e}")
        return None


def main():
    st.title("🧬 Cell Count Analysis Dashboard")
    st.markdown("---")
    
    # Load data
    data = load_data()
    if data is None:
        return
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Analysis",
        ["Overview", "Part 2: Frequency Analysis", "Part 3: Statistical Analysis", "Part 4: Baseline Analysis", "Custom Query"]
    )
    
    if page == "Overview":
        show_overview(data)
    elif page == "Part 2: Frequency Analysis":
        show_frequency_analysis(data)
    elif page == "Part 3: Statistical Analysis":
        show_statistical_analysis(data)
    elif page == "Part 4: Baseline Analysis":
        show_baseline_analysis(data)
    elif page == "Custom Query":
        show_custom_query()


def show_overview(data):
    st.header("📊 Project Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_samples = data['frequency']['sample'].nunique()
        st.metric("Total Samples", f"{total_samples:,}")
    
    with col2:
        total_records = len(data['frequency'])
        st.metric("Cell Count Records", f"{total_records:,}")
    
    with col3:
        cell_types = data['frequency']['population'].nunique()
        st.metric("Cell Types", cell_types)
    
    with col4:
        baseline_samples = len(data['baseline'])
        st.metric("Baseline Melanoma Samples", baseline_samples)
    
    st.markdown("---")
    
    # Summary statistics
    st.subheader("Dataset Summary")
    
    # Cell type distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Cell Type Average Percentages:**")
        cell_avg = data['frequency'].groupby('population')['percentage'].mean().sort_values(ascending=False)
        for cell_type, avg_pct in cell_avg.items():
            st.write(f"• {cell_type}: {avg_pct:.2f}%")
    
    with col2:
        # Pie chart of average cell type distribution
        fig = px.pie(
            values=cell_avg.values,
            names=cell_avg.index,
            title="Average Cell Type Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)


def show_frequency_analysis(data):
    st.header("📈 Part 2: Cell Type Frequency Analysis")
    
    st.markdown("**Question:** What is the frequency of each cell type in each sample?")
    
    # Sample data preview
    st.subheader("Sample Data")
    st.dataframe(data['frequency'].head(20))
    
    # Download button
    csv = data['frequency'].to_csv(index=False)
    st.download_button(
        label="Download Full Frequency Data (CSV)",
        data=csv,
        file_name="cell_frequency_summary.csv",
        mime="text/csv"
    )
    
    # Visualization
    st.subheader("Frequency Distribution by Cell Type")
    
    fig = px.box(
        data['frequency'], 
        x='population', 
        y='percentage',
        title="Cell Type Frequency Distribution Across All Samples"
    )
    fig.update_layout(
        xaxis_title="Cell Population",
        yaxis_title="Relative Frequency (%)",
        xaxis_tickangle=45
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary statistics
    st.subheader("Summary Statistics")
    summary = data['frequency'].groupby('population')['percentage'].agg(['mean', 'std', 'min', 'max']).round(2)
    st.dataframe(summary)


def show_statistical_analysis(data):
    st.header("📊 Part 3: Statistical Analysis")
    
    st.markdown("**Question:** Compare melanoma patients receiving miraclib - responders vs non-responders")
    
    # Key findings
    st.subheader("🔍 Key Findings")
    
    significant_cells = data['stats'][data['stats']['significant'] == 'Yes']
    if len(significant_cells) > 0:
        for _, row in significant_cells.iterrows():
            direction = "higher" if row['responders_mean'] > row['non_responders_mean'] else "lower"
            st.success(f"**{row['population'].upper()}**: Responders have {direction} frequencies (p={row['p_value']:.4f})")
    else:
        st.info("No significant differences found at α=0.05 level")
    
    # Statistical results table
    st.subheader("📋 Statistical Test Results")
    
    # Format the results for display
    display_stats = data['stats'].copy()
    display_stats['responders_mean'] = display_stats['responders_mean'].round(2)
    display_stats['non_responders_mean'] = display_stats['non_responders_mean'].round(2)
    display_stats['p_value'] = display_stats['p_value'].apply(lambda x: f"{x:.4e}")
    
    st.dataframe(display_stats)
    
    # Boxplot visualization
    st.subheader("📊 Responders vs Non-Responders Comparison")
    
    # Create interactive boxplot
    fig = px.box(
        data['comparison'],
        x='population',
        y='percentage',
        color='response',
        title="Cell Population Frequencies: Responders vs Non-Responders<br>(Melanoma Patients Receiving Miraclib - PBMC Samples)",
        color_discrete_map={'yes': '#2ecc71', 'no': '#e74c3c'}
    )
    
    fig.update_layout(
        xaxis_title="Cell Population",
        yaxis_title="Relative Frequency (%)",
        xaxis_tickangle=45,
        legend_title="Response"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Sample counts
    col1, col2 = st.columns(2)
    
    with col1:
        responders = data['comparison'][data['comparison']['response'] == 'yes']['sample'].nunique()
        st.metric("Responder Samples", responders)
    
    with col2:
        non_responders = data['comparison'][data['comparison']['response'] == 'no']['sample'].nunique()
        st.metric("Non-Responder Samples", non_responders)


def show_baseline_analysis(data):
    st.header("🎯 Part 4: Baseline Data Analysis")
    
    st.markdown("**Focus:** Melanoma PBMC samples at baseline (time=0) treated with miraclib")
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_subjects = len(data['baseline'])
        st.metric("Total Subjects", total_subjects)
    
    with col2:
        responders = len(data['baseline'][data['baseline']['response'] == 'yes'])
        st.metric("Responders", responders)
    
    with col3:
        males = len(data['baseline'][data['baseline']['sex'] == 'M'])
        st.metric("Males", males)
    
    # Project breakdown
    st.subheader("📈 Breakdown by Categories")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Project distribution
        project_counts = data['baseline']['project_code'].value_counts()
        fig = px.pie(
            values=project_counts.values,
            names=project_counts.index,
            title="Samples by Project"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Response distribution
        response_counts = data['baseline']['response'].value_counts()
        response_labels = {'yes': 'Responders', 'no': 'Non-responders'}
        fig = px.pie(
            values=response_counts.values,
            names=[response_labels[x] for x in response_counts.index],
            title="Response Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed breakdown table
    st.subheader("📋 Detailed Breakdown")
    
    # Cross-tabulation
    crosstab = pd.crosstab(
        data['baseline']['project_code'], 
        data['baseline']['response'], 
        margins=True, 
        margins_name="Total"
    )
    crosstab.columns = ['Non-responders', 'Responders', 'Total']
    
    st.markdown("**By Project and Response:**")
    st.dataframe(crosstab)
    
    # Raw data preview
    st.subheader("📄 Sample Data")
    st.dataframe(data['baseline'].head(20))


def show_custom_query():
    st.header("🔍 Custom Database Query")
    
    st.markdown("Run custom SQL queries on the cell count database.")
    
    # Predefined useful queries
    st.subheader("Sample Queries")
    
    sample_queries = {
        "All table names": "SELECT name FROM sqlite_master WHERE type='table';",
        "Database schema": "SELECT sql FROM sqlite_master WHERE type='table';",
        "Sample count by condition": """
            SELECT c.condition_name, COUNT(*) as sample_count
            FROM samples s
            JOIN subjects su ON s.subject_id = su.subject_id
            JOIN conditions c ON su.condition_id = c.condition_id
            GROUP BY c.condition_name;
        """,
        "Average B-cell count by treatment": """
            SELECT t.treatment_name, AVG(cc.count) as avg_b_cells
            FROM cell_counts cc
            JOIN samples s ON cc.sample_id = s.sample_id
            JOIN subjects su ON s.subject_id = su.subject_id
            JOIN treatments t ON su.treatment_id = t.treatment_id
            WHERE cc.cell_type = 'b_cell'
            GROUP BY t.treatment_name;
        """
    }
    
    selected_query = st.selectbox("Choose a sample query:", list(sample_queries.keys()))
    
    # Query input
    query = st.text_area(
        "SQL Query:", 
        value=sample_queries[selected_query], 
        height=150
    )
    
    if st.button("Execute Query"):
        if query.strip():
            result = query_database(query)
            if result is not None:
                st.subheader("Query Results")
                st.dataframe(result)
                
                # Download results
                if not result.empty:
                    csv = result.to_csv(index=False)
                    st.download_button(
                        label="Download Results (CSV)",
                        data=csv,
                        file_name="query_results.csv",
                        mime="text/csv"
                    )
        else:
            st.warning("Please enter a SQL query.")


if __name__ == "__main__":
    main()