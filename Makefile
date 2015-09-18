# This makefile handles some python package management activities.


all: README.rst

README.rst: README.md
	pandoc -o $@ $<

clean:
	rm -rf dist

dist:
	python setup.py sdist
	python setup.py bdist_wheel

