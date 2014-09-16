#!/usr/bin/env python2

import feedparser

# Pulls in the RSS feed of housing posts from Craigslist (with a few options),
# scrapes each listing page for its address, and uses the Google Distance
# Matrix API to rank them by their walking distance to major Caltrain stations.

# Settings:
numBathrooms = 2
numBedrooms = 3
minAsk = 2500 # in dollars
maxAsk = 4000 # in dollars
region = 'sby' # craigslist region, sby = south bay, pen = peninsula, etc.

def buildListingsUrl(skip):
    url = 'http://sfbay.craigslist.org/search/{0}/apa?'.format(region)
    url += 'bathrooms={0}&bedrooms={1}'.format(numBathrooms, numBedrooms)
    url += '&maxAsk={0}&minAsk={1}'.format(maxAsk, minAsk)
    url += '&s={0}&format=rss'.format(skip)
    return url

def collectListings():
    print('Collecting listings...')
    skip = 0
    lastContenderCount = 0
    contenders = {}
    while True:
        url = buildListingsUrl(skip)
        feed = feedparser.parse(url)

        if len(feed['entries']) <= 0:
            return contenders
        for entry in feed['entries']:
            contenders[entry['link']] = entry['title']
        skip += len(feed['entries'])
        print(skip)

        if len(contenders) == lastContenderCount:
            break
        lastContenderCount = len(contenders)

    print('Found {0} unique listings.'.format(len(contenders)))
    return contenders

if __name__ == '__main__':
    contenders = collectListings()
