import re
import subprocess

class Genotick:
	
	def __init__(self,config):
		self.config = config
		self.genotick_path = config['settings']['RAMDrive']
		
	def reverse(self):
		print("\n\n===================================\n")
		log("Reversing data...");
		
		for f in os.scandir(self.config.raw_directory):
			if f.name.startswith("reverse_"):
				log("Removing {}".format(f.path))
				os.unlink(f.path)
				
		subprocess.run(["java", "-jar", "genotick.jar", "reverse=" + self.config.raw_directory])
		self._clean(self.genotick_path)
		
		print("\n\n===================================\n")	
		
		
	def run(self, settings):
		self._clean()
		self._write_config(settings)
		cwd = os.getcwd()
		os.chdir(self.genotick_path)
		subprocess.run(["java", "-jar", "genotick.jar", "input=file:config.txt", "output=csv"],timeout=86400)
		self.pid = self._post_process()
		os.chdir(cwd)	
		return self.pid

		
	def fetch_outcome(self, markets):
		# search for a predictions file, and if one is found use it to extract the id of the run just cmpleted
		if self.pid != '':
				
			# open the log, look for the profit recordings, we want the following:
			#  Total profit for market [x]: [n] ticks, avg. [n] ticks / trade  <-  the actual account gain/loss in ticks with the avg. gain/loss per trade in ticks
			#  Total trades: [n], profitable trades: [n]   <- win rate
			market = ''
			profit = 0
			total_trades = 0
			profitable_trades = 0
			result = {}
			for line in open('{}genotick-log-{}.txt'.format(self.config['settings']['RAMDrive'],self.pid)).readlines():
				
				match = re.search("Total profit for market ([a-zA-Z0-9\\-]+): (\\-?\\d+\\.\\d+E?-?\\d?) ticks, avg. (\\-?\\d+\\.\\d+E?-?\\d?) ticks / trade",line)
				if match:
					market = match.group(1)
					instrument = get_instrument(config['instruments'],market)
					total_ticks = float(match.group(2)) * instrument['multiplier']
					tickspertrade = float(match.group(3)) * instrument['multiplier']
				else: 
					match = re.search("Total trades: (\\d+), profitable trades: (\\d+)",line)
					if match and market != '':
						total_trades = int(match.group(1))
						if total_trades == 0:
							raise NoTradesError(market)
						profitable_trades = int(match.group(2))
						winrate = float(profitable_trades)/float(total_trades)
			
			if market == '':
				raise NoMarketFoundError()
			else:
				log("{} :: Total Ticks: {}, Ticks Per Trade: {}, Win Rate: {}".format(market,total_ticks,tickspertrade,winrate*100))
				return {'Ticks': total_ticks,'TicksPerTrade':tickspertrade,'TotalTrades': total_trades, 'ProfitableTrades': profitable_trades, 'WinRate':winrate}, {'market':market,'pid':pid}
			
		else:
			raise NoResultsFoundError()
				
				
	def _post_process(self):
		pid = self._get_pid()
		return pid
	
	def _get_pid(self):
		pid = ''
		for f in os.scandir(self.genotick_path):
			if f.name.startswith("predictions_"):
				pid = re.search("predictions_(\\d+).csv",f.name).group(1)
				break		
		return pid
		
		
	def _write_config(self,settings):
		# make fresh copy of default config file and put in our custom run settings 	
		copyfile('empty_config.txt', self.genotick_path+'config.txt')
		
		f = open(self.genotick_path + "config.txt","a+")
		
		log("Using config:")
		if 'performTraining' in settings:
			f.write("performTraining\t{}".format(settings['performTraining']))
		if 'populationDesiredSize' in settings:
			f.write("\r\npopulationDesiredSize\t{}\r\n".format(settings['populationDesiredSize']))
			log("    populationDesiredSize\t{}".format(populationDesiredSize))
		if 'dataMaximumOffset' in settings:
			f.write("dataMaximumOffset\t{}\r\n".format(settings['dataMaximumOffset']))
			log("    dataMaximumOffset\t{}".format(dataMaximumOffset))
		if 'startTimePoint' in settings:
			f.write("startTimePoint\t{}\r\n".format(settings['startTimePoint']))
			log("    startTimePoint\t{}".format(settings['startTimePoint']))
		if 'endTimePoint' in settings:
			f.write("endTimePoint\t{}\r\n".format(settings['endTimePoint']))
			log("    endTimePoint\t{}".format(settings['endTimePoint']))
			
		f.close()
		
		
	def _clean():
		log("Cleaning Genotick output...")
		self._clean_path('.')
		self._clean_path(self.genotick_path)

		
	def _clean_path(path):
		for f in os.scandir(path):
			if f.name.startswith("genotick-") or f.name.startswith("profit_") or f.name.startswith("predictions_") or f.name == "config.txt":
				log("Removing {}".format(f.path))
				os.unlink(f.path)	
			if f.name.startswith('savedPopulation'):
				log("Removing {}".format(f.path))
				rmtree(f.path)	


