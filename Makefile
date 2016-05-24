.PHONY: run test

all: run

run:
	python himawari/app.py

test:
	py.test tests
