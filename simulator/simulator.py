import random		
from simulator.genotick import Genotick

class Simulate:
	def __init__(self,config):	
		self.config = config
		self.genotick = Genotick(config)
		
	def run(self,markets):
		self.genotick.run(self._prepare(), markets)
	
	def _prepare(self):
		log("Preparing run...")

		data_dir = self._setup_data_dir()
		
		# if there is a custom configuration provided for the selected market, use this settings instead of the deault
		# any settings missing from custom market config will be taken from the default config
		settings = get_settings(market,config)
		
		populationDesiredSize = random.choice(settings['populationDesiredSize'])			
		dataMaximumOffset = random.choice(settings['dataMaximumOffset'])
		
		for market in markets:
			log("Using market {}".format(market))
			copyfile('raw/{}.csv'.format(market), '{}/{}.csv'.format(data_dir,market))
			copyfile('raw/reverse_{}.csv'.format(market), '{}/reverse_{}.csv'.format(data_dir,market))
		
		print("\n\n===================================\n")	
		
		
	def _setup_data_dir(self):
		data_dir = self.config['settings']['RAMDrive']+'data'

		if not os.path.isdir(data_dir):
			log("data folder does not exist, creating...")
			os.mkdir(data_dir)
			
		# remove data files from previous runs
		for f in os.scandir(data_dir):
			if f.name.endswith(".csv"):
				log("Removing old data file {}".format(f.path))
				os.unlink(f.path)
				
		return data_dir
		
