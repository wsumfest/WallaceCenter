import numpy 
import scipy
import os
from apiclient.discovery import build
from apiclient.errors import HttpError
from os.path import join, dirname
from dotenv import load_dotenv
import json
import matplotlib.pyplot as plt
import logging
import time
import csv
import sys
import copy
import subprocess
import datetime
import errno

LOG_FILE = "log/keyword_simulations.log"
GRAPHING_LOG_FILE = "graphing_values.log"
TRENDS_SERVER = "https://www.googleapis.com"
TRENDS_VERSION = "v1beta"
START_DATE = "2016-01-01"

def main():
	os.chdir(BASE + "/analysis/logs")
	last_sim = max(os.listdir('.'), key = os.path.getctime)
	words = collect_words(last_sim)
	os.chdir(BASE)
	plot_all_counties(words, 1)
	health_values = get_health_values(words, 1)
	plot_health_values(health_values, 1)
	return words

"""
Sets the dates based on the first point in DATA.
"""
def set_x_values(data):
	first_point = data[0]
	points = first_point[1]
	dates = [point["date"] for point in points]
	return dates


"""
Plots health trends values. The dates are all the same for each word, so we look at the first datapoint and plot the values.
Returns the coeffecients for the linear best fit polynomial for future analysis.
"""
def plot_health_values(data, case):
	numlines = len(data)
	x_values = set_x_values(data)
	top_value = len(x_values)
	x = numpy.arange(top_value)
	dataset = [[] for item in x]
	average_values = [0 for item in range(top_value)]
	for word in data:
		data_points = [point["value"] for point in word[1]]
		values = data_points
		index = 0
		while index < top_value:
			dataset[index].append(values[index])
			index +=1

		plt.plot(x, values, linewidth=0.3)

	#High degree best fit polynomial
	coefficients = ave_coeff(numpy.polyfit(x, dataset, 20))
	polynomial = numpy.poly1d(coefficients)
	best_fit = polynomial(x)
	#Linear best fit polynomial
	coefficients = ave_coeff(numpy.polyfit(x, dataset, 1))
	polynomial = numpy.poly1d(coefficients)
	linear_best_fit = polynomial(x)

	plt.plot(x, best_fit, linewidth=4)
	plt.plot(x, linear_best_fit, linewidth=4)
	plt.show()
	return coefficients


"""
Returns the average of coeffecients for best fit line. 
"""
def ave_coeff(coeff):
	ret = []
	for item in coeff:
		ret.append(sum(item)/float(len(item)))
	return ret

"""
Rotates dataset for analysis of counties.
"""
def make_dataset(data):
	top_value = len(data[0])
	dataset = [[] for item in range(top_value)]
	for item in data:
		index = 0
		while index < top_value:
			dataset[index].append(item[index])
			index += 1 
	return dataset

"""

DEPRECIATED

Plots the regression for all counties given data from words.
"""
def plot_all_counties(words, case):
	dataset = []
	for county in COUNTIES:
		code = strip_code(county)
		health_values = get_health_values(words, case, geoLocation=code)
		numlines = len(health_values)
		x_values = set_x_values(health_values)
		top_value = len(x_values)
		x_values = numpy.arange(top_value)
		average_values = [0 for item in range(top_value)]
		for word in health_values:
			data_points = [point["value"] for point in word[1]]
			print data_points
			index = 0
			while index < top_value:
				if data_points[index] != u'NaN':
					average_values[index] += data_points[index]
				index += 1
		average = [average_value / numlines for average_value in average_values]
		dataset.append(average)
		plt.plot(x_values, average)

	dataset = make_dataset(dataset)
	coefficients = ave_coeff(numpy.polyfit(x_values, dataset, 1))
	polynomial = numpy.poly1d(coefficients)
	linear_best_fit = polynomial(x_values)

	coefficients = ave_coeff(numpy.polyfit(x_values, dataset, 20))
	polynomial = numpy.poly1d(coefficients)
	best_fit = polynomial(x_values)

	plt.plot(x_values, best_fit, linewidth=4)
	plt.plot(x_values, linear_best_fit, linewidth=4)
	plt.show()
	return

	
