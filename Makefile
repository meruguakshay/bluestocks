.PHONY: load test clean ratios report dashboard api

load:
	python -m src.etl.loader

test:
	python -m pytest tests/

ratios:
	python -m src.analytics.ratios

report:
	python -m src.etl.report

dashboard:
	python -m src.etl.dashboard

api:
	python -m src.etl.api

clean:
	powershell -Command "if (Test-Path db/nifty100.db) { Remove-Item db/nifty100.db -Force }"
	powershell -Command "if (Test-Path output/*) { Remove-Item output/* -Force }"
