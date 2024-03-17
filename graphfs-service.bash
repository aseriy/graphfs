#!/bin/bash

source ~/git/graphfs/graphfs-env/bin/activate
export PYTHONPATH=~/git/graphfs/binstore/src

cd ~/git/graphfs/binstore
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
