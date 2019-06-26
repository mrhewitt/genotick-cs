import re
import os
import subprocess
from shutil import copyfile
from shutil import rmtree
from visualizer.profits import Profits

class NoResultsFoundError(Exception):
	pass
	
class MarketMismatchError(Exception):
	pass
	
class EmptyMarketsError(Exception):
	pass

class NoTradesError(Exception):
	pass

class MissingGenotickFileError(Exception):
	pass

	
class Genotick:
	
	def __init__(self,config):
		self.config = config
		self.genotick_path = config['settings']['RAMDrive']

	def is_installed(self):
		return os.path.isfile('genotick.jar') and os.path.isfile(self.genotick_path + '/genotick.jar')
	
	def install(self):	
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

		# if genotick is not yet installed on the ram drive, do this now by just copying it across
		# note: we need the .jar in both local folder and ramdrive so that we can reverse raw data 	
		if not os.path.isfile(self.genotick_path + '/genotick.jar'):
			copyfile('genotick.jar', self.genotick_path)
			
			
	def reverse(self):
		print("\n\n===================================\n")
		log("Reversing data...");
		
		for f in os.scandir(self.config.raw_directory):
			if f.name.startswith("reverse_"):
				log("Removing {}".format(f.path))
				os.unlink(f.path)
				
		subprocess.run(["java", "-jar", "genotick.jar", "reverse=" + self.config['settings']['raw_directory']])
		self.clean('.')
		
		print("\n\n===================================\n")	
		
		
	def run(self, settings):
		self.clean(self.genotick_path)
		self._write_config(settings)
		cwd = os.getcwd()
		os.chdir(self.genotick_path)
		subprocess.run(["java", "-jar", "genotick.jar", "input=file:config.txt", "output=csv"],timeout=86400)
		os.chdir(cwd)
		return self
	
	def get_pid(self):
		pid = ''
		for f in os.scandir(self.genotick_path):
			if f.name.startswith("predictions_"):
				pid = re.search("predictions_(\\d+).csv",f.name).group(1)
				break		
		return pid

	def parse_for_profit(self, line):
		match = re.search("Total profit for market ([a-zA-Z0-9\\-]+): (\\-?\\d+\\.?\\d*E?-?\\d?) ticks, avg. (\\-?\\d+\\.?\\d*E?-?\\d?) ticks / trade",line)
		if match:
			ticks = match.group(2)
			net_ticks = net_ticks = ticks
			return (match.group(1), {'Ticks': ticks, 'Ticks Per Trade': match.group(3)})
		else:
			return (False,None)

	def parse_for_trades(self,line):
		match = re.search("Total trades: (\\d+), profitable trades: (\\d+)",line)
		if match:
			total_trades = int(match.group(1))
			if total_trades == 0:
				raise NoTradesError()
			return (total_trades, float(match.group(2))/float(total_trades))
		else:
			return (False,None)
	
	def fetch_outcome(self, markets):
		# search for a predictions file, and if one is found use it to extract the id of the run just cmpleted
		pid = self.get_pid()
		if pid != '':
			log_file = '{}/genotick-log-{}.txt'.format(self.genotick_path,pid)
			if not os.path.isfile(log_file):
				raise MissingGenotickFileError("{} log file is missing".format(log_file))
				
			profits_csv = "{}/profit_{}.csv".format(self.genotick_path,pid)
			if not os.path.isfile(profits_csv):
				raise MissingGenotickFileError("{} is missing".format(profits_csv))
				
			# open the log, look for the profit recordings, we want the following:
			#  Total profit for market [x]: [n] ticks, avg. [n] ticks / trade  <-  the actual account gain/loss in ticks with the avg. gain/loss per trade in ticks
			#  Total trades: [n], profitable trades: [n]   <- win rate
			instruments = {}
			total_trades = 0
			profitable_trades = 0
			for line in open(log_file).readlines():
				market,ticks = self.parse_for_profit(line)
				if market:
					instruments[market] = ticks
				else:
					trades = self.parse_for_trades(line)
					if trades: 
						total_trades = trades[0]
						win_rate = trades[1]

			# throw if we did not find any line covering the total number of trades taken
			if total_trades == 0:
				raise NoTradesError(market)

			if len(markets) != len(instruments):
				raise MarketMismatchError()
			
		#	log("{} :: Total Ticks: {}, Ticks Per Trade: {}, Win Rate: {}".format(market,total_ticks,tickspertrade,winrate*100))
			profits = Profits(profits_csv).get_stats()
			result = {
						'Net Ticks': profits['net_profit'],
						'Max Abs. Drawdown': profits['max_drawdown'],
						'Max Profit': profits['max_profit'],
						'Biggest Winner': profits['biggest_winner'],
						'Biggest Looser': profits['biggest_looser'],
						'Avg. Trade': profits['average_trade'],
						'Avg. Loosing Trade': profits['average_looser'],
						'Avg. Winning Trade': profits['average_winner'],
						'Total Trades': total_trades, 
						'Win Rate': win_rate
					}
			for m in instruments:
				result[m] = instruments[m]
				
			return result
				
		else:
			raise NoResultsFoundError()
				
		
	def _write_config(self,settings):
		# make fresh copy of default config file and put in our custom run settings 	
		copyfile('empty_config.txt', self.genotick_path+'/config.txt')
		
		f = open(self.genotick_path + "config.txt","a+")
		
		#log("Using config:")
		if 'performTraining' in settings:
			f.write("performTraining\t{}".format(settings['performTraining']))
		if 'populationDesiredSize' in settings:
			f.write("\r\npopulationDesiredSize\t{}\r\n".format(settings['populationDesiredSize']))
			#log("    populationDesiredSize\t{}".format(populationDesiredSize))
		if 'dataMaximumOffset' in settings:
			f.write("dataMaximumOffset\t{}\r\n".format(settings['dataMaximumOffset']))
			#log("    dataMaximumOffset\t{}".format(dataMaximumOffset))
		if 'startTimePoint' in settings:
			f.write("startTimePoint\t{}\r\n".format(settings['startTimePoint']))
			#log("    startTimePoint\t{}".format(settings['startTimePoint']))
		if 'endTimePoint' in settings:
			f.write("endTimePoint\t{}\r\n".format(settings['endTimePoint']))
			#log("    endTimePoint\t{}".format(settings['endTimePoint']))
			
		f.close()
		
		
	def clean(self,path):
		for f in os.scandir(path):
			if f.name.startswith("genotick-") or f.name.startswith("profit_") or f.name.startswith("predictions_") or f.name == "config.txt":
				log("Removing {}".format(f.path))
				os.unlink(f.path)	
			if f.name.startswith('savedPopulation'):
				log("Removing {}".format(f.path))
				rmtree(f.path)	


