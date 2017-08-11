from os.path import join, dirname
from dotenv import load_dotenv
import os
import logging
import pprint
import sys
import datetime
import pdb
import search
import csv
import errno
import json
from Queue import Queue
import time
import traceback
import openpyxl
from google_client import GoogleClient
import graphviz


class Simulation(object):
    LOG_FILE = "log/keyword_simulations.log"
    EXCEL_WORD_FILE = "excel_sheets/words.xlsx"
    TRENDS_SERVER = "https://www.googleapis.com"
    COUNTIES_FILE = "search/ca_subcategories.csv"
    TRENDS_VERSION = "v1beta"
    K = 1

    def __init__(self, case_number, geoLocation, full_simulation, startDate, endDate):
        self.case_num = case_number
        self.geoLocation = geoLocation
        self.startDate = startDate
        self.endDate = endDate
        self.full_simulation = full_simulation
        self.google_client = GoogleClient(Simulation.TRENDS_SERVER, Simulation.TRENDS_VERSION)
        self.start_case = Simulation.get_case_words(self.case_num)
        self.topics = []
        self.words = []
        self.nextLabelInt = 0
        self.graph = graphviz.Digraph()
        self.mapLabelToNode = dict()

    """
    Functionality of mkdir -p in unix command line system.
    """
    @staticmethod
    def mkdir_p(path):
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise
        return


    """
    Sets the Topics for a given simulation.
    """
    def set_topics(self):
        google_client = self.google_client
        start_case = self.start_case
        topics = google_client.find_topics(start_case, self.geoLocation)
        self.topics = topics
        return topics

    """
    Yields the next node value.
    """
    def nextNodeValue(self):
        self.nextLabelInt += 1
        return str(self.nextLabelInt) 

    """
    Adds a new node to the graph
    """
    def addNodeToGraph(self, sourceLabel, newLabel, isRoot=False):
        if isRoot:
            rootLabelValue = self.nextNodeValue()
            labelValue = self.nextNodeValue()
            self.mapLabelToNode[sourceLabel] = str(rootLabelValue)
            self.mapLabelToNode[newLabel] = str(labelValue)
            self.graph.node(rootLabelValue, sourceLabel)
            self.graph.node(labelValue, newLabel, shape='doublecircle')
            self.graph.edge(rootLabelValue, labelValue)
        else:
            labelValue = self.nextNodeValue()
            self.mapLabelToNode[newLabel] = str(labelValue)
            self.graph.node(labelValue, newLabel)

            print self.mapLabelToNode
            print labelValue
            sourceLabelValue = self.mapLabelToNode[sourceLabel]
            print "Adding edge from " + sourceLabel + " to " + newLabel
            self.graph.edge(sourceLabelValue, str(labelValue))
        return

    """
    Adds a list of source nodes to our graph.
    """
    def addSourceNodesToGraph(self, words):
        for word in words:
            labelValue = self.nextLabelInt()
            self.mapLabelToNode[word] = labelValue
            self.graph.node(labelValue, word)
        return 

    """
    Returns the words that are most popularly searched with the top topics for a region.
    """
    def get_words_related_to_topics(self):
        google_client = self.google_client
        words = google_client.full_request(self.topics, self.geoLocation)
        valid_words = []
        for word in words:
            if Simulation.valid_term_local(word):
                valid_words.append(word)

        return valid_words

    """
    We determine keywords to run simulation over by passing in a NUMBER, we then return an array of string 
    to run our simulation over. Add cases to this function in order to expand our simulation range. If an unknown
    number is passed, we return an error that is to be raised in our generator function.
    """
    @staticmethod
    def get_case_words(num):
        if num == 0:
            return ["pregnancy"]
        elif num == 1:
            return ["fertility"]
        elif num == 2:
            return ["birth control"]
        elif num == 3:
            return ["iud"]
        elif num == 4:
            return ["contraceptive"]
        elif num == 5:
            return ["abortion"]
        elif num == 6:
            return ["emergency contraceptive", "the pill"]
        else:
            raise ValueError("An unknown case number was provided", str(num))


    """
    Function that returns the keywords generated from a seed set. Change the GEOLOCATION to specify the area you wish to 
    cover, CORRELATION is used to decide what level to add a term. Get the developer API from a team member and place it in a .env file in the
    same repo as this file. There are a few places to look out for exceptions in this function. If the keyword_number
    argument is set to an invalid number, a ValueError is raised in our get_case_words function. 
    """
    def generate_keywords(self):
        boolSet = False
        word_queue = Queue()
        ##Build service to trends API with developer key in .env file
        google_client = self.google_client
        if self.full_simulation == "1":
            logging.critical("starting a full simulation")
            try:
                topics = self.set_topics()
                logging.info("Our topics are")
                logging.info(topics)
                if len(topics) >= 1:
                    consolidatedTopic = topics[0]
                    self.addNodeToGraph(self.start_case[0], consolidatedTopic, True)
                    boolSet = True
                key_words = self.get_words_related_to_topics()
                if key_words == []:
                    key_words = self.start_case
            except ValueError as e:
                logging.error("Could not evaluate seed set")
                raise e
        ##To lower runtime of operations
        else:
            logging.critical("starting a small simulation")
            key_words = self.start_case
        soFar = set(key_words)
        if boolSet:
            for word in key_words:
                self.addNodeToGraph(consolidatedTopic, word)


        logging.info("Our key words are: ")
        logging.info(key_words)

        logging.info("Starting simulation with Trends for area: " + self.geoLocation)

        searched_this_cycle = set()

        for item in key_words:
            word_queue.put(item)
        ##Run simulation and determine seeded list, we restrict location based on current ISO-2 codes found at, http://en.wikipedia.org/wiki/ISO_3166-2#Current_codes
        while not word_queue.empty():
            item = word_queue.get(block=False)
            if item in searched_this_cycle:
                continue
            new_words = google_client.make_request(item, self.geoLocation, self.startDate, self.endDate)

            for word in new_words:
                valid_term_boolean = Simulation.valid_term_local(word)
                if not valid_term_boolean:
                    continue

                if word not in soFar:
                    self.addNodeToGraph(item, word)
                    logging.info("adding " + word + " to our seed set.")
                    soFar.add(word)
                    word_queue.put(word)

        new_words_list = list(soFar)
        for word in new_words_list:
            new_words = google_client.make_request(word, self.geoLocation, self.startDate, self.endDate)
            for item in new_words:
                valid_term_boolean = Simulation.valid_term_local(item)
                if not valid_term_boolean:
                    continue

                if item not in soFar:
                    self.addNodeToGraph(word, item)
                    logging.info("adding " + item + " to our seed set.")
                    soFar.add(item)

        for word in new_words_list:
            new_words = google_client.make_request(word, self.geoLocation, self.startDate, self.endDate)
            for item in new_words:
                valid_term_boolean = Simulation.valid_term_local(item)
                if not valid_term_boolean:
                    continue

                if item not in soFar:
                    self.addNodeToGraph(word, item)
                    logging.info("adding " + item + " to our seed set.")
                    soFar.add(item)

        self.words = list(soFar)
        print self.graph.source

        return 


    @classmethod
    def load_excel_workbook(cls):
        local_validation = os.getcwd() + "/" + cls.EXCEL_WORD_FILE
        workbook = openpyxl.load_workbook(local_validation)
        return workbook



    """
    A valiadtion system using local excel sheets rather than google sheets.
    """
    @classmethod
    def valid_term_local(cls, word):
        ### for some reason if yaz band ###
        if word == "yaz band":
            return False
        workbook = Simulation.load_excel_workbook()
        sheet = workbook.get_sheet_by_name('words')
        rows = sheet.rows
        new_row_value = sum(1 for _ in rows) + 1
        rows = sheet.rows
        word_dict = {}
        for row in rows:
            word_dict[row[0].value] = row[1].value

        if word not in word_dict.keys():
            concat = "A" + str(new_row_value)
            sheet[concat] = word
            workbook.save(filename=os.getcwd() + "/" + cls.EXCEL_WORD_FILE)
            return True
            
        if word_dict[word] == None:
            return True

        return word_dict[word]

    """
    Create a csv file recording the contents of this simulation.
    """
    def send_data(self):
        output_dir = os.getcwd() + "/output/keywords/" + self.geoLocation
        Simulation.mkdir_p(output_dir)
        name = output_dir + "/" + datetime.datetime.now().strftime('%Y-%m-%d-%H:%M') + ".csv"
        with open(name, "wb") as csvfile:
            field_names = ["case", "cc", "query", "starting_date"]
            writer = csv.DictWriter(csvfile, fieldnames=field_names)
            writer.writeheader()
            for word in self.words:
                try:
                    word = u"{0}".format(word)
                    writer.writerow({"case": str(self.case_num), "query": word, "starting_date": self.startDate})
                except UnicodeEncodeError as e:
                    logging.error("Unicode Error: ")
                    logging.error(e.object[e.start:e.end])
                    continue
        return

    """
    Takes a GEOLOCATION as an input and returns the geoLocation one step above it. Since we are focusing on CA for
    our preliminary pass, we only have two levels of trickling. In the future, we will need to add more steps to this
    method.
    """
    @classmethod
    def trickle_up(cls, geoLocation):
        if geoLocation == "US-CA" or geoLocation == "US-OR":
            return "US"
        if geoLocation == "US":
            return None
        return "US-CA"

