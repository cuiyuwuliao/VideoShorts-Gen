#!/bin/bash

# Check if Python is installed
python3 --version > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Python is not installed or not in PATH."
    echo "Please install Python from https://www.python.org/downloads/"
    echo "After installation, make sure to check 'Add Python to PATH' during installation."
    exit 1
fi

# Navigate to the script's directory
cd "$(dirname "$0")"

# Install required packages
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "Setup Complete! (^>_^<) ..."