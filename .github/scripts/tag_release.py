# tag_release.py
import sys
import subprocess
import tomli # Or `tomli` for Python < 3.11

# 1. Read the version from the single source of truth
with open("pyproject.toml", "rb") as f:
    pyproject_data = tomli.load(f)
    version = pyproject_data["project"]["version"]

# 2. Construct the tag and the git command
tag = f"v{version}"
print(f"Found version {version}. Creating tag: {tag}")

# 3. Run the git command
try:
    subprocess.run(["git", "tag", tag], check=True)
except subprocess.CalledProcessError:
    print(f"Error: Could not create tag. Does the tag '{tag}' already exist?")
    sys.exit(1)
except FileNotFoundError:
    print("Error: 'git' command not found. Is Git installed and in your PATH?")
    sys.exit(1)
else:
    print(f"Successfully created tag '{tag}'.")
    sys.exit(0)