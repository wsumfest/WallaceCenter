import os
import sys
import csv
import countries
import get_most_visited_site
import datetime


"""
Takes a FILENAME as an input (received as the most recent csv file) and writes a high level representation
of the data in the file. So far, we write the most visited site (highest probability of visiting) as well as
the proportion of sites located in the US and the probability of a user visiting a site in the US.
"""
def main(case, cc):
    BASE = os.getcwd()
    output_dir = BASE + "/analysis/logs"
    name = output_dir + "/" + datetime.datetime.now().strftime('%Y-%m-%d-%H:%M') + ".txt"
    subdirectories = os.popen("ls output/keywords").read()
    subdirectories = format(subdirectories)
    with open(name, "w") as f:
        for sub_dir in subdirectories:
            search_dir_path = BASE + "/output/search/" + "US-CA"
            word_dir_path = BASE + "/output/keywords/" + sub_dir
            os.chdir(search_dir_path)
            last_search_file = max(os.listdir('.'), key = os.path.getctime)
            
            os.chdir(word_dir_path)
            last_words_file = max(os.listdir('.'), key = os.path.getctime)
            last_words_file = word_dir_path + "/" + last_words_file
            last_search_file = search_dir_path + "/" + last_search_file

            most_visited_sites = get_most_visited_site.main(last_search_file)
            us_percent, us_prob = countries.main(last_search_file)
            words = get_words(last_words_file)

        
            f.write("Region: " + write_description_from_region(sub_dir) + ".\n")
            f.write("Case: " + case + ".\n")
            f.write("Correlation For Top Terms: " + cc + ".\n")
            f.write("Correlation For Bottom Terms: " + bc + ".\n")
            f.write("Queries: " +  words + ".\n")
    return

"""
Receives a csv file by FILENAME and returns all the words from a simulation.
"""
def get_words(filename):
    words_list = list()
    with open(filename, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            words_list.append(row["query"])
    return ",".join(words_list)

"""
Writes the sites from SITES into file from HANDLE.
"""
def write_sites(handle, sites):
    get_ordinal_value = lambda n: "%d%s" % (n,"tsnrhtdd"[(n/10%10!=1)*(n%10<4)*n%10::4])
    index = 1
    for site in sites:
        ordinal = get_ordinal_value(index)
        handle.write(ordinal + " Most Visited Site: " + site + ".\n")
        index += 1
    return


"""
Format output.
"""
def format(string):
    sub_dirs = []
    next_dir = ""
    for c in string:
        if c != "\n":
            next_dir += str(c)
        else:
            sub_dirs.append(next_dir)
            next_dir = ""
    return sub_dirs


"""
Gets the description
"""
def write_description_from_region(region):
    filename = "/Users/willsumfest/preto3/search/ca_subcategories.csv"
    with open(filename, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['geo_code'] == region:
                return row["location"]
    return region


if __name__ == '__main__':
    assert len(sys.argv) >= 4
    case = sys.argv[1]
    cc = sys.argv[2]
    bc = sys.argv[3]
    main(case, cc)
