import sys
import os
from os.path import join, dirname
from dotenv import load_dotenv
import requests
import json
import ast
import numpy
import datetime
import csv
import errno
# import analysis

BASE_URL = "http://api.census.gov/data/2014/acs5"
BASE = "/Users/willsumfest/preto3"
COUNTY_FILE = BASE + "/census/ca_counties.csv"
VARIABLE_FILE = BASE + "/census/categories.json"
ZIP_CODES = []
NULL_RESPONSES = []

"""
Functionality of mkdir -p in unix command line system.
"""
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


"""
gets batch data from params.
"""
def get_batch_data(params, county_code, zip_code):
    url = make_url(params, county=county_code, zip_code=zip_code)
    response = requests.get(url)
    if response.status_code == 204:
        global NULL_RESPONSES
        NULL_RESPONSES = NULL_RESPONSES + [zip_code]
        return None
    try:
        data = ast.literal_eval(response.text)
    except ValueError as e:
        print zip_code + " bad response"
        return None
    return data

"""
Appends data from DATA2 into DATA1, assumes format of [[],[]] for both data.
"""
def append_data(data1, data2):
    data1[0] += data2[0]
    data1[1] += data2[1]
    return data1

"""
Makes a request to the US CENSUS with PARAMETERS.
"""
def make_request(parameters, county_code="", zip_code=""):
    end = len(parameters)
    index, top_value = 0, 50
    data = [[],[]]
    #### In blocks of 50 ####
    while top_value <= end:
        batch_params = parameters[index:top_value]
        data_ = get_batch_data(batch_params, county_code, zip_code)
        if data_ == None:
            return data_
        data = append_data(data, data_)
        index += 50
        top_value += 50
    #### sweep up the remaining if necessary####
    if index < end:
        batch_params = parameters[index:end]
        data_ = get_batch_data(batch_params, county_code, zip_code)
        if data_ == None:
            return data_
        data = append_data(data, data_)
    return data

"""
Function that takes a list of parameters and a county and creates a census url for a request.
Note that the state is 06 since we are working exclusively in california in this stage.
"""
def make_url(parameters, county="", zip_code=""):
    head = dirname(os.getcwd())
    dotenv_path = join(head, '.env')
    load_dotenv(dotenv_path)
    parameters = make_params(parameters)
    print parameters

    if county != "":
        url = BASE_URL + "?get=" + parameters + "&for=county:" + county + "&in=state:06&key=" + os.environ.get('CENSUS_API_KEY')
    elif zip_code != "":
        url = BASE_URL + "?get=" + parameters + "&for=zip+code+tabulation+area:" + zip_code + "&key=" + os.environ.get('CENSUS_API_KEY')
    else:
        url = BASE_URL + "?get=" + parameters + "&for=state:06&key=" + os.environ.get('CENSUS_API_KEY')
    return url


"""
Creates a string from a list of parameters.
"""
def make_params(parameters):
    params = ""
    for item in parameters:
        params += str(item) + ","
    params = params[:-1]
    return params
    
"""
Receives data from the census format and post processes it into relational data to insert into csv file.
We will use this csv file to perform our statistical analysis.
"""
def post_process(data, county_code="", zip_code=""):
    if data == None:
        return 
    a = numpy.asarray(data)
    if county_code != "":
        Dir = os.getcwd() + "/simulations/counties/" + county_code
        mkdir_p(Dir)
        name = Dir + "/" + datetime.datetime.now().strftime('%Y-%m-%d-%H:%M') + ".csv"
    elif zip_code != "":
        Dir = os.getcwd() + "/simulations/zip_codes/" + zip_code
        mkdir_p(Dir)
        name = Dir + "/" + datetime.datetime.now().strftime('%Y-%m-%d-%H:%M') + ".csv"
    else:
        Dir = os.getcwd() + "/simulations/" + "CA_whole"
        mkdir_p(Dir)
        name = Dir + "/" + datetime.datetime.now().strftime('%Y-%m-%d-%H:%M') + ".csv"
    numpy.savetxt(name, a, delimiter=",", fmt="%s")
    return


"""
We need a county and a list of parameters, and we will make an api request to the census.
"""
def main(parameters, is_county_code):
    ### We are using county_code simulations ###
    if is_county_code == "0":
        #For all counties in CA
        with open(COUNTY_FILE, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                county_code = row["county_code"]
                data = make_request(parameters, county_code=county_code)
                post_process(data, county_code=county_code)
    ### We will be using zip_codes ###
    else:
        global ZIP_CODES
        ZIP_CODES = [str(i) for i in range(90001, 96162)]
        for zip_code in ZIP_CODES:
            data = make_request(parameters, zip_code=zip_code)
            post_process(data, zip_code=zip_code)

    #For CA as a whole
    data = make_request(parameters)
    post_process(data)
    # analysis.main(is_county_code, zip_codes=ZIP_CODES, null_responses=NULL_RESPONSES)
    return
    

if __name__ == '__main__':
    os.chdir(BASE + "/census")
    with open(VARIABLE_FILE, "r") as var_file:
        parameters = json.load(var_file).keys()
    main(parameters, sys.argv[1])

