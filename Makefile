.PHONY: install run clean

install:
	uv venv
	uv pip install -e "."

run:
	uv run nasa

clean:
	rm -rf .venv
