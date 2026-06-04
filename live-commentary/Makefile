.PHONY: install dev demo test lint
install:
	pip install -e .
dev:
	pip install -e ".[live,voice,dotenv]"
demo:
	python -m livecommentary demo --speed 6
test:
	python -m unittest discover -s tests -v
