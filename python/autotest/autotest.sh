#version 0.1.0
#!/usr/bin/env bash

AUTOTEST_COMMAND=$0
AUTOTEST_OPTION=$*

AUTOTEST_DATA_FILE="autotest.data"

function help() {
cat<<EOF
your input:
"$AUTOTEST_COMMAND $AUTOTEST_OPTION"
usage:
"$AUTOTEST_COMMAND <option>"
option:
    - record
    - run
example:
"$AUTOTEST_COMMAND record" to record input event.
"$AUTOTEST_COMMAND run" to run autotest.
EOF
}

if [ $# != 1 ]; then
    help
    exit
fi

if [ $1 != "record" -a $1 != "run" ]; then
    help
    exit
fi

function record() {
    echo "autotest record begin..."
    echo "press Ctrl+C to quit."
    trap "echo ...autotest record end" INT
    getevent &> /data/autotest.record
}

function run() {
    echo "autotest run begin..."
    $SHELL $AUTOTEST_DATA_FILE
    echo "...autotest run end"
}

if [ $AUTOTEST_OPTION == "record" ]; then
    record
else
    run
fi