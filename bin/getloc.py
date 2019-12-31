import urllib.request
import urllib.parse
import json
import sys
import os

if (len(sys.argv) != 2):
	print("Expected a single location to be passed in to print geographic location for")
	sys.exit(16)


loc=sys.argv[1]
loc=urllib.parse.quote(loc)

mapapi="https://maps.googleapis.com/maps/api/geocode/json"
try:
	API_KEY=os.environ['API_KEY']
except KeyError:
	print("You need to set the API_KEY environment variable to your google API key")
	sys.exit(32)

with urllib.request.urlopen(mapapi + "?address=" + loc + "&key=" + API_KEY) as response:
	payload = response.read()

dict = json.loads(payload)
results = dict['results']
if (len(results) != 1):
	print("Expected exactly one result for <" + loc + "> but got " + str(len(results)) + " results.")
	sys.exit(16)

first=results[0]
geometry=first['geometry']
location=geometry['location']
lat=location['lat']
lng=location['lng']

if (lat > 0):
	gpslat=str(lat)
	gpslatref='N'
else:
	gpslat=str(-lat)
	gpslatref='S'

if (lng > 0):
	gpslng=str(lng)
	gpslngref='E'
else:
	gpslng=str(-lng)
	gpslngref='W'

print(
      "-GPSLatitude=" + gpslat + " -GPSLatitudeRef=" + gpslatref + " " +
      "-GPSLongitude=" + gpslng + " -GPSLongitudeRef=" + gpslngref
     )
	






