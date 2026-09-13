.PHONY: setup pipeline dashboard clean

setup:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "Verifying streamlit installation..."
	@python -c "import streamlit; print('Streamlit version:', streamlit.__version__)" || (echo "Streamlit installation failed" && exit 1)
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
	@if command -v streamlit >/dev/null 2>&1; then \
		echo "Using streamlit command..."; \
		streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0; \
	else \
		echo "Using python -m streamlit..."; \
		python -m streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0; \
	fi

clean:
	@echo "Cleaning up generated files..."
	rm -f *.db *.csv *.png
	@echo "Cleanup completed!"