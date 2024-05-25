format-check:
	black --check --diff .
format:
	black .
	isort .
typecheck:
	mypy .
