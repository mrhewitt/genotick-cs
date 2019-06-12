import os
import time
import numpy as np
import pandas as pd
import subprocess
import sys
import random
import yaml
import re

from os import listdir
from os.path import isfile, join
from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen
from shutil import copyfile
from shutil import move

def log(message):
	f = open("simulate.log","a+")
	f.write(message + "\r\n")
	f.close()
	print(message)
	
	
def install_genotick():
	if not os.path.isfile('genotick.jar'):
		log("Installing Genotick...")
		
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
			save_config_line = True
			for i in ('#populationDAO','performTraining','startTimePoint','endTimePoint','populationDesiredSize','dataMaximumOffset'):
				save_config_line &= (line.decode('utf-8').find(i) == -1)
			if save_config_line:
				f.write(line)
			
		f.close();
		
			
def reverse_data(): 
	print("\n\n===================================\n")
	log("Reversing data...");
	
	for f in os.scandir('raw'):
		if f.name.startswith("reverse_"):
			log("Removing {}".format(f.path))
			os.unlink(f.path)
			
	subprocess.run(["java", "-jar", "genotick.jar", "reverse=raw"])
	print("\n\n===================================\n")

#	onlyfiles = [f for f in listdir(data_path) if isfile(join(data_path, f))]


def prepare_run(config):
	log("Preparing run...")
	
	if not os.path.isdir('data'):
		log("data folder does not exist, creating...")
		os.mkdir('data')
		
	# remove data files from previous runs
	for f in os.scandir('data'):
		if f.name.endswith(".csv"):
			log("Removing old data file {}".format(f.path))
			os.unlink(f.path)
		
	# select a random file from the raw data directory to train
	# check config first, if the user specified a list of markets to use, select only from those
	if 'market' in config['default']:
		if type(config['default']['market']) == 'str':
			market = config['default']['market']
		else:
			market = random.choice(config['default']['market'])
	else:
		market = random.choice([f for f in listdir('raw') if isfile(join('raw/', f)) and f.find('reverse_') == -1]).replace('.csv','')
	
	log("Using market {}".format(market))
	copyfile('raw/{}.csv'.format(market), 'data/{}.csv'.format(market))
	copyfile('raw/reverse_{}.csv'.format(market), 'data/reverse_{}.csv'.format(market))

	
	# delete config from previous run
	if os.path.isfile('config.txt'):
		os.unlink('config.txt')
		
	# make fresh copy of default config file and put in our custom run settings 	
	copyfile('empty_config.txt', 'config.txt')
	
	# if there is a custom configuration provided for the selected market, use this settings instead of the deault
	# any settings missing from custom market config will be taken from the default config
	settings = config['default']
	if market in config: 
		for key in config[market]:
			settings[key] = config[market][key]

	populationDesiredSize = random.choice(settings['populationDesiredSize'])			
	dataMaximumOffset = random.choice(settings['dataMaximumOffset'])
	
	f = open("config.txt","a+")
	f.write("performTraining\ttrue")
	f.write("\r\npopulationDesiredSize\t{}\r\n".format(populationDesiredSize))
	f.write("dataMaximumOffset\t{}\r\n".format(dataMaximumOffset))
	f.write("startTimePoint\t{}\r\n".format(settings['startTimePoint']))
	f.write("endTimePoint\t{}\r\n".format(settings['endTimePoint']))
	f.close()
	
	log("Using config:")
	log("    populationDesiredSize\t{}".format(populationDesiredSize))
	log("    dataMaximumOffset\t{}".format(dataMaximumOffset))
	log("    startTimePoint\t{}".format(settings['startTimePoint']))
	log("    endTimePoint\t{}".format(settings['endTimePoint']))
	
	print("\n\n===================================\n")

	
