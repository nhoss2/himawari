.PHONY: clean run test

all: clean run

clean:
	rm -rf frames/*
	rm -f out.mp4

run:
	python app.py

test:
	py.test test