"""
Formats code to dma standard from csvfile.
"""
def strip_code(code):
	if code == "US-CA" or code == "US-MS" or code == "US-LA" or code == "US":
		return code
	code = code[6:]
	return int(code)


"""
Collects all the unique queries from an analysis log.
"""
def collect_words(filename):
	collection, base_set = list(), set()
	with open(filename, "r") as f:
		lines = f.readlines()
		for line in lines:
			if line[0:8] == "Queries:":
				words = line[8:]
				content = [word.strip() for word in words.split(",")]
				for word in content:
					if word[-1] == ".":
						word = word[:-1]
					if word not in base_set:
						collection.append(word)
						base_set.add(word)
	return collection

"""
Gets the health trends value for all words in a simulation.
"""
def get_health_values(words, case, geoLocation="US-CA"):
	service = build_service()
	values = []
	for word in words:
		health_value = make_request(service, word, geoLocation, case)
		if health_value != None:
			if health_value != u'NaN':
				values.append(health_value)

	return values

"""
Makes the request to the health trends api. We use start date from START DATE.
"""
def make_request(service, word, geoLocation, case):
	cases = {0: service.getTimelinesForHealth, 1: service.getGraph}
	func = cases[case]
	if case == 1:
		health_value = func(terms=word, restrictions_geo=geoLocation, restrictions_startDate=START_DATE)
	else:
		if type(geoLocation) == str:
			if geoLocation == "US":
				health_value = func(terms=word, geoRestriction_country=geoLocation)
			else:
				health_value = func(terms=word, geoRestriction_region=geoLocation)
		else:
			health_value = func(terms=word, geoRestriction_dma=geoLocation)
	try:
		response = health_value.execute()
		points = response["lines"][0]["points"]
		value = (word, points)
	except HttpError as e:
		error_content = json.loads(e.content)
		code = error_content["error"]["code"]
		if code == 404:
		    logging.info("Not enough info for this word, continue")
		    return None
		elif code == 429:
			logging.info("Our rate has been exceeded, wait and continue")
			time.sleep(4)
			return make_request(service, word, geoLocation, case)
		elif (code // 100) == 5:
			logging.error("Our google service has an internal server error, process and try again")
			time.sleep(4)
			return make_request(service, word, geoLocation, case)
		else:
			logging.error("an unknown error appeared")
			logging.error(e)
			raise e
	return value


"""
Builds service to our trends api.
"""
def build_service():
    head, tail = os.path.split(dirname(__file__))
    dotenv_path = join("/Users/willsumfest/preto3", '.env')
    load_dotenv(dotenv_path)
    discovery_url = TRENDS_SERVER + '/discovery/v1/apis/trends/' + TRENDS_VERSION + '/rest'
    trends_developer_key = os.environ.get('TRENDS_DEVELOPER_KEY')
    service = build('trends', TRENDS_VERSION, developerKey=trends_developer_key, discoveryServiceUrl=discovery_url)
    return service


"""
Returns search terms for a REGION based on the last simulation.
"""
def get_terms(region):
	os.chdir(BASE + "/analysis/logs")
	last_sim = max(os.listdir('.'), key = os.path.getctime)
	content = []
	with open(last_sim, "r") as filename:
		lines = filename.readlines()
		index = 0
		returned_words = []
		while index < len(lines):
			line = lines[index]
			if line[:8] == "Region: ":
				print line[8:-2], region
				if line[8:-2] == region:
					print "should be good"
					query_lines = lines[index + 4]
					words = query_lines[8:]
					content = [word.strip() for word in words.split(",")]
					for word in content:
						if word[-1] == ".":
							word = word[:-1]
							returned_words.append(word)
						else:
							returned_words.append(word)
			index += 1
	return returned_words



"""
We want to illustrate the differences between two regions in the search queries and sites that users might end up on.
We call a function to illustrate the queries and a function to illustrate the sites.
"""
def write_term_results(region1, region2, region3, region4="United States"):
	terms_for_region_1 = get_terms(region1)
	terms_for_region_2 = get_terms(region2)
	terms_for_region_3 = get_terms(region3)
	terms_for_region_4 = get_terms(region4)
	print len(terms_for_region_1)
	print len(terms_for_region_2)
	print len(terms_for_region_3)
	print len(terms_for_region_4)

	first_set = set(terms_for_region_1 + terms_for_region_2 + terms_for_region_3)
	result_list = list(first_set) + [x for x in terms_for_region_4 if x not in first_set]

	values_for_region_1 = get_values_for_terms(region1, result_list)
	dict_for_region_1 = make_dict(values_for_region_1[1])
	values_for_region_2 = get_values_for_terms(region2, result_list)
	dict_for_region_2 = make_dict(values_for_region_2[1])
	values_for_region_3 = get_values_for_terms(region3, result_list)
	dict_for_region_3 = make_dict(values_for_region_3[1])
	values_for_region_4 = get_values_for_terms(region4, result_list)
	dict_for_region_4 = make_dict(values_for_region_4[1])

	values_for_region_1 = get_values(result_list, dict_for_region_1)
	values_for_region_2 = get_values(result_list, dict_for_region_2)
	values_for_region_3 = get_values(result_list, dict_for_region_3)
	values_for_region_4 = get_values(result_list, dict_for_region_4)

	width = 0.20
	fig, ax = plt.subplots()
	ind = numpy.arange(len(result_list))
	rects1 = ax.bar(ind, values_for_region_1, width, color='r')
	rects2 = ax.bar(ind + width, values_for_region_2, width, color='b')
	rects3 = ax.bar(ind + width*2, values_for_region_3, width, color='g')
	rects4 = ax.bar(ind + width*3, values_for_region_4, width, color='m')

	ax.set_ylabel('Proportion of Searches')
	ax.set_title('Most Common Searched Queries Related to Birth Control in 01/01/16')
	ax.set_xticks(ind + width)
	ax.set_xticklabels(result_list, rotation='vertical')
	ax.legend((rects1[0], rects2[0], rects3[0], rects4[0]), (region1, region2, region3, region4))
	fig.tight_layout()
	plt.show()

	return_value_list_region_1 = set_return_value_list(result_list, values_for_region_1)
	return_value_list_region_2 = set_return_value_list(result_list, values_for_region_2)
	return_value_list_region_3 = set_return_value_list(result_list, values_for_region_3)
	return_value_list_region_4 = set_return_value_list(result_list, values_for_region_4)

	return ((region1, return_value_list_region_1) , (region2, return_value_list_region_2), (region3, return_value_list_region_3), (region4, return_value_list_region_4))


"""
Graphs the frequencies of site visits by county using the search frequencies in tup_of_values.
"""
def write_site_results(tup_of_values):
	values_for_region_1 = tup_of_values[0][1]
	values_for_region_2 = tup_of_values[1][1]
	values_for_region_3 = tup_of_values[2][1]
	values_for_region_4 = tup_of_values[3][1]
	probability_site_list_region1 = return_site_list(values_for_region_1)
	probability_site_list_region2 = return_site_list(values_for_region_2)
	probability_site_list_region3 = return_site_list(values_for_region_3)

	top_20_sites_region1 = sorted(probability_site_list_region1, key=lambda k: probability_site_list_region1[k], reverse=True)[:19]
	top_20_sites_region2 = sorted(probability_site_list_region2, key=lambda k: probability_site_list_region2[k], reverse=True)[:19]
	top_20_sites_region3 = sorted(probability_site_list_region3, key=lambda k: probability_site_list_region3[k], reverse=True)[:19]

	first_set = set(top_20_sites_region1 + top_20_sites_region2)
	result_list = list(first_set) + [x for x in top_20_sites_region3 if x not in first_set]
	result_list = sorted(result_list, key=lambda k: probability_site_list_region3[k], reverse=True)

	values_for_region_1 = get_values(result_list, probability_site_list_region1)
	values_for_region_2 = get_values(result_list, probability_site_list_region2)
	values_for_region_3 = get_values(result_list, probability_site_list_region3)

	width = 0.25
	fig, ax = plt.subplots()
	ind = numpy.arange(len(result_list))
	rects1 = ax.bar(ind, values_for_region_1, width, color='r')
	rects2 = ax.bar(ind + width, values_for_region_2, width, color='b')
	rects3 = ax.bar(ind + width*2, values_for_region_3, width, color='g')
	ax.set_ylabel('Estimated Proportion of Visits')
	ax.set_title('Most Visited Sites for Birth Control Between Jan 01, 2016-Jan 12, 2017')
	ax.set_xticks(ind + width)
	ax.set_xticklabels(result_list, rotation='vertical')
	ax.legend((rects1[0], rects2[0], rects3[0]), (region1, region2, region3,))
	fig.tight_layout()
	plt.show()


	return


"""
Reads the most recent search term simulation file, then returns the normalized site probabilities for a region.
"""
def return_site_list(dict_of_region):
	file_name = return_file_name_for_last_search_simulation()
	return_value = {}
	for key in dict_of_region.keys():
		normalized_probability = dict_of_region[key]
		with open(file_name, "r") as csvfile:
			reader = csv.DictReader(csvfile)
			for row in reader:
				if row["word"] == key:
					if row["displayLink"] not in return_value:
						return_value[row["displayLink"]] = normalized_probability * get_probability(row["position"])
					else:
						return_value[row["displayLink"]] += normalized_probability * get_probability(row["position"])
	return return_value

"""
Returns the filename of the last search simulation.
"""
def return_file_name_for_last_search_simulation():
	root = "/Users/willsumfest/preto3/output/search/US-CA"
	os.chdir(root)
	last_search_file = max(os.listdir('.'), key = os.path.getctime)
	file_name = root + "/" + last_search_file
	return file_name


"""
Returns search frequencies normalized to word for a given region.
"""
def set_return_value_list(term_list, values_for_region):
	return_dict = dict()
	index, top = 0, len(term_list)
	while index < top:
		term = term_list[index]
		value = values_for_region[index]
		return_dict[term] = value
		index += 1

	return return_dict

"""
Returns a list normalized with values from dictionary.
"""
def get_values(total_list, dictionary):
	values = []
	for term in total_list:
		if term in dictionary.keys():
			values.append(dictionary[term])
		else:
			values.append(0.0)
	return values

"""
Creates a dictionary from a list of smaller dictionary.
"""
def make_dict(dict_list):
	dictionary = dict()
	for term_pair in dict_list:
		key = term_pair.keys()[0]
		val = term_pair.values()[0]
		dictionary[key] = val
	return dictionary

"""
Gets the values for search terms for a given region.
"""
def get_values_for_terms(region, terms):
	service = build_service()
	geoLocation = get_code_from_county(region) 
	if type(geoLocation) == str:
		if len(terms) <= 5:
			graph = service.getTimelinesForHealth(terms=terms, geoRestriction_region=geoLocation, time_startDate=START_DATE)
			ret_points = graph.execute()
			print ret_points
		else:
			bottom, top, block = 0, 1, 5
			bottom_index = bottom * block
			top_index = top * block
			ret_points = dict()
			ret_points['lines'] = []
			while top_index < len(terms):
				request_terms = terms[bottom_index:top_index]
				if geoLocation == "US":
					graph = service.getTimelinesForHealth(terms=request_terms, geoRestriction_country=geoLocation, time_startDate=START_DATE)
				else:
					graph = service.getTimelinesForHealth(terms=request_terms, geoRestriction_region=geoLocation, time_startDate=START_DATE)
				ret_points['lines'].extend(graph.execute()['lines'])

				bottom_index += block
				top_index += block
			top_index = len(terms)
			request_terms = terms[bottom_index:top_index]
			if geoLocation == "US":
				graph = service.getTimelinesForHealth(terms=request_terms, geoRestriction_country=geoLocation, time_startDate=START_DATE)
			else:
				graph = service.getTimelinesForHealth(terms=request_terms, geoRestriction_region=geoLocation, time_startDate=START_DATE)
			ret_points['lines'].extend(graph.execute()['lines'])
			with open("/".join([os.getcwd(), GRAPHING_LOG_FILE]), "w") as graph_log:
				graph_log.write(json.dumps(ret_points))

		ave_points = average(ret_points)
		return ave_points

	else:
		if len(terms) == 0:
			return
		elif len(terms) <= 5:
			print terms
			graph = service.getTimelinesForHealth(geoRestriction_dma=geoLocation, terms=terms, time_startDate=START_DATE)
			ret_points = graph.execute()
		else:
			bottom, top, block = 0, 1, 5
			bottom_index = bottom * block
			top_index = top * block
			ret_points = dict()
			ret_points['lines'] = []
			while top_index < len(terms):
				request_terms = terms[bottom_index:top_index]
				print len(request_terms)
				graph = service.getTimelinesForHealth(geoRestriction_dma=geoLocation, terms=request_terms, time_startDate=START_DATE)
				try:
					ret_points['lines'].extend(graph.execute()['lines'])
					print ret_points
				except HttpError as e:
					print e
					continue

				bottom_index += block
				top_index += block
			top_index = len(terms)
			request_terms = terms[bottom_index:top_index]
			graph = service.getTimelinesForHealth(terms=request_terms, geoRestriction_dma=geoLocation, time_startDate=START_DATE)
			ret_points['lines'].extend(graph.execute()['lines'])
			with open("/".join([os.getcwd(), GRAPHING_LOG_FILE]), "w") as graph_log:
				graph_log.write(json.dumps(ret_points))

		ave_points = average(ret_points)
		return ave_points



"""
Gets the county code from a region description.
"""
def get_code_from_county(region):
	filename = BASE + "/search/ca_subcategories.csv"
	with open(filename, "r") as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			if row["location"] == region:
				return strip_code(row["geo_code"])
	return None

"""
Average points for each term in terms
"""
def average(values):
	terms = values["lines"]
	term_aggregate = [[],[]]
	total_agg = 0
	for term in terms:
		new_dict = dict()
		points = term["points"]
		index = 1
		agg = 0
		for point in points:
			agg += point['value']
			index += 1
		average_points = float(agg)
		total_agg += average_points
		new_dict[term["term"]] = average_points
		term_aggregate[0].append(term["term"])
		term_aggregate[1].append(copy.deepcopy(new_dict))
	ret_values = []
	for dic in term_aggregate[1]:
		new_dict = {}
		key = dic.keys()[0]
		value = dic.values()[0]
		average_value = value / float(total_agg)
		new_dict[key] = average_value
		ret_values.append(copy.deepcopy(new_dict))
	term_aggregate[1] = ret_values
	return term_aggregate




"""
Returns the probaility of a user visiting a site at a given POSITION. Based off of research done by other entities.
"""
def get_probability(position):
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


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
    return




if __name__ == '__main__':
	region1 = "San Francisco-Oakland-San Jose CA"
	region2 = "Fresno-Visalia CA"
	region3 = "California"
	logging.basicConfig(filename=LOG_FILE,level=logging.INFO)
	BASE = os.getcwd()
	# main() ##This was for all counties over time, now we're going to focus on two counties 
	search_frequencies = write_term_results(region1, region2, region3)
	print search_frequencies
	output_dir = BASE + "/output/final/" + datetime.datetime.now().strftime('%Y-%m-%d-%H:%M')
	mkdir_p(output_dir)
	output_file = output_dir + "/words.txt"
	with open(output_file, "w") as output_file:
		output_file.write(json.dumps(search_frequencies))

	write_site_results(search_frequencies)


