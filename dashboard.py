#!/usr/bin/env python3

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from pathlib import Path
import numpy as np


# Page configuration
st.set_page_config(
    page_title="Cell Count Analysis Dashboard",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .section-header {
        font-size: 1.8rem;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #3498db;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #e7f3ff;
        border: 1px solid #b3d9ff;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .data-table {
        border-radius: 10px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

def display_enhanced_dataframe(df, title, description, max_rows=100):
    """Display an enhanced dataframe with proper formatting and download option"""
    
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)
    
    if description:
        st.markdown(f'<div class="info-box"><strong>Data Description:</strong> {description}</div>', 
                   unsafe_allow_html=True)
    
    # Show data statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Records", f"{len(df):,}")
    with col2:
        if 'sample' in df.columns:
            st.metric("Unique Samples", f"{df['sample'].nunique():,}")
        elif 'subject_code' in df.columns:
            st.metric("Unique Subjects", f"{df['subject_code'].nunique():,}")
        else:
            st.metric("Columns", f"{len(df.columns)}")
    with col3:
        if 'population' in df.columns:
            st.metric("Cell Types", f"{df['population'].nunique()}")
        elif 'project_code' in df.columns:
            st.metric("Projects", f"{df['project_code'].nunique()}")
        else:
            st.metric("Data Points", f"{df.size:,}")
    with col4:
        if 'percentage' in df.columns:
            st.metric("Avg Percentage", f"{df['percentage'].mean():.2f}%")
        elif 'count' in df.columns:
            st.metric("Avg Count", f"{df['count'].mean():,.0f}")
        else:
            st.metric("Non-null Values", f"{df.count().sum():,}")
    
    # Determine how many rows to show
    rows_to_show = min(len(df), max_rows)
    
    st.markdown(f"**Showing {rows_to_show} of {len(df)} records**")
    
    # Display the dataframe with enhanced styling
    st.dataframe(
        df.head(rows_to_show),
        use_container_width=True,
        height=400 if rows_to_show > 10 else 300
    )
    
    # Download section
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("**Download Complete Dataset**")
        st.caption(f"Download all {len(df)} records as CSV file")
    
    with col2:
        csv_data = df.to_csv(index=False)
        filename = f"{title.lower().replace(' ', '_').replace(':', '')}.csv"
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            use_container_width=True
        )


def create_enhanced_boxplot(df, title, x_col, y_col, color_col=None):
    """Create an enhanced boxplot with better styling"""
    
    fig = px.box(
        df, 
        x=x_col, 
        y=y_col, 
        color=color_col,
        title=title,
        color_discrete_map={'yes': '#27ae60', 'no': '#e74c3c'} if color_col == 'response' else None
    )
    
    fig.update_layout(
        title_font_size=16,
        title_x=0.5,
        xaxis_title_font_size=14,
        yaxis_title_font_size=14,
        legend_title_font_size=12,
        height=500,
        showlegend=True if color_col else False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='lightgray'),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='lightgray')
    )
    
    return fig


