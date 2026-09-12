# Cell Count Analysis Project

A data analysis pipeline for cell count data from clinical trials with database management, statistical analysis, and interactive visualization.

## Project Structure

```
├── cell-count.csv                          # Source data file
├── load_data.py                           # Part 1: Database creation and data loading
├── analyze_frequency.py                   # Part 2: Cell frequency analysis
├── statistical_analysis.py               # Part 3: Statistical comparison
├── data_subset_analysis.py               # Part 4: Baseline data analysis
├── dashboard.py                           # Interactive Streamlit dashboard
├── requirements.txt                       # Python dependencies
├── Makefile                              # Automation commands
├── README.md                             # This file
└── DATABASE_SCHEMA.md                    # Database schema documentation
```

## Installation & Execution

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Quick Start

1. Install dependencies:
   ```bash
   make setup
   ```

2. Run the complete pipeline:
   ```bash
   make pipeline
   ```

3. Start the interactive dashboard:
   ```bash
   make dashboard
   ```

The dashboard will be available at: http://localhost:8501

### Manual Execution

If you prefer to run individual components:

```bash
# Step 1: Create database and load data
python load_data.py

# Step 2: Analyze cell frequencies
python analyze_frequency.py

# Step 3: Statistical analysis
python statistical_analysis.py

# Step 4: Baseline analysis
python data_subset_analysis.py

# Start dashboard
streamlit run dashboard.py
```

## Dashboard Link

Local URL: http://localhost:8501

Note: For GitHub Codespaces, use the forwarded port URL.

## Analysis Parts

### Part 1: Data Management
- Creates normalized SQLite database (cell_count.db)
- Loads 10,500 samples with cell count data
- Implements relational schema with proper indexing

### Part 2: Frequency Analysis
- Calculates relative frequencies for each cell type per sample
- Generates cell_frequency_summary.csv with 52,500 records

### Part 3: Statistical Analysis
- Compares melanoma patients: miraclib responders vs non-responders
- Performs Mann-Whitney U tests for statistical significance
- Creates boxplot visualizations
- Key Finding: CD4 T-cells show significantly higher frequencies in responders (p=0.0134)

### Part 4: Baseline Analysis
- Analyzes melanoma PBMC samples at baseline (time=0) with miraclib treatment
- Provides breakdowns by project, response, and demographics
- 656 baseline samples from 656 subjects

## Output Files

| File | Description |
|------|-------------|
| cell_count.db | SQLite database (4.8 MB) |
| cell_frequency_summary.csv | All sample frequency data (52,500 rows) |
| melanoma_miraclib_comparison.csv | Filtered comparison data (9,840 rows) |
| statistical_results.csv | Statistical test results |
| response_comparison_boxplot.png | Boxplot visualization |
| baseline_melanoma_miraclib_samples.csv | Baseline sample data (656 rows) |
| baseline_summary_stats.csv | Baseline summary statistics |

## Dependencies

- pandas: Data manipulation and analysis
- matplotlib & seaborn: Static plotting
- scipy: Statistical tests
- streamlit: Interactive dashboard
- plotly: Interactive visualizations

## Key Results

### Statistical Significance
- CD4 T-cells: Significant difference between responders and non-responders (p=0.0134)
- Other cell types: No significant differences (p > 0.05)

### Sample Sizes
- Total samples analyzed: 1,968 (melanoma + miraclib + PBMC)
- Responders: 993 samples
- Non-responders: 975 samples

### Baseline Demographics
- Total baseline subjects: 656
- Males: 344, Females: 312
- Projects: prj1 (384 samples), prj3 (272 samples)

## Troubleshooting

### Common Issues

1. Missing dependencies:
   ```bash
   make setup
   ```

2. Database not found:
   ```bash
   make pipeline
   ```

3. Dashboard won't start:
   - Check if port 8501 is available
   - Try: `streamlit run dashboard.py --server.port 8502`

4. Permission errors:
   ```bash
   chmod +x *.py
   ```

## Cleanup

To remove all generated files:
```bash
make clean
```