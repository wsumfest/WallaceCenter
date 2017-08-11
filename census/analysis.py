import csv
import datetime
import demographics
import os
import json
from collections import OrderedDict

JSON_FILE = demographics.VARIABLE_FILE
COUNTIES_FILE = ""
CONFIDENCE_99 = float(2.576 / 1.645)
TOTAL_POPULATION = 0
TOTAL_POPULATION_ERROR = 0


def main(is_county_code, zip_codes=[], null_responses=[]):
    global COUNTIES_FILE
    COUNTIES_FILE = demographics.BASE + "/census/ca_counties.csv"
    if is_county_code == "0":
        base_path = demographics.BASE + "/census/simulations/counties"
        base_write = demographics.BASE + "/census/analysis/counties/" + datetime.datetime.now().strftime('%Y-%m-%d-%H:%M') + ".txt"
        with open(base_write, "w") as handle:
            os.chdir(base_path)
            subdirectories = os.popen("ls").read()
            subdirectories = format(subdirectories)
            for sub_dir in subdirectories:
                ch_dir = base_path + "/" + sub_dir
                os.chdir(ch_dir)
                last_simulation = max(os.listdir('.'), key = os.path.getctime)
                write_from_file(handle, last_simulation)
                handle.write("\n\n\n")
    else:
        base_path = demographics.BASE + "/census/simulations/zip_codes"
        base_write = demographics.BASE + "/census/analysis/zip_codes/" + datetime.datetime.now().strftime('%Y-%m-%d-%H:%M') + ".txt"
        with open(base_write, "w") as handle:
            write_null_responses(handle, null_responses)
            os.chdir(base_path)
            subdirectories = os.popen("ls").read()
            subdirectories = format(subdirectories)
            for sub_dir in subdirectories:
                ch_dir = base_path + "/" + sub_dir
                os.chdir(ch_dir)
                last_simulation = max(os.listdir('.'), key = os.path.getctime)
                write_from_file(handle, last_simulation, zip_codes=0)
                handle.write("\n\n\n")

"""
Writes the null responses from NULL_REPONSES into HANDLE.
"""
def write_null_responses(handle, null_responses):
    string = "Could not evaluate information for zip_codes: "
    for zip_code in null_responses:
        string += (zip_code + ", ")
    string = string[:-2]
    handle.write(string + ".\n\n\n")
    return



"""
Writes Appropriate Values into HANDLE.
"""
def write_from_file(handle, f, zip_codes=1):
    code = os.getcwd().split("/")[-1]
    with open(f, "r") as csvfile:
        with open(COUNTIES_FILE, "r") as county_file:
            reader = csv.DictReader(csvfile)
            vals = next(row for row in reader)
            if zip_codes == 1:
                write_county(handle, code, county_file)
            else:
                write_zip_code(handle, code)

            set_total_population(vals)
            write_total_population(handle)
            write_reproductive_males(handle, vals)
            write_reproductive_females(handle, vals)
            write_median_age(handle, vals)
            write_median_income(handle, vals)
            write_educational_attainment(handle, vals)
            write_foreign_born(handle, vals)
            write_races(handle, vals)
    return


"""
Writes the ZIP_CODE into HANDLE.
"""
def write_zip_code(handle, code):
    handle.write("Zip Code: " + code + ".\n")
    return

"""
Writes the appropriate description for CODE from COUNTY_FILE into HANDLE.
"""
def write_county(handle, code, county_file):
    reader = csv.DictReader(county_file)
    description = ""
    for row in reader:
        if row["county_code"] == code:
            description = row["county"]
        else:
            continue
    handle.write("County: " + description + ".\n")
    return

"""
Writes the foreign born population into HANDLES from VALUES.
"""
def write_foreign_born(handle, values):
    us_born_pop = float(values["B06009_001E"])
    us_born_error = float(values["B06009_001M"])
    us_born_upper_bound = us_born_pop + (CONFIDENCE_99 * us_born_error)
    us_born_lower_bound = us_born_pop - (CONFIDENCE_99 * us_born_error)
    foreign_born_pop = TOTAL_POPULATION - us_born_pop
    foreign_born_upper_bound = TOTAL_POPULATION - us_born_lower_bound
    foreign_born_lower_bound = TOTAL_POPULATION - us_born_upper_bound
    handle.write("Foreign Born Population Estimate: " + str(foreign_born_pop) + ".\n")
    handle.write("Foreign Born Population Range: " + str(foreign_born_lower_bound) + "," + str(foreign_born_upper_bound) + ".\n")
    return

"""
Writes the median Age for a county into a HANDLE.
"""
def write_median_age(handle, values):
    median_age = values["B01002_001E"]
    median_age_error = values["B01002_001M"]
    MOE_99 = (CONFIDENCE_99 * float(median_age_error))
    median_age_upper_bound = float(median_age) + MOE_99
    median_age_lower_bound = float(median_age) - MOE_99
    handle.write("Median Age Estimate: " + median_age + ".\n")
    handle.write("Median Age Range: " + str(median_age_lower_bound) + "," + str(median_age_upper_bound) + ".\n")
    return


