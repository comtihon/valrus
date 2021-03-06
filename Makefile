make:
	python setup.py bdist_wheel

install: make
	sudo pip install dist/enot-*

tests:
	python -m pytest --capture=sys

deploy: make
	twine upload dist/*

.PHONY: install
