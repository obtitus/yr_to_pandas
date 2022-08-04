install:
	poetry install

install_dev: install
	poetry run pre-commit install

lint:
	poetry run pre-commit run --all-files

run:
	poetry run python yr_to_pandas/yr_client.py
