.PHONY: load test clean ratios report dashboard api

load:
	python src/etl/loader.py

test:
	pytest tests/etl/

ratios:
	python src/etl/ratios.py

report:
	python src/etl/report.py

dashboard:
	python src/etl/dashboard.py

api:
	python src/etl/api.py

clean:
	powershell -Command "if (Test-Path db/nifty100.db) { Remove-Item db/nifty100.db -Force }"
	powershell -Command "if (Test-Path output/*) { Remove-Item output/* -Force }"