"""
Writes the number of reproductive males from VALUES into HANDLE.
"""
def write_reproductive_males(handle, values):
    total_reproductive_population = 0.0
    total_reproductive_upper_bound = 0.0
    total_reproductive_lower_bound = 0.0
    prefix = "B01001"
    for key in values.keys():
        try:
            if key[-1] != "E":
                continue
            if key[0:6] == prefix:
                suffix = key[7:10]
                kicker = int(suffix)
                if kicker >= 6 and kicker <= 14:
                    total_var = prefix + "_" + suffix + "E"
                    error_var = prefix + "_" + suffix + "M"
                    total_for_range = float(values[total_var])
                    error_for_range = float(values[error_var])
                    upper_for_range = total_for_range + (CONFIDENCE_99 * error_for_range)
                    lower_for_range = total_for_range - (CONFIDENCE_99 * error_for_range)
                    total_reproductive_population += total_for_range
                    total_reproductive_lower_bound += lower_for_range
                    total_reproductive_upper_bound += upper_for_range
        except ValueError:
            continue
    handle.write("Total Population for Reproductive Males Estimate: " + str(total_reproductive_population) + ".\n")
    handle.write("Total Population of Reproductive Males Range: " + str(total_reproductive_lower_bound) + "," + str(total_reproductive_upper_bound) + ".\n")
    return

"""
Writes the number of reproductive females from VALUES into HANDLE.
"""
def write_reproductive_females(handle, values):
    total_reproductive_population = 0.0
    total_reproductive_upper_bound = 0.0
    total_reproductive_lower_bound = 0.0
    prefix = "B01001"
    for key in values.keys():
        try:
            if key[-1] != "E":
                continue
            if key[0:6] == prefix:
                suffix = key[7:10]
                kicker = int(suffix)
                if kicker >= 30 and kicker <= 38:
                    total_var = prefix + "_" + suffix + "E"
                    error_var = prefix + "_" + suffix + "M"
                    total_for_range = float(values[total_var])
                    error_for_range = float(values[error_var])
                    upper_for_range = total_for_range + (CONFIDENCE_99 * error_for_range)
                    lower_for_range = total_for_range - (CONFIDENCE_99 * error_for_range)
                    total_reproductive_population += total_for_range
                    total_reproductive_lower_bound += lower_for_range
                    total_reproductive_upper_bound += upper_for_range
        except ValueError:
            continue
    handle.write("Total Population for Reproductive Females Estimate: " + str(total_reproductive_population) + ".\n")
    handle.write("Total Population for Reproductive Females Range: " + str(total_reproductive_lower_bound) + "," + str(total_reproductive_upper_bound) + ".\n")
    return


"""
Writes the median household income from VALUES into HANDLE.
"""
def write_median_income(handle, values):
    median_income = float(values["B19013_001E"])
    median_income_error = float(values["B19013_001M"])
    median_income_lower_bound = median_income - (CONFIDENCE_99 * median_income_error)
    median_income_upper_bound = median_income + (CONFIDENCE_99 * median_income_error)
    handle.write("Median Hosuehold Income Estimate: " + str(median_income) + ".\n")
    handle.write("Median Household Income Range: " + str(median_income_lower_bound) + "," + str(median_income_upper_bound) + ".\n")
    return

"""
Sets global variable to total population in VALUES.
"""
def set_total_population(values):
    global TOTAL_POPULATION
    global TOTAL_POPULATION_ERROR
    TOTAL_POPULATION = float(values["B01001_001E"])
    TOTAL_POPULATION_ERROR = float(values["B01001_001M"])
    return

"""
Writes the total population to HANDLE.
"""
def write_total_population(handle):
    total_pop_upper_bound = TOTAL_POPULATION + (CONFIDENCE_99 * TOTAL_POPULATION_ERROR)
    total_pop_lower_bound = TOTAL_POPULATION - (CONFIDENCE_99 * TOTAL_POPULATION_ERROR)
    handle.write("Total Population Estimate: " + str(TOTAL_POPULATION) + ".\n")
    handle.write("Total Population Range: " + str(total_pop_lower_bound) + "," + str(total_pop_upper_bound) + ".\n")
    return

"""
Write the educational attainments of a population into HANDLE.
"""
def write_educational_attainment(handle, values):
    high_school_or_lower_pop = float(values["B06009_002E"])
    high_school_or_lower_pop_error = float(values["B06009_002M"])
    high_school_or_lower_pop_upper_bound = high_school_or_lower_pop + (CONFIDENCE_99 * high_school_or_lower_pop_error)
    high_school_or_lower_pop_lower_bound = high_school_or_lower_pop - (CONFIDENCE_99 * high_school_or_lower_pop_error)
    estimate_for_high_school_or_higher = TOTAL_POPULATION - high_school_or_lower_pop
    estimate_for_high_school_or_higher_upper_bound = TOTAL_POPULATION - high_school_or_lower_pop_lower_bound
    estimate_for_high_school_or_higher_lower_bound = TOTAL_POPULATION - high_school_or_lower_pop_upper_bound
    handle.write("High School Education or Higher Estimate: " + str(estimate_for_high_school_or_higher) + ".\n")
    handle.write("High School Education or Higher Range: " + str(estimate_for_high_school_or_higher_lower_bound) + "," + str(estimate_for_high_school_or_higher_upper_bound) + ".\n")
    return

