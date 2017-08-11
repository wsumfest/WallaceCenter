import sys
import os
from os.path import join, dirname
from dotenv import load_dotenv
import requests
import json
import subprocess
import datetime
import csv
import simulate_keywords
import gspread
import openpyxl


ANALYSIS_URL = "https://docs.google.com/spreadsheets/d/1IK1cvWz13IP22t-SdlZMmrzdc5R-LZMTBjS7QCBRdlY/edit#gid=0"
LEN_OF_SPREADSHEET = 9000

LOCAL_ANALYSIS_SHEET = "excel_sheets/sites.xlsx"


"""
Receives a list of WORDS and a CASE NUMBER as inputs. Our function then makes a search using Google's API,
parses through the first ten sites in the results for each search and writes the appropriate attributes to 
a csv file in OUTPUT/SEARCH. 
"""
def main(words, case_num, code="US-CA"):
    head, tail = os.path.split(dirname(__file__))
    dotenv_path = join(head, '.env')
    load_dotenv(dotenv_path)
    params = {
        'url' : 'www.googleapis.com/customsearch/v1',
        'cx' : os.environ.get('SEARCH_PARAM_CX'),
        'key' : os.environ.get('TRENDS_DEVELOPER_KEY'),
    }
    output_dir = os.getcwd() + "/output/search/" + code
    simulate_keywords.Simulation.mkdir_p(output_dir)
    name = output_dir + "/" + datetime.datetime.now().strftime('%Y-%m-%d-%H:%M') + ".csv"
    with open(name, "wb") as csvfile:
        field_names = ["case", "word", "position", "link", "displayLink", "country"]
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        writer.writeheader()
        for word in words:
            params['q'] = word
            try:
                text = u'https://{url}?q={q}&cx={cx}&key={key}'.format(**params)
                reponse = requests.get(text.encode("utf8"))
                data = json.loads(reponse.text)
            except requests.exceptions.SSLError as e:
                print e
                pass 

            try:
                if data["error"]["code"] == 403:
                    #do some error correcting
                    raise Exception("Over our search quota for today.")
            except:
                index = 1
                try:
                    for item in data["items"]:
                        display_link = item["displayLink"]
                        p = subprocess.Popen(["geoiplookup", display_link], stdout=subprocess.PIPE)
                        country, err = p.communicate()
                        country_only = find_country(country)
                        word = u"{0}".format(word)
                        writer.writerow({"case": str(case_num), "word": word, "position": str(index), "link": item["link"], "displayLink": display_link, "country": country_only})
                        index += 1
                    index = 1
                except UnicodeEncodeError as e:
                    print e
                    continue
                except KeyError:
                    continue
    send_data(name)
    return 




"""
Receives an input string COUNTRY that is return by geoiplookup. We are only interested in the country version,
which is given in the first line of the string. We then strip the header and return a string of the counrty name 
only.
"""
def find_country(country):
    country_only = country.splitlines()[0]
    country_only = country_only[23:]
    return country_only

"""
Sends data from last simulation to a Google Spreadsheet for analysis.
"""
def send_data(filename):

    local_validation = os.getcwd() + "/" + LOCAL_ANALYSIS_SHEET
    workbook = openpyxl.load_workbook(local_validation)
    sheet = workbook.get_sheet_by_name('sites')
    sites = [row[0].value for row in sheet.rows]
    next_row = len(sites) + 1

    with open(filename, "rb") as out_file:
        reader = csv.DictReader(out_file)

        for row in reader:
            display_link = row["displayLink"]
            if display_link not in sites:
                concat = "A" + str(next_row)
                sheet[concat] = display_link
                next_row += 1

    workbook.save(filename= os.getcwd() + "/" + LOCAL_ANALYSIS_SHEET)
    return


"""
Gets the first Empty row in a worksheet. This requires a network connection.
"""
def return_first_row(worksheet):
    index = 1
    values = worksheet.col_values(1)
    while index < LEN_OF_SPREADSHEET:
        value = values[index]
        if value == "":
            return index + 1
        else:
            index += 1
    return



if __name__ == '__main__':
    case_num = sys.argv[1]
    words = sys.argv[2:]
    main(words, case_num)