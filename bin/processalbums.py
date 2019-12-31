from __future__ import print_function
import sys
import os
import glob
import re
import tempfile
import zipfile
import subprocess
import sys
import shutil

def printerr(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def runpgm(args):
	pgm = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
	stderr = pgm.stderr.readlines()
	for line in pgm.stderr:
		printerr(line.strip())
	for line in pgm.stdout:
		print(line.strip())
	pgm.communicate()

	return pgm.returncode

# processZipFile: 
#  -Create a temporary directory 
#  -Unzip the zip file of pictures to the temporary directory
#  -Run exiftool on the directory of files to set the date/time stamp and location
#  -Copy the pictures to the output directory
def processZipFile(zipname, outdir, picloc, date, time):
	tempdir = tempfile.mkdtemp()
	with zipfile.ZipFile(zipname, 'r') as zip:
		zip.extractall(tempdir)

	datetime='-DateTimeOriginal=\'' + date + ',' + time + '\''
	with open(picloc, 'r') as locfile:
		loc = locfile.read().strip()
	args = "exiftool -overwrite_original " + datetime + " " + loc + " " + tempdir

	rc=runpgm(args)
	if (rc != 0):
		printerr("Unable to set date/time/location for: " + zipname);
		return rc

	for item in os.listdir(tempdir):
		s = os.path.join(tempdir, item)
		if os.path.isfile(s):
			d = os.path.join(outdir, item)
			shutil.copy2(s, d)

	return 0

def createZipFile(file, name):
	zipname=tempfile.NamedTemporaryFile(suffix='.zip', delete=False).name
	zip = zipfile.ZipFile(zipname, 'w')
	zip.write(file, name)
	zip.close()

	return zipname

def verifyAlbum(googledir,singledir,locdir,outdir,entry):
	file = entry[0]
	location = entry[1]
	date = entry[2]
	time = entry[3]
	appleAlbum = entry[4]

	if (file.endswith(".zip")):
		picfile = googledir + "/" + file
		if not(os.path.isfile(picfile)):
			print("Google zip file: " + picfile + " does not exist. No processing performed.")
			return None
	elif (file.endswith(".jpg")):
		picfile = singledir + "/" + file
		if not(os.path.isfile(picfile)):
			print("Google jpeg file: " + picfile + " does not exist. No processing performed.")
			return None
	else:
		print("Input file needs to be either a .jpg or .zip file. File: " + file + " specified.")
		return None

	if not(os.path.isfile(picfile)):
		print("Google picture(s) file: " + picfile + " does not exist. No processing performed.")
		return None

	locationFile = locdir + "/" + location

	datePieces = re.split(":", date)
	if (len(datePieces) != 3):
		print("Invalid date specified. Format: yyyy:mm:dd")
		return None
	try:
		year = int(datePieces[0])
		month = int(datePieces[1])
		day = int(datePieces[2])
	except ValueError:
		print("Invalid year, month, or day specified. Format: yyyy:mm:dd");
		return None

	if (year < 1 or year > 9999):
		print("Invalid year specified for date: " + date)
		return None 
	if (month < 1 or month > 12):
		print("Invalid month specified for date: " + date)
		return None 
	if (day < 1 or day > 31):
		print("Invalid day specified for date: " + date)
		return None 

	timePieces = re.split(":", time)
	if (len(timePieces) != 3):
		print("Invalid time specified. Format: hh:mm:ss")
		return None
	try:
		hour = int(timePieces[0])
		minute = int(timePieces[1])
		second = int(timePieces[2])
	except ValueError:
		print("Invalid hour, minute or second specified. Format: hh:mm:ss");
		return None

	if (hour < 0 or hour > 23):
		print("Invalid hour specified for time: " + time)
		return None 
	if (minute < 0 or minute > 59):
		print("Invalid minute specified for time: " + time)
		return None 
	if (second < 0 or second > 59):
		print("Invalid second specified for time: " + time)

	appleDir = outdir + "/" + appleAlbum

	return { 
		"file" : picfile,
		"loc" : locationFile, 
		"date": date,
		"time": time, 
		"out" : appleDir
	} 

def main():
	if (len(sys.argv) != 3):
		print("Expected a source directory of album zip files and a target directory to write new directories to")
		return(1)

	indir=sys.argv[1]
	outdir=sys.argv[2]

	albumdirpath = indir + "/albums"
	singledirpath = indir + "/singles"
	locdirpath = indir + "/locations"
	mapfilepath = indir + "/albums.map"

	albumdir = glob.glob(albumdirpath)
	singledir = glob.glob(singledirpath)
	locdir = glob.glob(locdirpath)
	mapfile  = glob.glob(mapfilepath)

	if (len(albumdir) != 1 or not(os.path.isdir(albumdir[0]))):
		print("Need to specify exactly one album directory: " + albumdirpath)
		return(8)

	if (len(singledir) != 1 or not(os.path.isdir(singledir[0]))):
		print("Need to specify exactly one singles directory: " + singledirpath)
		return(8)

	if (len(locdir) != 1 or not(os.path.isdir(locdir[0]))):
		print("Need to specify exactly one location directory: " + locdirpath)
		return(8)

	if (len(mapfile) != 1 or not(os.path.isfile(mapfile[0]))):
		print("Need to specify exactly one album map file: " + mapfilepath)
		return(8)

	if (not(os.path.isdir(outdir))):
		print("Need to specify exactly one output directory: " + outdir)
		return(8)

	with open(mapfilepath, 'r') as mapfp:
		lines = mapfp.read().splitlines()

	entries = []
	for line in lines:
		line = line.strip()
		if (line != '' and not(line.startswith('#'))):
			entries.append(re.split("\t+", line))

	albums = []
	for entry in entries:
		album = verifyAlbum(albumdirpath,singledirpath,locdirpath,outdir,entry)
		if (album == None):
			return(4)

		albums.append(album)

	for album in albums:
		if not(os.path.exists(album['out'])):
			try:
				os.makedirs(album['out'])
			except PermissionError as e:
				print(str(e))
				print("Unable to create output directory: " + album['out'])
				return 8

	for album in albums:
		if (album['file'].endswith('.jpg')):
			zip = createZipFile(album['file'], os.path.basename(album['file']))
			if (zip == None):
				return 8
			else:
				album['zip'] = zip
		else:
			album['zip'] = album['file']

	for album in albums:
		print("Writing: " + album['file'] + " to: " + album['out']);
		rc=processZipFile(album['zip'], album['out'], album['loc'], album['date'], album['time'])
		if (rc != 0):
			return rc

	return 0

if __name__ == '__main__':
    sys.exit(main())
