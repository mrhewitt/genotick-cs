import os
import time
import numpy as np
import pandas as pd
import subprocess
import sys
import random

from os import listdir
from os.path import isfile, join
from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen
from shutil import copyfile

def install_genotick():
	if not os.path.isfile('genotick.jar'):
		print("Installing Genotick...\r\n")
		
		# download genotick installation and install the jar file
		zipfile = ZipFile(BytesIO(urlopen('https://genotick.com/static/download/genotick.zip').read()))
		#print(*zipfile.namelist(), sep = "\n") 
		with open('genotick.jar', 'wb') as f:
			f.write( zipfile.open("genotick/genotick.jar").read() )
			f.close();
		#zipfile.extract("genotick/genotick.jar");
		
		# extract genotick example config file and save it as our default config excluding settings that we will customize
		f = open('empty_config.txt','wb+')
		for line in zipfile.open("genotick/exampleConfigFile.txt").readlines():
			for i in ('#populationDAO','performTraining','startTimePoint','endTimePoint','populationDesiredSize','dataMaximumOffset'):
				if line.decode('utf-8').find(i) == -1:
					f.write(line)
		f.close();
		
			
def reverse_data(): 
	print("Reversing data...\r\n");
	
	for f in os.scandir('raw'):
		if f.name.startswith("reverse_"):
			os.unlink(f.path)
			
	subprocess.run(["java", "-jar", "genotick.jar", "reverse=raw"])

#	onlyfiles = [f for f in listdir(data_path) if isfile(join(data_path, f))]


def prepare_run():
	print("Preparing run...\r\n")
	
	# delete config from previous run
	if os.path.isfile('config.txt'):
		os.unlink('config.txt')
		
	# make fresh copy of default config file and put in our custom run settings 	
	copyfile('empty_config.txt', 'config.txt')
	
	f = open("config.txt","a+")
	# create a population with a random number of robots, in multiples of 10000, from 10000 to 100000 inclusive
	f.write("populationDesiredSize\t{}\r\n".format(random.randint(1,11) * 10000))
	# look back 1 month, 1 quarter (3 months) (+- 65 trading days), half year (6 months) [+- 124 trading days] or 1 year (12 months) [+- 265 trading days]
	f.write("dataMaximumOffset\t{}\r\n".format( random.choice((1,65,6*20,12*20)) ))
	# start time point is for now fixed to 2010 till end of 2018 leaving 2019 for walk-forward
	# this needs to become more flexible
	f.write("startTimePoint\t20100101\r\n")
	f.write("endTimePoint\t20181231\r\n")
	f.close()
	
	if not os.path.isdir('data'):
		os.mkdir('data')
		
	# remove data files from previous runs
	for f in os.scandir('data'):
		if f.name.endswith(".csv"):
			os.unlink(f.path)
		
	# select a random file from the raw data directory to train
	market = random.choice([f for f in listdir('raw') if isfile(join('raw/', f)) and f.find('reverse_') == -1])
	print("Using market {}\r\n".format(market))
	copyfile('raw/' + market, 'data/' + market)
	copyfile('raw/reverse_' + market, 'data/reverse_' + market)
	
	
def process_result():
	print("Processing Result...\r\n")
	
def main():
	
	# install genotick jar and config files if they don't already exist in this folder
	install_genotick()

	f = open("lock","w+")
	f.close()
	
	while os.path.isfile('lock'): 
		# ensure all raw data is reversed, do this before each run in case new data files where dropped
		reverse_data()
		
		# select a random dataset to parse with some random settings, then begin training
		prepare_run()
		subprocess.run(["java", "-jar", "genotick.jar", "input=file:config.txt"])
		# see if this result is on of the top, and if so save it for future reference
		process_result()
		# small pause to give my old CPU a break!
		time.sleep(15)
		
		
if __name__ == "__main__":
	main()