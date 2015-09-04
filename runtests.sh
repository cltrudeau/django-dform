#!/bin/bash

find . -name "*.pyc" -exec rm {} \;
coverage run -p --source=dform --omit="runtests.py" ./tests.py
if [ "$?" = "0" ]; then
    coverage combine
    echo -e "\n\n================================================"
    echo "Test Coverage"
    coverage report
    echo -e "\nrun \"coverage html\" for full report"
    echo -e "\n"
fi