def process_result(type):
	log("Processing Result...")
	
	results = {}
	if not os.path.isdir('results'):
		log("Missing results folder, creating...")
		os.mkdir('results')
	elif os.path.isfile('results/results.yaml'):
		with open("results/results.yaml") as f:
			results = yaml.safe_load(f)
			
	pid = ''
	for f in os.scandir('.'):
		if f.name.startswith("predictions_"):
			pid = f.name.split('_').pop().split('.').shift()
			break
			
	if pid != '':

		# open the log, look for the profit recordings, we want the following:
		#  Total profit for market [x]: [n]%   <-  the actual account gain/loss
		#  Total trades: [n], profitable trades: [n]   <- win rate
		market = ''
		profit = 0
		total_trades = 0
		profitable_trades = 0
		for line in open('genotick-log-{}.csv'.format(pid)).readlines():	
			match = re.search("Total profit for market ([a-zA-Z\-]): (\d+\.\d+) %",line)
			if match:
				market = match.group(1)
				profit = match.group(2)
			else: 
				match = re.search("Total trades: (\d+), profitable trades: (\d+)",line)
				if match:
					total_trades = match.group(1)
					profitable_trades = match.group(2)
					winrate = float(profitable_trades)/float(total_trades)
		
		key = market + '-' + pid
		if not key in results:
			results[key] = {}
		results[key][type] = {'Percent': profit,'TotalTrades': total_trades, 'ProfitableTrades': profitable_trades, 'WinRate':winrate} 
			
		folder_name = 'results/{}-{}/{}'.format(market,pid,type)
		log("Storing results in {}".format(folder_name))
		
		os.mkdir(folder_name)			
		move('predictions_{}.csv'.format(pid),folder_name)
		move('profit_{}.csv'.format(pid),folder_name)
		move('config.txt',folder_name)
		move('savedPopulation_' + pid, folder_name)
	
		with open('results/results.yaml', 'w') as f:
			yaml.dump(results, f, default_flow_style=False)	
	
	else:
		log("Cannot find predictions output")
		
	# read the last two lines to determine how much profit was made
	# not most efficient has whole log has to be cached but its simple and files are not huge
	#for line in reversed(list(open("filename"))):
    #print(line.rstrip())
	
	
def prepare_oos(config):
	log("Preparing OOS...")
	
	# delete config from previous run
	if os.path.isfile('config.txt'):
		os.unlink('config.txt')
		
	# we start making predictions in OOS from the last day we did the training on, this predicts for tomorrow
	# i.e. the first day that we have not yet trained for	
	# no end time, we use rest of data for OOS
	copyfile('empty_config.txt', 'config.txt')
	
	f = open("config.txt","a+")
	f.write("startTimePoint\t{}\r\n".format(settings['endTimePoint']))
	# dont train, just predict
	f.write("performTraining\tfalse")
	# use the population we created, but from the ram drive for speed, we are not going to save this
	#f.write("populationDAO\t{}:\{}".format(config.ramdrive,''))
	f.close()
	
	print("\n\n===================================\n")
	

def prepare_trained_oos():
	log("Preparing OOS Training...")
	
	# delete config from previous run
	if os.path.isfile('config.txt'):
		os.unlink('config.txt')
		
	# we start making predictions in OOS from the last day we did the training on, this predicts for tomorrow
	# i.e. the first day that we have not yet trained for	
	# no end time, we use rest of data for OOS
	copyfile('empty_config.txt', 'config.txt')
	
	f = open("config.txt","a+")
	f.write("startTimePoint\t{}\r\n".format(settings['endTimePoint']))
	# dont train, just predict
	f.write("performTraining\ttrue")
	# use the population we created, but from the ram drive for speed, we are not going to save this
	f.write("populationDAO\t{}:\{}".format(config.ramdrive,''))
	f.close()
	
	print("\n\n===================================\n")
	

	
def main():
	
	# install genotick jar and config files if they don't already exist in this folder
	install_genotick()

	f = open("lock","w+")
	f.close()
	
	while os.path.isfile('lock'): 
		# read the config file between runs, this allows users to ammend this to add/change settings whilst	
		# a simulation is taking place so these changes can take effect whenever the next simulation is started
		with open("config.yaml") as f:
			config = yaml.safe_load(f);
		
		# ensure all raw data is reversed, do this before each run in case new data files where dropped
		reverse_data()
		
		# select a random dataset to parse with some random settings, then begin training
		prepare_run(config)
		subprocess.run(["java", "-jar", "genotick.jar", "input=file:config.txt", "output=csv"],timeout=86400)
		# see if this result is on of the top, and if so save it for future reference
		process_result('InSample')	
		
		# small pause to give my old CPU a break!
		time.sleep(15)
		
		# now process the remaining data as an OOS period to determine how will the AI does on unseen data that it has
		# not been trained on
		prepare_oos()
		subprocess.run(["java", "-jar", "genotick.jar", "input=file:config.txt", "output=csv"],timeout=86400)
		process_result('OOS')
		
		# small pause to give my old CPU a break!
		time.sleep(15)
		
		# now process the OOS period again, but this time let the AI train after each month, this way we emulate real
		# trading of the OOS period better, new data is traded unseen/untrained, but the AI is allowed to train itself
		# on the OOS data that has been traded in logical chunks (monthly in this case)
		# TODO: make this a configurable period to allow non-daily data
		prepare_trained_oos()
		subprocess.run(["java", "-jar", "genotick.jar", "input=file:config.txt", "output=csv"],timeout=86400)
		process_result('TrainedOOS')
		
		# small pause to give my old CPU a break!
		time.sleep(15)
		
		
if __name__ == "__main__":
	main()