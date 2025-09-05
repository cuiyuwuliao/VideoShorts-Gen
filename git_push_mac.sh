#!/bin/bash

echo "========================================"
echo "          GIT PUSH SCRIPT"
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

# Check git status
echo "Current status:"
git status

echo ""
echo "Adding all changes to staging..."
git add .

echo ""
commit_message="AutoCommit: $(date)"
echo "Committing changes: $commit_message"
git commit -m "$commit_message"

echo ""
echo "Pushing to remote repository..."
git push origin main

echo ""
echo "========================================"
echo "Push completed successfully!"
echo "========================================"