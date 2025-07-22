check:
	-flake8 --max-line-length 100 */*.py */*.py
	-mypy --strict */*.py

.PHONY: check
