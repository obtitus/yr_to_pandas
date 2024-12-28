install:
	poetry install

install_dev: install
	poetry run pre-commit install
	(cd ..;git clone https://github.com/obtitus/yr_to_pandas.git yr_to_pandas_gh_pages;cd yr_to_pandas_gh_pages;git checkout gh_pages)

# running lint with `poetry run pre-commit run --all-files` fails, no clue why
lint:
	pre-commit run --all-files

test:
	poetry run python -m yr_to_pandas.yr_client
	poetry run python -m yr_to_pandas.yr_examples

doc:
	(cd docs;make html)

push_doc:
	(cd ../yr_to_pandas_gh_pages;make push_doc)

doc_auto:
	poetry run when-changed -r yr_to_pandas "make doc"
