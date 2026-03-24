.PHONY: test autoresearch explore random all

test:
	uv run pytest tests/ -v

autoresearch:
	uv run python run_autoresearch.py --experiments 200 --seed 42 -w 4

explore:
	uv run python run_autoresearch.py --experiments 200 --seed 42 --exploit 0.2 --explore 0.6 --random 0.2 -w 4

random:
	uv run python run_autoresearch.py --experiments 200 --seed 42 --exploit 0.2 --explore 0.2 --random 0.6 -w 4

all:
	$(MAKE) explore & $(MAKE) random & wait
