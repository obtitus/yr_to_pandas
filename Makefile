push_doc: copy_docs
	git add -A .
	git com -am "updated docs"
	git push

copy_docs: create_doc
	rsync -r ../yr_to_pandas/docs/_build/html/ .

create_doc:
	(cd ../yr_to_pandas/docs/;make html)
