.PHONY: clean run

all: clean run

clean:
	rm -f img/*.png
	rm -f frames/*.png

run:
	python app.py
