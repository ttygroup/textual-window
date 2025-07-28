# Install the package
install:
	uv sync

# Run the demo with defined entry command
run:
	uv run textual-window

# Run the demo in dev mode
run-dev:
	uv run textual run --dev textual_window.demo:WindowDemo

# Run the console
console:
	uv run textual console -x EVENT -x SYSTEM

# Runs ruff, exits with 0 if no issues are found
lint:
  @uv run ruff check src || (echo "Ruff found issues. Please address them." && exit 1)

# Runs mypy, exits with 0 if no issues are found
typecheck:
  @uv run mypy src || (echo "Mypy found issues. Please address them." && exit 1)
  @uv run basedpyright src || (echo "BasedPyright found issues. Please address them." && exit 1)

# Runs black
format:
  @uv run black src

# Runs ruff, mypy, and black
all-checks: lint typecheck format
  echo "All pre-commit checks passed. You're good to PR to main."

# Remove build/dist directories and pyc files
clean:
  rm -rf build dist
  find . -name "*.pyc" -delete

# Remove tool caches
clean-caches:
  rm -rf .mypy_cache
  rm -rf .ruff_cache

# Remove the virtual environment and lock file
del-env:
  rm -rf .venv
  rm -rf uv.lock

# Removes all environment and build stuff
reset: clean clean-caches del-env install
  @echo "Environment reset."

# Release the kraken
release:
  bash .github/scripts/validate_main.sh && \
  uv run .github/scripts/tag_release.py && \
  git push --tags

sync-tags:
  git fetch --prune origin "+refs/tags/*:refs/tags/*"