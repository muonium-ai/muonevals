.PHONY: test autoresearch

test:
	python3 -m pytest tests/ -v

autoresearch:
	python3 run_autoresearch.py --experiments 20 --seed 42