def create_enhanced_pie_chart(data, labels, title, colors=None):
    """Create an enhanced pie chart with better styling"""
    
    fig = px.pie(
        values=data,
        names=labels,
        title=title,
        color_discrete_sequence=colors or px.colors.qualitative.Set3
    )
    
    fig.update_layout(
        title_font_size=16,
        title_x=0.5,
        height=400,
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5)
    )
    
    fig.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )
    
    return fig
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
        st.error(f"❌ Missing files: {missing_files}")
        st.info("💡 Please run 'make pipeline' first to generate all required files.")
        return None
    
    try:
        data = {
            'frequency': pd.read_csv(files['frequency']),
            'stats': pd.read_csv(files['stats']),
            'comparison': pd.read_csv(files['comparison']),
            'baseline': pd.read_csv(files['baseline']),
            'baseline_stats': pd.read_csv(files['baseline_stats'])
        }
        
        # Validate data structure
        expected_columns = {
            'frequency': ['sample', 'total_count', 'population', 'count', 'percentage'],
            'stats': ['population', 'responders_mean', 'non_responders_mean', 'p_value', 'significant'],
            'comparison': ['sample', 'response', 'population', 'count', 'total_count', 'percentage'],
            'baseline': ['project_code', 'subject_code', 'response', 'sex', 'sample_code']
        }
        
        for dataset, expected_cols in expected_columns.items():
            missing_cols = [col for col in expected_cols if col not in data[dataset].columns]
            if missing_cols:
                st.error(f"❌ Missing columns in {dataset}: {missing_cols}")
                return None
        
        # Validate data ranges
        if data['frequency']['percentage'].min() < 0 or data['frequency']['percentage'].max() > 100:
            st.warning("⚠️ Percentage values outside expected range (0-100%)")
        
        if data['comparison']['response'].unique().tolist() != ['no', 'yes'] and set(data['comparison']['response'].unique()) != {'no', 'yes'}:
            st.warning(f"⚠️ Unexpected response values: {data['comparison']['response'].unique()}")
            
        return data
        
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
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
    st.markdown('<div class="main-header">🔬 Cell Count Analysis Dashboard</div>', unsafe_allow_html=True)
    
    # Load data
    data = load_data()
    if data is None:
        return
    
    # Enhanced sidebar navigation
    st.sidebar.markdown("## 📊 Navigation")
    st.sidebar.markdown("Select an analysis section to explore:")
    
    page = st.sidebar.selectbox(
        "Choose Analysis",
        [
            "🏠 Project Overview", 
            "📈 Part 2: Cell Frequency Analysis", 
            "🧪 Part 3: Statistical Analysis", 
            "🎯 Part 4: Baseline Analysis", 
            "🔍 Custom Database Query"
        ]
    )
    
    # Add sidebar info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 Quick Stats")
    st.sidebar.metric("Total Samples", f"{data['frequency']['sample'].nunique():,}")
    st.sidebar.metric("Cell Count Records", f"{len(data['frequency']):,}")
    st.sidebar.metric("Analysis Samples", f"{data['comparison']['sample'].nunique():,}")
    
    # Route to appropriate page
    if page == "🏠 Project Overview":
        show_enhanced_overview(data)
    elif page == "📈 Part 2: Cell Frequency Analysis":
        show_enhanced_frequency_analysis(data)
    elif page == "🧪 Part 3: Statistical Analysis":
        show_enhanced_statistical_analysis(data)
    elif page == "🎯 Part 4: Baseline Analysis":
        show_enhanced_baseline_analysis(data)
    elif page == "🔍 Custom Database Query":
        show_enhanced_custom_query()


