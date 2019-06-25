import pytest
from simulator.market import Market


@pytest.fixture
def market_data(tmpdir):
	tmp = tmpdir.mkdir("raw")
	tmp.join('EURUSD-D.csv').write("20190101,1.2323,0,0,0,0\n20190102,1.24321,0,0,0,0\n20190103,1.2563,0,0,0,0\n")
	tmp.join('XTIUSD-D.csv').write("20190101,54.3,0,0,0,0\n20190102,55.23,0,0,0,0\n")	
	tmp.join('USDJPY-D.csv').write("20190101,110.234,0,0,0,0\n20190102,113.23,0,0,0,0\n")
	tmp.join('YM-D.csv').write("20190101,24738,0,0,0,0\n20190102,27432,0,0,0,0\n")
	return tmp

def test_market_multiplier(market_data):	
	market = Market({'settings':{'raw_directory': str(market_data)}})
	assert market.get_multiplier('EURUSD-D') == 10000
	assert market.get_multiplier('XTIUSD-D') == 100
	assert market.get_multiplier('USDJPY-D') == 100
	assert market.get_multiplier('YM-D') == 1



def test_market_use(market_data):
	market = Market({'default':{},'settings':{'raw_directory': str(market_data)}})
	for instr in market.use('EURUSD-D'):
		assert instr['market'] == 'EURUSD-D'
		assert instr['instrument'] == 'EURUSD'
		assert instr['multiplier'] == 10000
	
	
def test_market_randomize(market_data):
	market = Market({'default':{},'settings':{'market':'XTIUSD-D','raw_directory': str(market_data)}})
	mkt = []
	for instr in market.randomize(2):
		mkt.append(instr['market'])
	# no market, pick two random markets from folder
	market = Market({'default':{},'settings':{'raw_directory': str(market_data)}})
	mkt = []
	for instr in market.randomize(2):
		mkt.append(instr['market'])

	# cannot start with more than 2 entries
	assert len(mkt) == 2	
	# must have 2 entries after removing duplicates	
	assert len(dict.fromkeys(mkt)) == 2

	# provide a market config list, expect 2 values back, must be the markets from the list
	market = Market({'default':{},'settings':{'market':['XTIUSD-D','YM-D'],'raw_directory': str(market_data)}})
	mkt = []
	for instr in market.randomize(2):
		mkt.append(instr['market'])
	
	# cannot start with more than 2 entries
	assert len(mkt) == 2	
	# must have 2 entries after removing duplicates	
	assert len(dict.fromkeys(mkt)) == 2
	# the two markets in the list must be the ones we provided
	mkt.extend(['XTIUSD-D','YM-D'])
	assert len(dict.fromkeys(mkt)) == 2
	
	# randomize 2 entries but given a fixed string in config, behaviour becomes "use"
	market = Market({'default':{},'settings':{'market':'XTIUSD-D','raw_directory': str(market_data)}})
	mkt = []
	for instr in market.randomize(2):
		mkt.append(instr['market'])
		
	# must have only 1 market
	assert len(mkt) == 1	
	# market must be the one provided in config, XTIUSD-D	
	assert mkt[0] == 'XTIUSD-D'
	