clean:
	rm -rf .pytest_cache
	rm -rf cov_html
	rm -f .coverage
	pip freeze |  awk '{print $1}' | xargs pip uninstall -y

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

run:
	uvicorn api:app --reload

run-tests:
	pytest -o log_cli=true -o log_cli_level=INFO --cov=app --cov-report html:cov_html -x

migrate:
	mongodb-migrate --url mongodb://127.0.0.1:27017/hooks_db