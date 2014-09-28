#!/usr/bin/env python2

# Pulls in the RSS feed of housing posts from Craigslist (with a few options),
# scrapes each listing page for its address, and uses the Google Distance
# Matrix API to rank them by their walking distance to major Caltrain stations.

# TODO: Actually use the Google Distance API, lol.

import feedparser
import HTMLParser
import os.path
import pickle
import re
import urllib2
import json as simplejson 
import sys
import heapq
from operator import itemgetter

# Settings:
numBathrooms = 2
numBedrooms = 3
minAsk = 2500 # in dollars
maxAsk = 4000 # in dollars
region = 'sby' # craigslist region, sby = south bay, pen = peninsula, etc.

# Constant-ish stuff. No need to mess with it.
addressRegex   = re.compile('<div class="mapaddress">(.*)</div>')
cityRegex      = re.compile('&amp;csz=(.*)&amp;')
listingCache   = 'listing.cache'
addressCache   = 'address.cache'
distanceCache  = 'distance.cache'
GOOGLE_API_BASE_URL = 'https://maps.googleapis.com/maps/api/distancematrix/json?origins='
DESTINATION = re.sub(r"\s+", '+', sys.argv[1])
API_KEY = sys.argv[2]

def dumpCache(obj, path):
    with open(path, 'wb') as f:
        pickle.dump(obj, f)

def loadCache(path):
    if os.path.isfile(path):
        with open(path, 'rb') as f:
            return pickle.load(f)
    return None

def buildListingsUrl(skip):
    url = 'http://sfbay.craigslist.org/search/{0}/apa?'.format(region)
    url += 'bathrooms={0}&bedrooms={1}'.format(numBathrooms, numBedrooms)
    url += '&maxAsk={0}&minAsk={1}'.format(maxAsk, minAsk)
    url += '&s={0}&format=rss'.format(skip)
    return url

def scrapeListings():
    print('Scraping listings...')
    skip = 0
    lastListingCount = 0
    listings = {}
    while True:
        url = buildListingsUrl(skip)
        feed = feedparser.parse(url)

        if len(feed['entries']) <= 0:
            return listings
        for entry in feed['entries']:
            listings[entry['link']] = entry['title']
        skip += len(feed['entries'])
        print(skip)

        if len(listings) == lastListingCount:
            break
        lastListingCount = len(listings)

    print('Fetched {0} unique listings.'.format(len(listings)))
    return listings

def loadListings():
    listings = loadCache(listingCache)
    if listings is None:
        listings = scrapeListings()
        dumpCache(listings, listingCache)
    else:
        print('Loaded {0} listings from cache.'.format(len(listings)))
    return listings

def scrapeAddress(url):
    markup = urllib2.urlopen(url).read()
    addressMatch = addressRegex.search(markup)
    if not addressMatch:
        return False
    address = addressMatch.group(1).strip()
    cityMatch = cityRegex.search(markup)
    if not cityMatch:
        return False
    city = cityMatch.group(1).strip().replace('++', ', ').replace('+', ' ')
    return '{0}, {1}'.format(address, city)

def loadAddresses(listings):
    addresses = loadCache(addressCache)
    if addresses is None:
        addresses = {}
    else:
        print('Loaded {0} addresses from cache.'.format(len(addresses)))

    htmlParser = HTMLParser.HTMLParser()
    curListing = 1
    totalListings = len(listings)
    if totalListings > 0:
        print('Scraping addresses from listings...')

    while len(listings) > 0:
        (url, title) = listings.popitem()
        print(u'[{0}/{1}] {2}'.format(curListing, totalListings, htmlParser.unescape(title)))
        curListing += 1

        address = scrapeAddress(url)
        if address:
            # Search for the square footage
            sqft = re.search( r'(\d{4})sqft', title, re.I)
            
            #  Call the Distance API here and return the distance
            (dist_val, dist_text) = getDistances(address)
            
            # Silly question, but does it matter that the title and sqft are in unicode?
            if sqft != None:
                addresses[url] = {'title': title, 'address': address, 'sqft': sqft.group(), 'distance': dist_text, 'value': dist_val}
            else:
                addresses[url] = {'title': title, 'address': address, 'sqft': None, 'distance': dist_text, 'value': dist_val}

        # This is horrendously inefficient, but Python is already slow, so who
        # cares, right? Right? *crickets*
        dumpCache(addresses, addressCache)
        dumpCache(listings, listingCache)
    return addresses

def formatAddress(addresses):
    temp = re.sub('[.!,;-?-]', ' ',addresses)
    formedAddress = re.sub('\s+','+',temp) 
    return formedAddress

def getDistances(org_address):
    address = formatAddress(org_address)
    
    googleUrl = GOOGLE_API_BASE_URL 
    googleUrl += '{0}|'.format(address)
    googleUrl += '&destinations={0}'.format(DESTINATION)
    googleUrl += '&mode=driving&units=imperial'
    googleUrl += '&key={0}'.format(API_KEY)
    # print googleUrl
    jsonObj = simplejson.load(urllib2.urlopen(googleUrl))
    # print simplejson.dumps(jsonObj,indent=4)
    if jsonObj['rows'][0]['elements'][0]['status'] == 'OK':
        dist_val = jsonObj['rows'][0]['elements'][0]['distance']['value']
        dist_text =  jsonObj['rows'][0]['elements'][0]['distance']['text']
        return (dist_val, dist_text)
    else:
        # NOT_FOUND or ZERO_RESULTS. Return large distance
        return ('1000000', None)

if __name__ == '__main__':
    listings = loadListings()
    addresses = loadAddresses(listings)
    
    # TODO: just print all the addresses and sqft for now
    newList = sorted(addresses.values(), key=lambda k: k['value'], reverse=True)
    
    # HORRIBLY INEFFICIENT WAY TO PRINT THE URL OF THE SORTED ITEMS
    for v in newList:
        print (v['distance'],v['address'],v['sqft']) 
        for i in addresses:
            if v['title'] == addresses[i]['title']:
                print i
                break
