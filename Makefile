.PHONY: clean run

all: clean run

clean:
	rm img/*.png
	rm frames/*.png

run:
	python app.py
