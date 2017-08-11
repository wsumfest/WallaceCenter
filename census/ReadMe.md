American Community Survey
=========================
For the purposes of our experiments, we will be evaluating demographics based on data provided by the ACS 5 year survey. Below we list important variables along with their descriptions. You can find important information abour FIPS codes in `ca_counties.csv`.

Variables
---------
To get the total value for a given variable, include an **E** after the number. To receive the margin of error, include an **M** after the number. 

1. `B00001_001`
    * Unweighted Population
2. `B00002_001`
    * Housing Units
3. `B01001_002`
    * Population of Males
4. `B01001_003` through `B01001_025`
    * Population of Males split up by age
5. `B01001_026`
    * Population of Females
6. `B01001_027` through `B01001_049`
    * Population of Females split up by age
7. `B06009_001`
    * Total number of participants in the survey for educational background
8. `B06009_002`
    * Number of participants with less than a high school degree or equivalents.


Using DMA's
===========
For several of our simulations, it is required to understand demographic information at a variety of granularities. One of these is set at the DMA (Designated Marketing Area) level, as specified by the Nielson Coorporation. We have liscened the 2017-2018 data from Nielson regarding which zipcodes make up the DMA's of interest. The `regionalDemographics.ipynb` notebook has several examples of regional demographic estimates made from underlying zipcode census data.

