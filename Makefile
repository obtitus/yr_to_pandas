install:
	poetry install

install_dev: install
	poetry run pre-commit install
