#!/bin/sh

source venv/bin/activate
python poll_results_checker.py &
python poll_creator.py &
