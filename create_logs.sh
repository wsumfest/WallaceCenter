mkdir -p output
mkdir -p output/search
mkdir -p output/keywords
mkdir -p census/simulations
mkdir -p analysis/logs
mkdir -p census/analysis/counties
mkdir -p census/analysis/zip_codes
mkdir -p log
if [ ! -f log/keyword_simulations.log ]; then
    touch log/keyword_simulations.log
fi
