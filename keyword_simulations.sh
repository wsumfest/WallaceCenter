CASE="2"
CC="100.0"
BC="70.0"
FULL_SIMULATION="1"
START_DATE="2015-07"
END_DATE="2016-07"
python search/simulate_keywords.py $CASE $START_DATE $END_DATE $FULL_SIMULATION
CODE=$?
CODE=0
if [[ $CODE -eq 0 ]]
then
    python analysis/main.py $CASE $CC $BC
    python analysis/write_graphs.py $REGION1 $REGION2
else
    echo "An error occurred, check output"   
fi
