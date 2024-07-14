.PHONY: install-hooks run-hooks install-hooks update add-requirements

# Install pre-commit hooks
install-hooks:
	pre-commit install

# Run pre-commit hooks on all files
run-hooks:
	pre-commit run --all-files

# Install pre-commit hooks
install-hooks:
	pre-commit install

# update packages
update:
	pip install --upgrade pip
	poetry update
	pre-commit autoupdate

# add requirements
add-requirements:
	poetry export -f requirements.txt --output requirements.txt --without-hashes
