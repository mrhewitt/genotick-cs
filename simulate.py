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
from shutil import copytree
from shutil import rmtree
from shutil import make_archive

def log(message):
	f = open("simulate.log","a+")
	f.write(message + "\r\n")
	f.close()
	print(message)

	
def remove_genotick_logs(path):
	log("Cleaning Genotick output...")
	for f in os.scandir(path):
		if f.name.startswith("genotick-") or f.name.startswith("profit_") or f.name.startswith("predictions_") or f.name == "config.txt":
			log("Removing {}".format(f.path))
			os.unlink(f.path)	
		if f.name.startswith('savedPopulation'):
			log("Removing {}".format(f.path))
			rmtree(f.path)

			
def genotick(install_path,message):
	log(message)
	cwd = os.getcwd()
	os.chdir(install_path)
	subprocess.run(["java", "-jar", "genotick.jar", "input=file:config.txt", "output=csv"],timeout=86400)
	os.chdir(cwd)
	
def install_genotick():
	if not os.path.isfile('genotick.jar'):
		log("Installing Genotick...")
		
		# download genotick installation and install the jar file
		zipfile = ZipFile(BytesIO(urlopen('https://genotick.com/static/download/genotick.zip').read())) 
		with open('genotick.jar', 'wb') as f:
			f.write( zipfile.open("genotick/genotick.jar").read() )
			f.close();

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
	remove_genotick_logs('r:')
	
	print("\n\n===================================\n")

	
def get_settings(market, config):
	# if there is a custom configuration provided for the selected market, use this settings instead of the deault
	# any settings missing from custom market config will be taken from the default config
	settings = config['default']
	if market in config: 
		for key in config[market]:
			settings[key] = config[market][key]
	return settings

	
def prepare_run(config):
	log("Preparing run...")
	remove_genotick_logs(config['settings']['RAMDrive'])
	
	data_dir = config['settings']['RAMDrive']+'data'
	if not os.path.isdir(data_dir):
		log("data folder does not exist, creating...")
		os.mkdir(data_dir)
		
	# remove data files from previous runs
	for f in os.scandir(data_dir):
		if f.name.endswith(".csv"):
			log("Removing old data file {}".format(f.path))
			os.unlink(f.path)
		
	# select a random file from the raw data directory to train
	# check config first, if the user specified a list of markets to use, select only from those
	if 'market' in config['settings']:
		if type(config['settings']['market']) == 'str':
			market = config['settings']['market']
		else:
			market = random.choice(config['settings']['market'])
	else:
		market = random.choice([f for f in listdir('raw') if isfile(join('raw/', f)) and f.find('reverse_') == -1]).replace('.csv','')
	
	log("Using market {}".format(market))
	copyfile('raw/{}.csv'.format(market), '{}/{}.csv'.format(data_dir,market))
	copyfile('raw/reverse_{}.csv'.format(market), '{}/reverse_{}.csv'.format(data_dir,market))
		
	# make fresh copy of default config file and put in our custom run settings 	
	copyfile('empty_config.txt', config['settings']['RAMDrive']+'config.txt')
	
	# if there is a custom configuration provided for the selected market, use this settings instead of the deault
	# any settings missing from custom market config will be taken from the default config
	settings = get_settings(market,config)
	
	populationDesiredSize = random.choice(settings['populationDesiredSize'])			
	dataMaximumOffset = random.choice(settings['dataMaximumOffset'])
	
	f = open(config['settings']['RAMDrive']+"config.txt","a+")
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

	
def get_instrument(instruments, market):	
	for name in instruments:
		if name == market.split('-').pop(0):
			return instruments[name] 
	return {'multiplier':1}
	
	
