.PHONY: install run test clean

install:
	uv venv
	uv pip install -e "."

run:
	uv run nasa

test:
	uv run --with pytest pytest -q tests

clean:
	rm -rf .venv
