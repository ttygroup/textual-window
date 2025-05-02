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

# Run the tmux script (see tmux.sh for details)
tmux:
	chmod +x tmux.sh
	./tmux.sh

# Build the package, run clean first
build: clean
	@echo "Building the package..."
	uv build
	
# Publish the package, run build first
publish: build
	@echo "Publishing the package..."
	uv publish

# Remove the build and dist directories
clean:
	rm -rf build dist
	find . -name "*.pyc" -delete

# Remove the virtual environment and lock file
del-env:
	rm -rf .venv
	rm -rf uv.lock

reset: clean del-env install
	@echo "Resetting the environment..."
#-------------------------------------------------------------------------------