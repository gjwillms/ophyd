#!/bin/bash
# Requires: the example IOCs to be running
# Requires: python-nose, python-coverage

script_path="`dirname \"$0\"`"
script_path="`( cd \"$script_path\" && pwd )`"
if [ -z "$script_path" ] ; then
    echo "Unable to get script path"
    exit 1
fi

motor_pv=XF:31IDA-OP{Tbl-Ax:FakeMtr}-I
areadet_pv=XF:31IDA-BI{Cam:Tbl}image1:Dim0SA

motor_val=$(caget -t $motor_pv 2>/dev/null)
areadet_val=$(caget -t $areadet_pv 2>/dev/null)

fail() {
    echo "**ERROR** TThe $1 is not running or is inaccessible from this network.  See ophyd.git/examples/iocs."
    echo ""
    echo "These tests assume the motor IOC example and the areaDetector IOC example are running."
    echo "PVs checked for:"
    echo "  $motor_pv (='$motor_val')"
    echo "  $areadet_pv (='$areadet_val')"
    exit 1
}

[ -z "$motor_val" ] && fail "Motor IOC"
[ -z "$areadet_val" ] && fail "areaDetector example IOC"
[ -d "doc" ] || (echo "Unable to find doc path" && exit 1)

cd $script_path/..

COVERAGE_HTML=doc/coverage
rm -rf $COVERAGE_HTML
mkdir $COVERAGE_HTML
nosetests --with-coverage --cover-erase --cover-html --cover-html-dir=$COVERAGE_HTML \
          --cover-tests --cover-package=ophyd --where=test -v
          # --cover-tests --cover-package=ophyd --tests=test.test_signal -v

view setup.py -c ":Coveragepy report"
