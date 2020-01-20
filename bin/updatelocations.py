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
#	print(args);
	pgm = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
	stderr = pgm.stderr.readlines()
	for line in pgm.stderr:
		printerr(line.strip())
	for line in pgm.stdout:
		print(line.strip())
	pgm.communicate()

	return pgm.returncode

# processAlbumDir: 
#  -Create a temporary directory 
#  -copy the directory of pictures to the temporary directory
#  -Run exiftool on the directory of files to set the location
#  -Copy the pictures to the output directory
def processAlbumDir(googledir, fixdir, outdir, picloc):
	for item in os.listdir(googledir):
		s = os.path.join(googledir, item)
		if os.path.isfile(s):
			d = os.path.join(fixdir, item)
			shutil.copy2(s, d)

	with open(picloc, 'r') as locfile:
		loc = locfile.read().strip()
	args = "exiftool -overwrite_original -Subject= -Keywords+='Curator:MikeFulton' " + loc + " '" + fixdir + "'"

	rc=runpgm(args)
	if (rc != 0):
		printerr("Unable to set location for location: " + loc + " at: " + fixdir);
		return rc

	for item in os.listdir(fixdir):
		s = os.path.join(fixdir, item)
		if os.path.isfile(s):
			d = os.path.join(outdir, item)
			shutil.copy2(s, d)

	return 0


def verifyAlbum(googledir,locdir,outdir,entry):
	file = entry[0]
	location = entry[1]
	appleAlbum = entry[2]

	picdir = googledir + "/" + file
	if not(os.path.isdir(picdir)):
			print("Google directory: " + picdir + " does not exist. No processing performed.")
			return None

	locationFile = locdir + "/" + location
	if not(os.path.isfile(locationFile)):
			print("Location File: " + locationFile + " does not exist. No processing performed.")
			return None

	fixedDir = outdir + "/google/" + file
	appleDir = outdir + "/" + appleAlbum

	return { 
		"dir" : picdir,
		"loc" : locationFile, 
		"fixed" : fixedDir,
		"apple" : appleDir
	} 

def main():
	if (len(sys.argv) != 3):
		print("Expected a source directory of album files and a target directory to write new directories to")
		return(1)

	indir=sys.argv[1]
	outdir=sys.argv[2]

	albumdirpath = indir + "/albums"
	locdirpath = indir + "/locations"
	mapfilepath = indir + "/albums.map"

	albumdir = glob.glob(albumdirpath)
	locdir = glob.glob(locdirpath)
	mapfile  = glob.glob(mapfilepath)

	if (len(albumdir) != 1 or not(os.path.isdir(albumdir[0]))):
		print("Need to specify exactly one album directory: " + albumdirpath)
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
		album = verifyAlbum(albumdirpath,locdirpath,outdir,entry)
		if (album == None):
			return(4)

		albums.append(album)

	for album in albums:
		if not(os.path.exists(album['apple'])):
			try:
				os.makedirs(album['apple'])
			except PermissionError as e:
				print(str(e))
				print("Unable to create output directory: " + album['apple'])
				return 8
		if not(os.path.exists(album['fixed'])):
			try:
				os.makedirs(album['fixed'])
			except PermissionError as e:
				print(str(e))
				print("Unable to create output directory: " + album['fixed'])

	for album in albums:
		print("Writing: " + album['dir'] + " to: " + album['fixed'] + " and then: " + album['apple']);
		rc=processAlbumDir(album['dir'], album['fixed'], album['apple'], album['loc'])
		if (rc != 0):
			return rc

	return 0

if __name__ == '__main__':
    sys.exit(main())