def fetch_outcome(config, resultPid):
	# search for a predictions file, and if one is found use it to extract the id of the run just cmpleted
	pid = ''
	for f in os.scandir(config['settings']['RAMDrive']):
		if f.name.startswith("predictions_"):
			pid = re.search("predictions_(\d+).csv",f.name).group(1)
			break
			
	if pid != '':
		if not resultPid:
			resultPid = pid
			
		# open the log, look for the profit recordings, we want the following:
		#  Total profit for market [x]: [n] ticks, avg. [n] ticks / trade  <-  the actual account gain/loss in ticks with the avg. gain/loss per trade in ticks
		#  Total trades: [n], profitable trades: [n]   <- win rate
		market = ''
		profit = 0
		total_trades = 0
		profitable_trades = 0
		result = {}
		for line in open('{}genotick-log-{}.txt'.format(config['settings']['RAMDrive'],pid)).readlines():
			
			match = re.search("Total profit for market ([a-zA-Z0-9\-]+): (\-?\d+\.\d+) ticks, avg. (\-?\d+\.\d+) ticks / trade",line)
			if match:
				market = match.group(1)
				instrument = get_instrument(config['instruments'],market)
				total_ticks = float(match.group(2)) * instrument['multiplier']
				tickspertrade = float(match.group(3)) * instrument['multiplier']
			else: 
				match = re.search("Total trades: (\d+), profitable trades: (\d+)",line)
				if match and market != '':
					total_trades = int(match.group(1))
					if total_trades == 0:
						log("Rejected - no trades taken")
						return {'market':False,'pid':False}
					profitable_trades = int(match.group(2))
					winrate = float(profitable_trades)/float(total_trades)
		
		if market == '':
			log('Cannot find results, rejecting run...')
			return False,False
		else:
			log("{} :: Total Ticks: {}, Ticks Per Trade: {}, Win Rate: {}".format(market,total_ticks,tickspertrade,winrate*100))
			return {'Ticks': total_ticks,'TicksPerTrade':tickspertrade,'TotalTrades': total_trades, 'ProfitableTrades': profitable_trades, 'WinRate':winrate}, {'market':market,'pid':resultPid}
		
	else:
		return False, False
		
	
def process_result(type,config, resultPid=False):
	log("Processing Result...")
	
	results = {}
	if not os.path.isdir('results'):
		log("Missing results folder, creating...")
		os.mkdir('results')
	elif os.path.isfile('results/results.yaml'):
		with open("results/results.yaml") as f:
			results = yaml.safe_load(f)

	# parse the outcome of the genotick run, and fetch the market, pid and profit statistics of the run in ticks
	outcome, location = fetch_outcome(config,resultPid)			
	if outcome != False:
		
		# only accept this run if it produced a sufficent amount of profit, either net ticks or average number of ticks made on each trade
		# checking for avg. per trade lets us filter runs that show a large profit, but when compared to the actual number of trades taken
		# the profit per trade is very small (i.e. harder to overcome slippage/spread and perhaps not great way to invest capital given time period)
		if outcome['Ticks'] >= config['settings'][type]['minProfit'] and outcome['TicksPerTrade'] >= config['settings'][type]['minTicksPerTrade']: 
			
			# results are stored in format MARKET-PID in results , e.g.  EURUSD-2912 to allow multiple runs on same pair
			# note:  PID is not gaurenteed to be unique, this needs to be fixed
			pid = location['pid']
			key = location['market'] + '-' + pid
			if not key in results:
				results[key] = {}
				
			# store the result in the yaml	
			results[key][type] = outcome

			folder_name = 'results/{}/{}'.format(key,type)
			log("Storing results in {}".format(folder_name))
		
			# backup the run outcome files and population to the results folder for the type of run (insample / oos etc) 
			os.makedirs(folder_name, exist_ok=True)			
			move('{}genotick-log-{}.txt'.format(config['settings']['RAMDrive'],pid),folder_name)
			move('{}predictions_{}.csv'.format(config['settings']['RAMDrive'],pid),folder_name)
			move('{}profit_{}.csv'.format(config['settings']['RAMDrive'],pid),folder_name)
			move('{}config.txt'.format(config['settings']['RAMDrive']),folder_name)
			
			# todo: fetch this from the ramdrive and store archived populations as a zip for performance and not having 10000's files on disk
			if os.path.isdir('{}savedPopulation_{}'.format(config['settings']['RAMDrive'],pid)) and type == 'InSample':
				make_archive(folder_name+'/population','zip','{}savedPopulation_{}'.format(config['settings']['RAMDrive'],pid))
	#			move('savedPopulation_' + pid, folder_name)
		
			with open('results/results.yaml', 'w') as f:
				yaml.dump(results, f, default_flow_style=False)	
			
			return location
		else:
			remove_genotick_logs(config['settings']['RAMDrive'])
			
			# remove this market from the result list altogether, as we dont want a population that fails any of the tests 
			if os.path.isdir('results/' + key):
				rmtree('results/' + key)
			results.pop(key,None)
			with open('results/results.yaml', 'w') as f:
				yaml.dump(results, f, default_flow_style=False)	
					
			log("Rejected {} - tick count of {} is less than minimum setting of {}".format(type,total_ticks,config['settings'][type]['minProfit']))
			return {'market':False,'pid':False}
		
	else:
		log("Cannot find predictions output")
		return {'market':False,'pid':False}
		
	
