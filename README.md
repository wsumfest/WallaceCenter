PreTo3
======
This Repository contians the code for the Wallace Center PreTo3 simulation. We are working under limited access for our proof of concept trial. So please be concious of the daily quatos for the Trends API.

Credentials
-----------
Get the developer keys for the Google API's from a team member and place them in a .env file.

Configurations
--------------
We are using a variety of python packages and dependencies for development. If you add any dependencies, update the `configure.sh` file with steps to install them. Before running an expirement, you will need to set your bash environment. Run `./configure.sh` in your terminal and then `source ~/.bash_profile`.

Determing Search Patterns
-------------------------
To run a simulation on a seed set, change the **BC** and **Case** variables in our `keywords_simulations.sh` file. Also, add your case to the `get_case_words` function in `search/simulate_keywords.py`. The **BC** variable determines the correlation on which a term is added to our list. If the variable is too tight, and our list will remain small. If it is too loose, our program is likely to return searches that are irrelevant to our investigation. So far, a value of 70.0 has given resonable results for our simulations. 

##### Understanding Simulation Parameters
- **Case**: This parameter determines the topic we are evaluating in a given simulation. Consult the `get_case_words` function in `search/simulate_keywords.py` for more detail.
- **CC**: The highest correlation value necessary for a query to be added to our list of keywords. Note this attribute has been depreciated and should not be set lower than 100.
- **BC**: The value in which we add a word into our list of keywords. 
- **Full Simulation**: This value is given a 1 if, at the beginning of the simulation, we search for the top topics related to our case. Otherwise, we give this value a 0.
- **Start Date**: This variable determines the beginning of our timeframe in which we request data from the Google Trends API.

##### Excel Sheets
This project has two excel sheets located in the directory `excel_sheets` the `words.xlsx` file contains information about each keyword and its relevancy to public health. This excel sheet is necessary to filter irrelvant queries, such as pop-culture references, from our simulation. The `sites.xlsx` excel sheet will be used to classify websites in the future.

##### Intermediate Outputs
In the spirit of full transparency, we have several intermediate outputs. All transactions with third party API's such as Google Trends and Google Search are logged in `log/keyword_simulations.log`. Moreover, all relevant processing in the determination of the keyword set is logged in `log/keyword_simulations.log`. After we have determined the keywords for each region in a simulation, we log the relevant information in `analysis/logs`, here you will find all of the keywords for each region in a simulation, as well as the general info about the simulation. Since there is no regional difference from the search API, all of the keywords are searched and the reponses are logged in `output/search/US-CA`, here you will find all of the relevant information necessary to determine the sites that are most likely to be visited from a simulation. Once we have graphed the intermediate graph for keywords in a simulation, all relevant information is logged in `output/final`. This allows us to load the data into an ipython notebook and manually consolidate keywords and frequencies to clean up our presentation. 

#####Final Presentation
In `data_cleanup.ipynb` you will notice that it is necessary to manually consolidate the frequencies of the keywords we would like to group together. Although tedious, this is a necessary component of our simulation as it allows our graphs to be cleaner and removes clutter from the presentation.

#####Saving Graphs
Save your graphs in the format **search-word**\_**initial**\_**date** for the intermediate graph of the keyword search frequencies. Save your graphs for the sites in the format **search-word**\_**sites**\_**date**. Save your final presentation for the simulation in the format **search-word**\_**final**\_**date**.


##Debugging 
It is important to be able to understand how to navigate the system in case of failures or bugs. If you are running a simulation and the system quits abruptly, there are several steps you can take in order to reconcile the problem. First, look at the traceback and determine where the error occured. If it involves a call to Google's API, look at the logs to determine the returned value of the API. If it appears that the returned data has changed from an API call (this happens every once and awhile), then make changes to the function as necessary. If you observe a high number of errors (400 or 500 status codes) from a particular Google API, contact your representative from Google Trends. 

Using the Census API
--------------------
We use the United States Census data to determine the demographic background for different geographic areas. The areas are FIPS encoded, to ease the search for an area we use a map from more native representations. For our proof of concept trial, we will focus on the counties of california and we create a map in `census/demographics.py`. 

##### Understanding Census Parameters
We are using the 5 year ACS survey provided by the United States Census. The document outlining search parameters on the Census website is very dense, therefore we outline our own set of parameters that are useful in `census/ReadMe.md`.


Bug Reporting
-------------
Report any bugs to wsumfest@gmail.com.
