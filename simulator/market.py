import random
import pandas as pd
from decimal import Decimal
from os import listdir
from os.path import isfile, join
				
class Market:
	def __init__(self,config):
		self.config = config
		self.index = 0
		self.markets = []

	def __iter__(self):
		self.index = 0
		return self

	def __next__(self): 
		try:
			result = self.markets[self.index]
		except IndexError:
			raise StopIteration
		self.index += 1
		return result
		
	def __len__(self):
		return len(self.markets)


	def use(self,market):
		instr = {'market': market, 'instrument': self._instrument_name(market), 'multiplier': self.get_multiplier(market), 'settings': self._get_settings(market)}
		self.markets.append(instr)
		return self
	
	def merge(self, merge_markets, count):
		for m in self.markets:
			self.markets[m]['merge_with'] = []
			
		return self
	
	def randomize(self,count):
		# select a random file from the raw data directory to train
		# check config first, if the user specified a list of markets to use, select only from those
		if 'market' in self.config['settings']:
			if type(self.config['settings']['market']) is str:
				self.use( self.config['settings']['market'] )
			else:
				self._random(self.config['settings']['market'],count)
		else:
			self._random([f.replace('.csv','') for f in listdir(self.config['settings']['raw_directory']) if isfile('{}/{}'.format(self.config['settings']['raw_directory'],f)) and f.find('reverse_') == -1], count)
		return self

		
	def get_multiplier(self,market):
		df = pd.read_csv( "{}/{}.csv".format(self.config['settings']['raw_directory'],market),header=None,names=['date','open','high','low','close','volume'],dtype={'open':str},index_col=0,parse_dates=True)
		digits = 1
		for index,row in df.iterrows():
			decimals = abs(Decimal(row['open']).as_tuple().exponent)
			if decimals > digits:
				digits = decimals
				
		# 5 is a special case, for fx pairs with 5 decimals, the 5th demical is actually a fraction of a pip, thus their
		# tick repsentation is actually a factor of 10000 not 100000 to leave the fractional pip as a fraction
		# ditto for a 3 digit fx pair, these are JPY pairs with a fractional pip
		if digits == 5:
			return 10000
		elif digits == 3:
			return 100
		elif digits == 1:
			return 1
		else:	
			return 10 ** digits

		
	def _random(self,list,count):
		while count and len(list) > 0:
			mkt = random.choice(list)
			self.use(mkt)
			list.remove(mkt)
			count = count - 1

			
	def _get_settings(self,market):
		# if there is a custom configuration provided for the selected market, use this settings instead of the deault
		# any settings missing from custom market config will be taken from the default config
		settings = self.config['default']
		if market in self.config: 
			for key in self.config[market]:
				settings[key] = self.config[market][key]
		return settings

		
	def _instrument_name(self,market):
		return market.split('-').pop(0)