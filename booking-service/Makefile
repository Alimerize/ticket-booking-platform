.PHONY: install test test-unit test-integration lint clean

install:
	pip install -r requirements-dev.txt

test:
	pytest -v

test-unit:
	pytest -v -m unit

test-integration:
	pytest -v -m integration

lint:
	ruff check app tests || true

clean:
	rm -rf .pytest_cache .coverage coverage.xml htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +