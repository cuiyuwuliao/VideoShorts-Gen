#!/bin/bash

echo "========================================"
echo "          GIT PULL SCRIPT"
echo "========================================"
echo ""

# Use the directory where this script is located
REPO_DIR="$(dirname "$0")"
cd "$REPO_DIR" || exit

echo "Repository directory: $REPO_DIR"
echo ""

# Check if this is a git repository
if ! git status > /dev/null 2>&1; then
    echo "ERROR: This is not a Git repository!"
    echo "Please run this script from your Git project folder."
    exit 1
fi

echo "Pulling latest changes from remote..."
git pull origin main

echo ""
echo "========================================"
echo "Pull completed successfully!"
echo "========================================"