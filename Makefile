.PHONY: clean run

all: clean run

clean:
	rm -f img/*.png
	rm -f frames/*.png
	rm -f out.mp4

run:
	python app.py
