install:
	poetry install

install_dev: install
	poetry run pre-commit install

lint:
	poetry run pre-commit run --all-files

run:
	poetry run python -m yr_to_pandas.yr_client

doc:
	(cd docs;make html)

doc_auto:
	poetry run when-changed -r yr_to_pandas "make doc"
