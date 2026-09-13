.PHONY: setup pipeline dashboard clean

setup:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "Dependencies installed successfully!"

pipeline:
	@echo "Starting data pipeline..."
	@echo "Step 1: Creating database and loading data..."
	python load_data.py
	@echo "Step 2: Analyzing cell frequencies..."
	python analyze_frequency.py
	@echo "Step 3: Performing statistical analysis..."
	python statistical_analysis.py
	@echo "Step 4: Running baseline data analysis..."
	python data_subset_analysis.py
	@echo "Pipeline completed successfully!"

dashboard:
	@echo "Starting dashboard server..."
	python -m streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0

clean:
	@echo "Cleaning up generated files..."
	rm -f *.db *.csv *.png
	@echo "Cleanup completed!"