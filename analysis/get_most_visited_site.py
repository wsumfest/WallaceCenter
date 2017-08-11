import sys
import csv
import operator
import datetime
import os


def main(filename):
    most_visited_object = MostVisitedSites(filename)
    most_visited_object.simulation()
    return most_visited_object.find_nth_max()

class MostVisitedSites(object):

    def __init__(self, filename, NUMBER=10):
        self.filename = filename
        self.site_dictionary = dict()
        self.num = NUMBER

    def get_filename(self):
        return self.filename

    def get_site_dictionary(self):
        return self.site_dictionary

    def put_site_dictionary(self, new_dictionary):
        self.site_dictionary = new_dictionary
        return 

    @classmethod
    def get_probability(cls, position):
        if position == "1":
            return 0.35
        elif position == "2":
            return 0.20
        elif position == "3":
            return 0.15
        elif position == "4":
            return 0.08
        elif position == "5":
            return 0.07
        elif position == "6":
            return 0.05
        elif position == "7":
            return 0.04
        elif position == "8":
            return 0.03
        elif position == "9":
            return 0.02
        else:
            return 0.01

    def simulation(self):
        site_dict = {}
        case = "0"
        filename = self.get_filename()
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                case = row["case"]
                position = row["position"]
                display_link = row["displayLink"]
                if display_link not in site_dict:
                    site_dict[display_link] = MostVisitedSites.get_probability(position)
                else:
                    site_dict[display_link] += MostVisitedSites.get_probability(position)
        self.put_site_dictionary(site_dict)
        return

    def find_nth_max(self):
        site_dict = self.get_site_dictionary()
        new_n = min(self.num, len(site_dict))
        sorted_keys = sorted(site_dict, key=lambda k: site_dict[k], reverse=True)
        return sorted_keys[:new_n]


if __name__ == '__main__':
    assert len(argv) == 2
    filename = sys.argv[1]
    main(filename)