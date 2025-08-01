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

# note: update the absolute python paths in tox.ini
test_python_versions:
	uv python install cpython-3.9.23-linux-x86_64-gnu \
		cpython-3.10.18-linux-x86_64-gnu \
		cpython-3.11.13-linux-x86_64-gnu \
		cpython-3.12.11-linux-x86_64-gnu \
		cpython-3.13.5-linux-x86_64-gnu

	poetry run tox

doc:
	(cd docs;make html)

push_doc:
	(cd ../yr_to_pandas_gh_pages;make push_doc)

doc_auto:
	poetry run when-changed -r yr_to_pandas "make doc"