def prepare_oos(config, location):
	log("Preparing OOS...")
		
	# we start making predictions in OOS from the last day we did the training on, this predicts for tomorrow
	# i.e. the first day that we have not yet trained for	
	# no end time, we use rest of data for OOS
	copyfile('empty_config.txt', config['settings']['RAMDrive']+'config.txt')
		
	settings = get_settings(location['market'],config)
	
	f = open("config.txt","a+")
	f.write("startTimePoint\t{}\r\n".format(settings['endTimePoint']))
	# dont train, just predict
	f.write("performTraining\tfalse\r\n")
	# use the population we created, we are just training so can read it from the regular drive
	f.write("populationDAO\tsavedPopulation_{}\r\n".format(location['pid']))
	f.close()
	
	print("\n\n===================================\n")
	

def prepare_trained_oos(config, location):
	log("Preparing OOS Training...")
	
	# delete config from previous run
	if os.path.isfile('config.txt'):
		os.unlink('config.txt')
		
	# we start making predictions in OOS from the last day we did the training on, this predicts for tomorrow
	# i.e. the first day that we have not yet trained for	
	# no end time, we use rest of data for OOS
	copyfile('empty_config.txt', 'config.txt')
	
	settings = get_settings(location['market'],config)
	
	f = open("config.txt","a+")
	f.write("startTimePoint\t{}\r\n".format(settings['endTimePoint']))
	# dont train, just predict
	f.write("performTraining\ttrue\r\n")
	# use the population we created, but from the ram drive for speed, we are not going to save this
	f.write("populationDAO\t{}savedPopulation_{}\r\n".format(config['settings']['ramdrive'],location.pid))
	f.close()
	
	# copy the saved population onto the ramdrive for processing, tranining off a ramdrive will be significantly
	# faster than on a regular sata or even M/sdd, 
	copytree("results/{}-{}/InSample/savedPopulation_{}".format(location['market'],location['pid'],location['pid']), "/".format(config['settings']['ramdrive']))
	
	print("\n\n===================================\n")
	

	
def main():

	# install genotick jar and config files if they don't already exist in this folder
	# note: removed this feature as this now requires the build from my fork, see readme
	#install_genotick()

	# create lock file to keep the process running until this file is removed
	# removing this file will cause the simulator to complete the current simulation then exit
	f = open("lock","w+")
	f.close()
	
	while os.path.isfile('lock'): 

		# read the config file between runs, this allows users to ammend this to add/change settings whilst	
		# a simulation is taking place so these changes can take effect whenever the next simulation is started
		with open("config.yaml") as f:
			config = yaml.safe_load(f);
		if config['settings']['RAMDrive'] != '':
			config['settings']['RAMDrive'] += ':/'
			
		# ensure run is clean
		remove_genotick_logs(config['settings']['RAMDrive'])

		# ensure all raw data is reversed, do this before each run in case new data files where dropped
		reverse_data()

		# select a random dataset to parse with some random settings, then begin training
		prepare_run(config)
		genotick(config['settings']['RAMDrive'],"Running Genotick for initial training")
		# see if this result is on of the top, and if so save it for future reference
		location = process_result('InSample',config)

		# only carry on if we found valid result
		if location['market']:
			# small pause to give my old CPU a break!
			time.sleep(15)
			
			# now process the remaining data as an OOS period to determine how will the AI does on unseen data that it has
			# not been trained on
			if config['settings']['oos']:
				prepare_oos(config, location)
				genotick(config['settings']['RAMDrive'],"Running Genotick for OOS prediction generation")
				process_result('OOS',config,location['pid'])	
				# small pause to give my old CPU a break!
				time.sleep(15)
			
			# now process the OOS period again, but this time let the AI train after each month, this way we emulate real
			# trading of the OOS period better, new data is traded unseen/untrained, but the AI is allowed to train itself
			# on the OOS data that has been traded in logical chunks (monthly in this case)
			# TODO: make this a configurable period to allow non-daily data
			#prepare_trained_oos()
		#	subprocess.run(["java", "-jar", "genotick.jar", "input=file:config.txt", "output=csv"],timeout=86400)
			#process_result('TrainedOOS')
			
		# small pause to give my old CPU a break!
		log("Run complete, sleeping...")
		time.sleep(15)
		
		
if __name__ == "__main__":
	main()