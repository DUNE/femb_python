#!/bin/bash

# This spews stuff expecting to get live output for testing under a
# Sumatra runner.

dofail=${1}

echo "live-spew $@"

for n in {0..3}
do
    date
    echo "message number $n to stdout"
    echo "message number $n to stderr" 1>&2
    sleep 1
done

if [ "$dofail" = "fail" ] ; then
    echo "live-spew.sh will fail now"
    echo "live-spew.sh will fail now" 1>&2
    exit 1
fi

exit 0