"""
Main method.
"""
def main(case_num, full_simulation, startDate="2010-01", endDate="2017-01"):
    ##Configure logging requirements
    logging.basicConfig(filename=Simulation.LOG_FILE,level=logging.INFO)
    total_words = []
    with open(Simulation.COUNTIES_FILE, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        number_of_counties_in_simulation = 0
        for row in reader:
            number_of_counties_in_simulation += 1
            code = row["geo_code"]
            description = row["location"]
            search_simulation_for_location = Simulation(case_num, code, full_simulation, startDate, endDate)
            search_simulation_for_location.generate_keywords()
            stringValue = "~/Desktop/" + str(code) + ".gv"
            search_simulation_for_location.graph.render(stringValue, view=True)
            total_words.extend(search_simulation_for_location.words)
            search_simulation_for_location.send_data()
    return total_words, number_of_counties_in_simulation


if __name__ == '__main__':
    assert len(sys.argv) == 5
    input_string = sys.argv
    case = int(input_string[1])
    starting_date = input_string[2]
    ending_date = input_string[3]
    full_simulation = input_string[4]
    try:
        words_and_number_of_counties = main(case, full_simulation, startDate=starting_date, endDate=ending_date)
        words = list(set(words_and_number_of_counties[0]))
        print words
        search.main(words, case)
        print words_and_number_of_counties[1]
        sys.exit(0)
    except ValueError as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print "*** print_tb:"
        traceback.print_tb(exc_traceback, limit=10, file=sys.stdout)
        print "*** print_exception:"
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=10, file=sys.stdout)
        sys.exit(1)



