# Makefile
install_gas_station:
	# Make sure the gas-station server is already clone
	python -m venv env && \
	. env/bin/activate && \
	pip install -r requirements.txt


start_gas_station:
	# Start gas-station server
	. env/bin/activate && \
	uvicorn src.main:app --host 0.0.0.0 --reload