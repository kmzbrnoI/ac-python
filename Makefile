check:
	-flake8 */*.py */*.py
	-mypy --strict */*.py

.PHONY: check
