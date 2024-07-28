.PHONY: install-hooks run-hooks install-hooks update add-requirements clean-pycache install-requirements

install-hooks:
	pre-commit install

run-hooks:
	pre-commit run --all-files

update:
	pip install --upgrade pip
	poetry update
	pre-commit autoupdate

clean-pycache:
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type f -name '*.pyc' -exec rm -f {} +

add-requirements:
	poetry export -f requirements.txt --output requirements.txt --without-hashes

install-requirements:
	poetry install --no-root

run-script:
	python run_scripts/github_download.py
