.PHONY: install-hooks run-hooks install-hooks update add-requirements clean-pycache

# Install pre-commit hooks
install-hooks:
	pre-commit install

# Run pre-commit hooks on all files
run-hooks:
	pre-commit run --all-files

# update packages
update:
	pip install --upgrade pip
	poetry update
	pre-commit autoupdate

# clean-pycache:
#     @echo "Removing __pycache__ directories and .pyc files..."
#     @find . -type d -name '__pycache__' -exec rm -rf {} +
#     @find . -type f -name '*.pyc' -exec rm -f {} +

# add requirements
add-requirements:
	poetry export -f requirements.txt --output requirements.txt --without-hashes

run-script:
	python run_scripts/github_download.py