def show_enhanced_overview(data):
    st.markdown('<div class="section-header">📊 Project Overview</div>', unsafe_allow_html=True)
    
    # Key metrics with enhanced styling
    st.markdown("### 🎯 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Total Samples", f"{data['frequency']['sample'].nunique():,}")
        st.caption("All samples in dataset")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Cell Count Records", f"{len(data['frequency']):,}")
        st.caption("Individual cell measurements")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Cell Types", data['frequency']['population'].nunique())
        st.caption("Different immune cell populations")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Baseline Samples", len(data['baseline']))
        st.caption("Time=0 melanoma samples")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Enhanced visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Cell Type Distribution")
        cell_avg = data['frequency'].groupby('population')['percentage'].mean().sort_values(ascending=False)
        
        fig = create_enhanced_pie_chart(
            data=cell_avg.values,
            labels=cell_avg.index,
            title="Average Cell Type Distribution Across All Samples"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📊 Frequency Distribution")
        
        fig = create_enhanced_boxplot(
            df=data['frequency'],
            title="Cell Type Frequency Distribution",
            x_col='population',
            y_col='percentage'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Enhanced summary table
    st.markdown("### 📋 Cell Type Statistics")
    summary_stats = data['frequency'].groupby('population')['percentage'].agg([
        ('Mean %', 'mean'),
        ('Std Dev %', 'std'),
        ('Min %', 'min'),
        ('Max %', 'max'),
        ('Median %', 'median')
    ]).round(2)
    
    st.dataframe(summary_stats, use_container_width=True)


def show_enhanced_frequency_analysis(data):
    st.markdown('<div class="section-header">📈 Part 2: Cell Type Frequency Analysis</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    <strong>Analysis Question:</strong> What is the frequency of each cell type in each sample?<br>
    <strong>Method:</strong> Calculate relative frequency of each cell population as percentage of total cell count per sample.
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced data display
    display_enhanced_dataframe(
        df=data['frequency'],
        title="Cell Type Frequency Data",
        description="Relative frequency (percentage) of each immune cell population in every sample. Each row represents one cell type from one sample.",
        max_rows=100
    )
    
    # Enhanced visualization section
    st.markdown("### 📊 Interactive Visualizations")
    
    # Visualization controls
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("**Visualization Options:**")
        viz_type = st.radio(
            "Choose visualization:",
            ["Box Plot", "Violin Plot", "Histogram", "Scatter Plot"]
        )
        
        selected_populations = st.multiselect(
            "Select cell types:",
            options=data['frequency']['population'].unique(),
            default=data['frequency']['population'].unique()
        )
    
    with col2:
        if selected_populations:
            filtered_data = data['frequency'][data['frequency']['population'].isin(selected_populations)]
            
            if viz_type == "Box Plot":
                fig = create_enhanced_boxplot(
                    df=filtered_data,
                    title="Cell Type Frequency Distribution",
                    x_col='population',
                    y_col='percentage'
                )
            elif viz_type == "Violin Plot":
                fig = px.violin(
                    filtered_data, 
                    x='population', 
                    y='percentage',
                    title="Cell Type Frequency Distribution (Violin Plot)",
                    box=True
                )
                fig.update_layout(
                    height=500,
                    showlegend=True,
                    xaxis=dict(showgrid=True, gridwidth=1, gridcolor='lightgray'),
                    yaxis=dict(showgrid=True, gridwidth=1, gridcolor='lightgray')
                )
            elif viz_type == "Histogram":
                fig = px.histogram(
                    filtered_data,
                    x='percentage',
                    color='population',
                    title="Frequency Distribution Histogram",
                    nbins=30,
                    opacity=0.7
                )
                fig.update_layout(height=500, showlegend=True)
            else:  # Scatter Plot
                sample_subset = filtered_data.sample(min(1000, len(filtered_data)))
                fig = px.scatter(
                    sample_subset,
                    x='total_count',
                    y='percentage',
                    color='population',
                    title="Frequency vs Total Cell Count",
                    hover_data=['sample']
                )
                fig.update_layout(height=500, showlegend=True)
            
            fig.update_layout(height=500, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
    
    # Summary statistics table
    st.markdown("### 📋 Statistical Summary")
    
    summary_data = data['frequency'].groupby('population')['percentage'].agg([
        ('Count', 'count'),
        ('Mean', 'mean'),
        ('Std Dev', 'std'),
        ('Min', 'min'),
        ('25%', lambda x: x.quantile(0.25)),
        ('Median', 'median'),
        ('75%', lambda x: x.quantile(0.75)),
        ('Max', 'max')
    ]).round(2)
    
    st.dataframe(summary_data, use_container_width=True)


def show_enhanced_statistical_analysis(data):
    st.markdown('<div class="section-header">🧪 Part 3: Statistical Analysis</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    <strong>Analysis Question:</strong> Compare melanoma patients receiving miraclib - responders vs non-responders<br>
    <strong>Method:</strong> Mann-Whitney U test to compare cell population frequencies between treatment response groups<br>
    <strong>Sample:</strong> PBMC samples only, melanoma condition, miraclib treatment
    </div>
    """, unsafe_allow_html=True)
    
    # Key findings section
    st.markdown("### 🔍 Key Statistical Findings")
    
    significant_cells = data['stats'][data['stats']['significant'] == 'Yes']
    
    if len(significant_cells) > 0:
        for _, row in significant_cells.iterrows():
            direction = "higher" if row['responders_mean'] > row['non_responders_mean'] else "lower"
            st.markdown(f"""
            <div class="success-box">
            <strong>🎯 SIGNIFICANT RESULT</strong><br>
            <strong>{row['population'].upper().replace('_', ' ')}</strong>: Responders have {direction} frequencies<br>
            p-value: {row['p_value']:.4e} (< 0.05)
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("ℹ️ No significant differences found at α=0.05 level")
    
    # Enhanced statistical results display
    display_enhanced_dataframe(
        df=data['stats'],
        title="Statistical Test Results (Mann-Whitney U Test)",
        description="Comparison of cell population frequencies between responders and non-responders. Shows means, standard deviations, sample sizes, test statistics, p-values, and significance.",
        max_rows=10
    )
    
    # Sample size information
    col1, col2, col3 = st.columns(3)
    with col1:
        responders = data['comparison'][data['comparison']['response'] == 'yes']['sample'].nunique()
        st.metric("👍 Responder Samples", responders, help="Melanoma patients who responded to miraclib treatment")
    
    with col2:
        non_responders = data['comparison'][data['comparison']['response'] == 'no']['sample'].nunique()
        st.metric("👎 Non-Responder Samples", non_responders, help="Melanoma patients who did not respond to miraclib treatment")
    
    with col3:
        total_analyzed = responders + non_responders
        st.metric("🧪 Total Analyzed", total_analyzed, help="Total samples included in statistical analysis")
    
    # Enhanced comparison data display
    st.markdown("---")
    display_enhanced_dataframe(
        df=data['comparison'],
        title="Responder vs Non-Responder Comparison Data",
        description="Filtered dataset used for statistical analysis: melanoma patients receiving miraclib treatment (PBMC samples only). Each row shows cell type frequency for one sample.",
        max_rows=100
    )
    
    # Interactive visualization
    st.markdown("### 📊 Interactive Comparison Visualization")
    
    # Visualization controls
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("**Chart Options:**")
        chart_type = st.selectbox(
            "Visualization type:",
            ["Box Plot", "Violin Plot", "Strip Plot", "Bar Chart (Means)"]
        )
        
        show_points = st.checkbox("Show individual points", value=False)
        
        selected_cells = st.multiselect(
            "Select cell types:",
            options=data['comparison']['population'].unique(),
            default=data['comparison']['population'].unique()
        )
    
    with col2:
        if selected_cells:
            plot_data = data['comparison'][data['comparison']['population'].isin(selected_cells)]
            
            if chart_type == "Box Plot":
                fig = create_enhanced_boxplot(
                    df=plot_data,
                    title="Cell Population Frequencies: Responders vs Non-Responders",
                    x_col='population',
                    y_col='percentage',
                    color_col='response'
                )
                if show_points:
                    fig.update_traces(boxpoints='all', jitter=0.3)
                    
            elif chart_type == "Violin Plot":
                fig = px.violin(
                    plot_data,
                    x='population',
                    y='percentage',
                    color='response',
                    title="Cell Population Frequencies: Responders vs Non-Responders (Violin Plot)",
                    box=True,
                    color_discrete_map={'yes': '#27ae60', 'no': '#e74c3c'}
                )
                fig.update_layout(height=500, showlegend=True)
                
            elif chart_type == "Strip Plot":
                fig = px.strip(
                    plot_data,
                    x='population',
                    y='percentage',
                    color='response',
                    title="Cell Population Frequencies: Individual Samples",
                    color_discrete_map={'yes': '#27ae60', 'no': '#e74c3c'}
                )
                fig.update_layout(height=500, showlegend=True)
                
            else:  # Bar Chart
                mean_data = plot_data.groupby(['population', 'response'])['percentage'].agg(['mean', 'std']).reset_index()
                fig = px.bar(
                    mean_data,
                    x='population',
                    y='mean',
                    color='response',
                    error_y='std',
                    title="Mean Cell Population Frequencies with Standard Deviation",
                    color_discrete_map={'yes': '#27ae60', 'no': '#e74c3c'}
                )
                fig.update_layout(height=500, showlegend=True)
            
            fig.update_layout(
                height=500,
                xaxis_tickangle=45,
                legend_title="Treatment Response"
            )
            st.plotly_chart(fig, use_container_width=True)


def show_enhanced_baseline_analysis(data):
    st.markdown('<div class="section-header">🎯 Part 4: Baseline Data Analysis</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    <strong>Analysis Focus:</strong> Melanoma PBMC samples at baseline (time=0) treated with miraclib<br>
    <strong>Purpose:</strong> Explore early treatment effects and understand patient demographics<br>
    <strong>Filter Criteria:</strong> Condition=melanoma, Treatment=miraclib, Time=0, Sample_type=PBMC
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced metrics
    st.markdown("### 📊 Baseline Dataset Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Total Subjects", len(data['baseline']), help="Unique subjects at baseline")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        responders = len(data['baseline'][data['baseline']['response'] == 'yes'])
        response_rate = (responders / len(data['baseline']) * 100)
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Responders", f"{responders} ({response_rate:.1f}%)", help="Subjects who responded to treatment")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        males = len(data['baseline'][data['baseline']['sex'] == 'M'])
        male_rate = (males / len(data['baseline']) * 100)
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Males", f"{males} ({male_rate:.1f}%)", help="Male subjects in baseline cohort")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        projects = data['baseline']['project_code'].nunique()
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Projects", projects, help="Number of different projects")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Enhanced visualizations
    st.markdown("### 📈 Demographic Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Project distribution
        project_counts = data['baseline']['project_code'].value_counts()
        fig = create_enhanced_pie_chart(
            data=project_counts.values,
            labels=project_counts.index,
            title="Distribution by Project",
            colors=['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Response distribution
        response_counts = data['baseline']['response'].value_counts()
        response_labels = ['Responders' if x == 'yes' else 'Non-responders' for x in response_counts.index]
        fig = create_enhanced_pie_chart(
            data=response_counts.values,
            labels=response_labels,
            title="Treatment Response Distribution",
            colors=['#27ae60', '#e74c3c']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Cross-tabulation analysis
    st.markdown("### 📋 Cross-Tabulation Analysis")
    
    tab1, tab2, tab3 = st.tabs(["Project vs Response", "Project vs Sex", "Response vs Sex"])
    
    with tab1:
        st.markdown("**Breakdown by Project and Treatment Response:**")
        crosstab1 = pd.crosstab(
            data['baseline']['project_code'], 
            data['baseline']['response'].map({'yes': 'Responders', 'no': 'Non-responders'}),
            margins=True, 
            margins_name="Total"
        )
        st.dataframe(crosstab1, use_container_width=True)
        
        # Stacked bar chart
        crosstab_pct = pd.crosstab(
            data['baseline']['project_code'], 
            data['baseline']['response'].map({'yes': 'Responders', 'no': 'Non-responders'}),
            normalize='index'
        ) * 100
        
        fig = px.bar(
            crosstab_pct, 
            title="Response Rate by Project (%)",
            color_discrete_map={'Responders': '#27ae60', 'Non-responders': '#e74c3c'}
        )
        fig.update_layout(yaxis_title="Percentage (%)", xaxis_title="Project", height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("**Breakdown by Project and Sex:**")
        crosstab2 = pd.crosstab(
            data['baseline']['project_code'], 
            data['baseline']['sex'].map({'M': 'Males', 'F': 'Females'}),
            margins=True, 
            margins_name="Total"
        )
        st.dataframe(crosstab2, use_container_width=True)
    
    with tab3:
        st.markdown("**Breakdown by Response and Sex:**")
        crosstab3 = pd.crosstab(
            data['baseline']['response'].map({'yes': 'Responders', 'no': 'Non-responders'}),
            data['baseline']['sex'].map({'M': 'Males', 'F': 'Females'}),
            margins=True, 
            margins_name="Total"
        )
        st.dataframe(crosstab3, use_container_width=True)
    
    # Enhanced baseline data display
    st.markdown("---")
    display_enhanced_dataframe(
        df=data['baseline'],
        title="Baseline Sample Dataset",
        description="Complete dataset of melanoma patients receiving miraclib treatment at baseline (time=0). Includes project assignment, demographics, treatment response, and sample information.",
        max_rows=100
    )


def show_enhanced_custom_query():
    st.markdown('<div class="section-header">🔍 Custom Database Query Interface</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    <strong>Interactive SQL Interface:</strong> Run custom queries on the cell count database<br>
    <strong>Database:</strong> SQLite with 6 tables (projects, conditions, treatments, subjects, samples, cell_counts)<br>
    <strong>Use Cases:</strong> Custom analysis, data exploration, hypothesis testing
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced sample queries
    st.markdown("### 📚 Sample Queries")
    
    sample_queries = {
        "📋 Database Schema": "SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name;",
        "📊 Sample Statistics": """
            SELECT 
                c.condition_name,
                t.treatment_name,
                COUNT(DISTINCT s.sample_id) as sample_count,
                COUNT(DISTINCT su.subject_id) as subject_count
            FROM samples s
            JOIN subjects su ON s.subject_id = su.subject_id
            JOIN conditions c ON su.condition_id = c.condition_id
            JOIN treatments t ON su.treatment_id = t.treatment_id
            GROUP BY c.condition_name, t.treatment_name
            ORDER BY sample_count DESC;
        """,
        "🧬 Average Cell Counts by Treatment": """
            SELECT 
                t.treatment_name,
                cc.cell_type,
                AVG(cc.count) as avg_count,
                COUNT(*) as sample_count
            FROM cell_counts cc
            JOIN samples s ON cc.sample_id = s.sample_id
            JOIN subjects su ON s.subject_id = su.subject_id
            JOIN treatments t ON su.treatment_id = t.treatment_id
            WHERE s.time_from_treatment_start = 0
            GROUP BY t.treatment_name, cc.cell_type
            ORDER BY t.treatment_name, avg_count DESC;
        """,
        "👥 Demographics Summary": """
            SELECT 
                c.condition_name,
                su.sex,
                su.response,
                COUNT(*) as subject_count,
                AVG(su.age) as avg_age
            FROM subjects su
            JOIN conditions c ON su.condition_id = c.condition_id
            WHERE su.response != ''
            GROUP BY c.condition_name, su.sex, su.response
            ORDER BY c.condition_name, su.sex, su.response;
        """,
        "⏰ Time Series Analysis": """
            SELECT 
                s.time_from_treatment_start,
                cc.cell_type,
                AVG(cc.count) as avg_count,
                COUNT(*) as sample_count
            FROM samples s
            JOIN cell_counts cc ON s.sample_id = cc.sample_id
            JOIN subjects su ON s.subject_id = su.subject_id
            JOIN conditions c ON su.condition_id = c.condition_id
            WHERE c.condition_name = 'melanoma'
            GROUP BY s.time_from_treatment_start, cc.cell_type
            ORDER BY s.time_from_treatment_start, cc.cell_type;
        """
    }
    
    # Query selection and editing
    col1, col2 = st.columns([1, 2])
    
    with col1:
        selected_query = st.selectbox("Choose a sample query:", list(sample_queries.keys()))
        
        st.markdown("**Query Tips:**")
        st.markdown("""
        - Use `LIMIT 100` for large results
        - Join tables using foreign keys
        - Filter with `WHERE` conditions
        - Group data with `GROUP BY`
        - Sort results with `ORDER BY`
        """)
    
    with col2:
        # Query input with syntax highlighting
        query = st.text_area(
            "SQL Query:", 
            value=sample_queries[selected_query], 
            height=200,
            help="Enter your SQL query here. Click 'Execute Query' to run it."
        )
    
    # Execute query
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        execute_button = st.button("🚀 Execute Query", type="primary")
    
    with col2:
        clear_button = st.button("🧹 Clear Query")
        if clear_button:
            st.rerun()
    
    if execute_button and query.strip():
        with st.spinner("Executing query..."):
            result = query_database(query)
            
            if result is not None and not result.empty:
                st.markdown("### 📊 Query Results")
                
                # Show result metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Rows Returned", len(result))
                with col2:
                    st.metric("Columns", len(result.columns))
                with col3:
                    if len(result) > 0:
                        st.metric("Data Types", result.dtypes.nunique())
                
                # Display results with pagination
                display_enhanced_dataframe(
                    df=result,
                    title="Query Results",
                    description=f"Results from custom SQL query. Showing data from the cell count database.",
                    max_rows=100
                )
                
                # Optional visualization for numeric results
                if len(result.select_dtypes(include=[np.number]).columns) >= 2:
                    st.markdown("### 📈 Quick Visualization")
                    numeric_cols = result.select_dtypes(include=[np.number]).columns.tolist()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        x_col = st.selectbox("X-axis:", numeric_cols + ['index'])
                        y_col = st.selectbox("Y-axis:", numeric_cols)
                    
                    with col2:
                        if st.button("Generate Plot"):
                            if x_col == 'index':
                                fig = px.line(result.reset_index(), x='index', y=y_col, title=f"{y_col} over Index")
                            else:
                                fig = px.scatter(result, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
                            fig.update_layout(height=400)
                            st.plotly_chart(fig, use_container_width=True)
                            
            elif result is not None and result.empty:
                st.warning("⚠️ Query executed successfully but returned no results.")
            else:
                st.error("❌ Query failed. Please check your SQL syntax and try again.")
    
    elif execute_button:
        st.warning("⚠️ Please enter a SQL query before executing.")


if __name__ == "__main__":
    main()