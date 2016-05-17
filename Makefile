.PHONY: clean run test

all: clean run

clean:
	rm -rf frames/*
	rm -f out.mp4
	rm -rf video_frames/*

run:
	python app.py

test:
	py.test test
