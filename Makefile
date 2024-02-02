# Makefile

install:
	# Make sure the gas-station server is already clone
	python -m venv env && \
	. env/bin/activate && \
	pip install -r requirements.txt

start:
	# Start gas-station server
	. env/bin/activate && \
	uvicorn src.main:app --host 0.0.0.0 --reload

test:
	pytest

clean:
	# Clean up Python project
	rm -rf env
	find . -name '*.pyc' -delete
	rm -rf build dist *.egg-info
	rm -f *.log

#start_database: service postgresql start
# check status: service postgresql status
# connect to the specific database: psql -h localhost -U gas_user -d gas_station

# show database: \l
# show tables: \dl
