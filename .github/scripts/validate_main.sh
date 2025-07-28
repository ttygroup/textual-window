#!/usr/bin/env bash
set -euo pipefail

# Check if on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
	echo "Error: You are not on the main branch. Please switch to main."
	exit 1
fi

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
	echo "Error: There are uncommitted changes. Please commit or stash them."
	exit 1
fi

# Fetch latest changes from remote
git fetch

# Check if local main is up to date with origin/main
if ! git rev-parse origin/main > /dev/null 2>&1; then
	echo "Error: Remote branch origin/main does not exist. Please set up a remote tracking branch."
	exit 1
fi
LOCAL_HASH=$(git rev-parse main)
REMOTE_HASH=$(git rev-parse origin/main)
if [ "$LOCAL_HASH" != "$REMOTE_HASH" ]; then
	echo "Error: Your local main branch is not up to date with origin/main. Please pull the latest changes."
	exit 1
fi