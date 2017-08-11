import sys
import os
from os.path import join, dirname
from dotenv import load_dotenv
from apiclient.discovery import build
from apiclient.errors import HttpError
import simulate_keywords
import json
import logging
import time

class GoogleClient(object):

    def __init__(self, trends_server, trends_version):
        logging.basicConfig(filename=simulate_keywords.Simulation.LOG_FILE,level=logging.INFO)
        self.trends_version = trends_version
        self.trends_server = trends_server
        self.service = self.build_service()

    """
    Builds service to our trends api.
    """
    def build_service(self):
        head, tail = os.path.split(dirname(__file__))
        dotenv_path = join(head, '.env')
        load_dotenv(dotenv_path)
        discovery_url = self.trends_server + '/discovery/v1/apis/trends/' + self.trends_version + '/rest'
        trends_developer_key = os.environ.get('TRENDS_DEVELOPER_KEY')
        service = build('trends', self.trends_version, developerKey=trends_developer_key, discoveryServiceUrl=discovery_url)
        return service


    """
    Makes a request to SERVICE for keyword WORD base on geoLocation GEOLOCATION. We use trickle logic to handle requests
    that do not have enough data at the county and state level. 
    """
    def make_request(self, word, geoLocation, startDate, endDate):
        top_queries = self.service.getTopQueries(term=word, restrictions_geo=geoLocation, restrictions_startDate=startDate, restrictions_endDate=endDate)
        returned_words = []
        K = simulate_keywords.Simulation.K
        try:
            response = top_queries.execute()
            if response == {}: #they began to return these. Basically just trickle up now
                if geoLocation == "US":
                    return []
                else:
                    location = simulate_keywords.Simulation.trickle_up(geoLocation)
                    return self.make_request(word, location, startDate, endDate)
            related_terms = response["item"]
            print related_terms
            cuttoff = min(K, len(related_terms))
            logging.info(related_terms)
            for term in related_terms[:cuttoff]:
                returned_words.append(term["title"])
            if cuttoff < len(related_terms):
                for term in related_terms[cuttoff:]:
                    if term["value"] >= 70:
                        returned_words.append(term["title"])

        except HttpError as e:
            print e
            error_content = json.loads(e.content)
            code = error_content["error"]["code"]
            if code == 400: #Not enough data to give us an accurate reading
                if geoLocation == "US":
                    return []
                else:
                    location = simulate_keywords.Simulation.trickle_up(geoLocation)
                    return self.make_request(word, location, startDate, endDate)
            elif code == 429: #Our trends rate has been exceeded, wait for two seconds and continue.
                logging.info("Our rate has been exceeded, we will wait for two seconds and continue.")
                time.sleep(2)
                return self.make_request(word, geoLocation, startDate, endDate)
            elif (code // 100) == 5:
                logging.error("An internal server error occured at the Google service, process and continue.")
                logging.error(e.content)
                time.sleep(3)
                print "error"
                return self.make_request(word, geoLocation, startDate, endDate)
            else:
                pass
        return returned_words

    """
    Returns all values in top queries for the topics in TOPICS for GEOLCATION.
    """
    def full_request(self, topics, geoLocation):
        soFAR = set()
        terms = []
        curr, top = 0, len(topics)
        K = 3
        while curr < top:
            topic = topics[curr]
            try:
                response = self.service.getTopQueries(term=topic, restrictions_geo=geoLocation).execute()
                print response
                related_terms = response["item"]
                cuttoff = min(K, len(related_terms))
                for item in related_terms:
                    if item["title"] not in soFAR:
                        terms.append(item["title"])
                        soFAR.add(item["title"])
                curr += 1
            except HttpError as e:
                error_content = json.loads(e.content)
                code = error_content["error"]["code"]
                if code == 404:
                    curr += 1
                elif code == 429:
                    time.sleep(2)
                    pass
                elif (code // 100) == 5:
                    time.sleep(1)
                    pass
                else:
                    logging.error(e)
                    curr +=1 

        print terms
        return terms


    """
    Takes a list of TERMS and a GEOLOCATION and determines the top topics that apply
    to the items in TERMS. 
    """
    def find_topics(self, terms, geoLocation):
        if geoLocation == None:
            return terms
        soFAR = set()
        topics = []
        curr, top = 0, len(terms)
        while curr < top:
            term = terms[curr]
            try:
                response = self.service.getTopTopics(term=term, restrictions_geo=geoLocation).execute()
                items = response["item"]
                top_topic_dict = items[0]
                top_topic = top_topic_dict["mid"]
                if top_topic not in soFAR:
                    topics.append(top_topic)
                    soFAR.add(top_topic)
                curr += 1
            except HttpError as e:
                error_content = json.loads(e.content)
                code = error_content["error"]["code"]
                if code == 404:
                    logging.info("Not enough info for this word, continue")
                    location = simulate_keywords.Simulation.trickle_up(geoLocation)
                    return self.find_topics(terms, location)
                elif code == 429:
                    logging.info("Our rate has been exceeded, wait and continue")
                    time.sleep(2)
                    pass
                elif (code // 100) == 5:
                    logging.error("Our google service has an internal server error, process and try again")
                    time.sleep(1)
                    pass
                else:
                    logging.error("an unknown error appeared")
                    logging.error(e)
                    curr += 1
        return topics