.PHONY: check lint format test testfast ready dumpinitialdata

check:
	python3 manage.py check

format:
	isort --atomic --skip-glob="venv/*" grunge
	black --exclude="venv/" grunge

lint:
	flake8 grunge
	black --check --exclude="venv/" grunge

test:
	python3 manage.py test

testfast:
	python3 manage.py test --failfast

ready: check lint testfast

dumpinitialdata:
	python manage.py dumpdata --natural-foreign --natural-primary \
		--exclude=admin.logentry --all --indent=2 > grunge/fixtures/initial_data.json
