#!/usr/bin/env python2

# Pulls in the RSS feed of housing posts from Craigslist (with a few options),
# scrapes each listing page for its address, and uses the Google Distance
# Matrix API to rank them by their walking distance to major Caltrain stations.

# Settings:
numBathrooms = 2
numBedrooms = 3
minAsk = 2500 # in dollars
maxAsk = 4000 # in dollars
region = "sby" # craigslist region, sby = south bay, pen = peninsula, etc.

def buildListingsUrl(skip):
    listingsUrl = "http://sfbay.craigslist.org/search/{0}/apa?".format(region)
    listingsUrl += "bathrooms={0}&bedrooms={1}".format(numBathrooms, numBedrooms)
    listingsUrl += "&maxAsk={0}&minAsk={1}".format(maxAsk, minAsk)
    listingsUrl += "&s={0}&format=rss".format(skip)
    return listingsUrl

if __name__ == "__main__":
    # Construct the listings URL.
    listingsUrl = buildListingsUrl()
    print(listingsUrl)
