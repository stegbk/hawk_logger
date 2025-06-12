include .env

.PHONY: test

test:
	@echo "Running tests with PYTHONPATH=src"
	@OPENAI_API_KEY=$(OPENAI_API_KEY) \
	MONGODB_URI=$(MONGODB_URI) \
	DOCKER_HOST=$(DOCKER_HOST) \
	PYTHONPATH=src .venv/bin/python -m pytest src/tests/test_hawk_logger_lambda.py
clean:
	python3 src/tests/clean_test_data.py

regression: clean
	@echo "Running regression suite..."
	PYTHONPATH=src pytest src/tests/test_regression_suite.py
	