"""
Writes race and origins into HANDLE.
"""
def write_races(handle, values):
    white_population_total = float(values["B01001A_001E"])
    white_population_error = float(values["B01001A_001M"])
    white_population_total_upper_bound = white_population_total + (CONFIDENCE_99 * white_population_error)
    white_population_total_lower_bound = white_population_total - (CONFIDENCE_99 * white_population_error)
    handle.write("White Population Estimate: " + str(white_population_total) + ".\n")
    handle.write("White Population Range: " + str(white_population_total_lower_bound) + "," + str(white_population_total_upper_bound) + ".\n")
    hispanic_population_total = float(values["B01001I_001E"])
    hispanic_population_error = float(values["B01001I_001M"])
    hispanic_population_total_upper_bound = hispanic_population_total + (CONFIDENCE_99 * hispanic_population_error)
    hispanic_population_total_lower_bound = hispanic_population_total - (CONFIDENCE_99 * hispanic_population_error)
    handle.write("Hispanic Population Estimate: " + str(hispanic_population_total) + ".\n")
    handle.write("Hispanic Population Range: " + str(hispanic_population_total_lower_bound) + "," + str(hispanic_population_total_upper_bound) + ".\n")
    black_population_total = float(values["B01001B_001E"])
    black_population_error = float(values["B01001B_001M"])
    black_population_total_upper_bound = black_population_total + (CONFIDENCE_99 * black_population_error)
    black_population_total_lower_bound = black_population_total - (CONFIDENCE_99 * black_population_error)
    handle.write("African American Population Estimate: " + str(black_population_total) + ".\n")
    handle.write("African American Population Range: " + str(black_population_total_lower_bound) + "," + str(black_population_total_upper_bound) + ".\n")
    native_american_population_total = float(values["B01001C_001E"])
    native_american_population_error = float(values["B01001C_001M"])
    native_american_population_total_upper_bound = native_american_population_total + (CONFIDENCE_99 * native_american_population_error)
    native_american_population_total_lower_bound = native_american_population_total - (CONFIDENCE_99 * native_american_population_error)
    handle.write("Native American Population Estimate: " + str(native_american_population_total) + ".\n")
    handle.write("Native American Population Range: " + str(native_american_population_total_lower_bound) + "," + str(native_american_population_total_upper_bound) + ".\n")
    asian_population_total = float(values["B01001D_001E"])
    asian_population_error = float(values["B01001D_001M"])
    asian_population_total_upper_bound = asian_population_total + (CONFIDENCE_99 * asian_population_error)
    asian_population_total_lower_bound = asian_population_total - (CONFIDENCE_99 * asian_population_error)
    handle.write("Asian American Population Estimate: " + str(asian_population_total) + ".\n")
    handle.write("Asian American Population Range: " + str(asian_population_total_lower_bound) + "," + str(asian_population_total_upper_bound) + ".\n")
    pacific_islander_total = float(values["B01001E_001E"])
    pacific_islander_error = float(values["B01001E_001M"])
    pacific_islander_total_upper_bound = pacific_islander_total + (CONFIDENCE_99 * pacific_islander_error)
    pacific_islander_total_lower_bound = pacific_islander_total - (CONFIDENCE_99 * pacific_islander_error)
    handle.write("Pacific Islander Population Estimate: " + str(pacific_islander_total) + ".\n")
    handle.write("Pacific Islander Population Range: " + str(pacific_islander_total_lower_bound) + "," + str(pacific_islander_total_upper_bound) + ".\n")
    other_total = float(values["B01001F_001E"])
    other_error = float(values["B01001F_001M"])
    other_total_upper_bound = other_total + (CONFIDENCE_99 * other_error)
    other_total_lower_bound = other_total - (CONFIDENCE_99 * other_error)
    handle.write("Other Race Population Estimate: " + str(other_total) + ".\n")
    handle.write("Other Race Population Range: " + str(other_total_lower_bound) + "," + str(other_total_upper_bound) + ".\n")
    two_or_more_races_total = float(values["B01001G_001E"])
    two_or_more_races_error = float(values["B01001G_001M"])
    two_or_more_races_total_upper_bound = two_or_more_races_total + (CONFIDENCE_99 * two_or_more_races_error)
    two_or_more_races_total_lower_bound = two_or_more_races_total - (CONFIDENCE_99 * two_or_more_races_error)
    handle.write("Two or More Races Population Estimate: " + str(two_or_more_races_total) + ".\n")
    handle.write("Two or More Races Population Range: " + str(two_or_more_races_total_lower_bound) + "," + str(two_or_more_races_total_upper_bound) + ".\n")
    return

"""
Loads the Descriptor for a VARIABLE from our JSON_FILE.
"""
def load_descriptor(variable):
    with open(JSON_FILE, "r") as json_file:
        data = json.load(json_file)
    if variable != 'county' and variable != 'state':
        value = data[variable]
    else:
        value = variable
    return value


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