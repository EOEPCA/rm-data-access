#!/bin/bash
echo "Running install.sh"

apt update

echo "Installing packages"
DEBIAN_FRONTEND=noninteractive apt install -y python3-flask gunicorn3 python3-pip

pip3 install -r /requirements.txt

rm -rf /var/lib/apt/lists/*
