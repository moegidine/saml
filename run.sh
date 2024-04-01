#!/bin/bash

python3.9 -m venv venv

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "There is no virtual environment created."
    exit 1
fi

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt >pip.log 2>&1
else
    echo "requirements.txt not found."
    exit 1
fi

export FLASK_DEBUG=0

if cd app; then
    FLASK_HOST="127.0.0.1" FLASK_PORT="30000" python main.py >app.log 2>&1 &
    app_pid=$!
    cd ..
else
    echo "app directory not found."
    exit 1
fi

if cd sp; then
    FLASK_HOST="127.0.0.1" FLASK_PORT="20000" python main.py >sp.log 2>&1 &
    sp_pid=$!
    cd ..
else
    echo "idp directory not found."
    kill $app_pid
    exit 1
fi

if cd idp; then
    FLASK_HOST="127.0.0.1" FLASK_PORT="11000" python main.py >idp.log 2>&1 &
    idp_pid=$!
    cd ..
else
    echo "idp directory not found."
    kill $app_pid
    kill $sp_pid
    exit 1
fi

if cd dse; then
    FLASK_HOST="127.0.0.1" FLASK_PORT="10000" python main.py >dse.log 2>&1 &
    dse_pid=$!
    cd ..
else
    echo "idp directory not found."
    kill $app_pid
    kill $sp_pid
    kill $idp_pid
    exit 1
fi

echo "APP, SP, IDP, DSE are running."

while true; do
    read -p "Do you want to stop APP, SP, IDP, DSE ? (y/n): " yn
    case $yn in
        [Yy]* ) kill $app_pid; kill $sp_pid; kill $idp_pid; kill $dse_pid; break;;
        * ) echo "Type Y/y to quit...";;
    esac
done
