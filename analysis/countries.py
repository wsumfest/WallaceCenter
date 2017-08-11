import os
import sys
import numpy 
import csv
from get_most_visited_site import MostVisitedSites

def main(filename):
    country_file = Country(filename)
    return country_file.get_proportion(), country_file.get_probability()


class Country(object):

    def __init__(self, filename):
        self.filename = filename

    def get_filename(self):
        return self.filename
    
    def get_proportion(self):
        filename = self.get_filename()
        total, num = 0,0
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                total += 1
                if row["country"] == "US, United States":
                    num += 1
        return (float(float(num)/float(total)) * 100)

    def get_probability(self):
        filename = self.get_filename()
        num_sites, us_prob = 0, 0
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                ### Only increment counter on first position because we're looking at relative frequencies ###
                if row["position"] == "1":
                    num_sites += 1
                if row["country"] == "US, United States":
                    us_prob += MostVisitedSites.get_probability(row["position"])
        return ((us_prob / float(num_sites)) * 100)

if __name__ == '__main__':
    assert len(argv) == 2
    main(filename)