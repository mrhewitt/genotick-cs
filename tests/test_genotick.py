import pytest
from simulator.genotick import Genotick
from simulator.genotick import NoTradesError
from simulator.genotick import MissingGenotickFileError
from simulator.genotick import MarketMismatchError
from simulator.market import Market

@pytest.fixture
def raw_data(tmpdir):
	tmp = tmpdir.mkdir("raw")
	tmp.join('EURUSD-D.csv').write("20190101,1.2323,0,0,0,0\n20190102,1.24321,0,0,0,0\n20190103,1.2563,0,0,0,0\n")
	tmp.join('XTIUSD-D.csv').write("20190101,54.3,0,0,0,0\n20190102,55.23,0,0,0,0\n")	
	tmp.join('USDJPY-D.csv').write("20190101,110.234,0,0,0,0\n20190102,113.23,0,0,0,0\n")
	tmp.join('YM-D.csv').write("20190101,24738,0,0,0,0\n20190102,27432,0,0,0,0\n")
	return tmp
	
	
@pytest.fixture
def ram_drive(tmpdir):
	tmp = tmpdir.mkdir("ramdrive")
	return tmp

	
@pytest.fixture
def init_genotick(ram_drive):
	genotick = Genotick({'settings': {'RAMDrive': str(ram_drive)}})
#	genotick.install()
	return genotick
	
def test_reverse(init_genotick, raw_data):
	pass
#	assert init_genotick.is_installed() == True
#	init_genotick.reverse()
	# must have 8 files , 4 raw test + 4 reversed
#	assert len(os.listdir(str(rawdir))) === 8 
	
	
def test_get_pid(init_genotick, ram_drive):
	ram_drive.join('predictions_1234.csv').write('x');
	assert init_genotick.get_pid() == '1234'	
	
def test_parse_for_profit(init_genotick):
	m,r = init_genotick.parse_for_profit("Total profit for market EURUSD-D: 1234.5 ticks, avg. 1.2 ticks / trade")
	assert m == 'EURUSD-D'
	assert type(r) is dict
	assert 'Ticks' in r and r['Ticks'] == '1234.5'
	assert 'Ticks Per Trade' in r and r['Ticks Per Trade'] == '1.2'	
	
	m,r = init_genotick.parse_for_profit("Total profit for market XTIUSD-D: 100 ticks, avg. 2 ticks / trade")
	assert m == 'XTIUSD-D'
	assert type(r) is dict
	assert 'Ticks' in r and r['Ticks'] == '100'
	assert 'Ticks Per Trade' in r and r['Ticks Per Trade'] == '2'		

	
	m,r = init_genotick.parse_for_profit("Total trades: 1234, profitable trades: 567")
	assert type(m) is bool and m == False
	
def test_parse_for_trades(init_genotick):
	p = init_genotick.parse_for_trades("Total trades: 2000, profitable trades: 1000")
	assert p[0] == 2000 and p[1] == 0.5

	try:
		p = init_genotick.parse_for_trades("Total trades: 0, profitable trades: 0")
		# fail if we get here, no trades should throw
		assert False
	except NoTradesError:
		pass
		
	p = init_genotick.parse_for_trades("Total profit for market EURUSD-D: 1234.5 ticks, avg. 1.2 ticks / trade")
	assert type(p[0]) is bool and p[0] == False
	
def test_fetch_outcome(init_genotick, ram_drive, raw_data):
	markets = Market({'default':{},'settings':{'raw_directory': str(raw_data)}})
	markets.use('EURUSD-D')
	markets.use('XTIUSD-D')
	
	ram_drive.join('predictions_1234.csv').write('x');

	# no genotick log file, missing file error
	try:
		r = init_genotick.fetch_outcome(markets)
		#except a MissingGenotickFileError exception
		assert False
	except MissingGenotickFileError:
		pass	
	ram_drive.join('genotick-log-1234.txt').write('xyz\nTotal profit for market EURUSD-D: 1234.5 ticks, avg. 1.2 ticks / trade\nTotal profit for market XTIUSD-D: 100 ticks, avg. 2 ticks / trade\n\nTotal trades: 2000, profitable trades: 1000');

	# no profits file, missing file error
	try:
		r = init_genotick.fetch_outcome(markets)
		#except a MissingGenotickFileError exception
		assert False
	except MissingGenotickFileError:
		pass
	ram_drive.join('profit_1234.csv').write("20190101,-10,-10\n20190102,10,20\n20190103,40,30\n20190104,20,-20\n")

	# successful parsing
	r = init_genotick.fetch_outcome(markets)
	assert type(r) is dict and 'EURUSD-D' in r and 'XTIUSD-D' in r
	assert len(r) == 12
	assert 'Ticks' in r['EURUSD-D'] and r['EURUSD-D']['Ticks'] == '1234.5'
	assert 'Ticks' in r['XTIUSD-D'] and r['XTIUSD-D']['Ticks'] == '100'
	assert 'Ticks Per Trade' in r['EURUSD-D'] and r['EURUSD-D']['Ticks Per Trade'] == '1.2'
	assert 'Ticks Per Trade' in r['XTIUSD-D'] and r['XTIUSD-D']['Ticks Per Trade'] == '2'
	assert 'Total Trades' in r and r['Total Trades'] == 2000
	assert 'Win Rate' in r and r['Win Rate'] == 0.5
	assert 'Net Ticks' in r and r['Net Ticks'] == 20
	assert 'Max Abs. Drawdown' in r and r['Max Abs. Drawdown'] == -10
	assert 'Max Profit' in r and r['Max Profit'] == 40
	assert 'Biggest Winner' in r and r['Biggest Winner'] == 30
	assert 'Biggest Looser' in r and r['Biggest Looser'] == -20
	assert 'Avg. Trade' in r and r['Avg. Trade'] == 5
	assert 'Avg. Loosing Trade' in r and r['Avg. Loosing Trade'] == -15
	assert 'Avg. Winning Trade' in r and r['Avg. Winning Trade'] == 25

	# log has missing market
	ram_drive.join('genotick-log-1234.txt').remove()
	ram_drive.join('genotick-log-1234.txt').write('xyz\nTotal profit for market XTIUSD-D: 100 ticks, avg. 2 ticks / trade\n\nTotal trades: 2000, profitable trades: 1000');
	try:
		r = init_genotick.fetch_outcome(markets)
		#except a mistamch exception
		assert False
	except MarketMismatchError:
		pass
		
	# run resulted in no trades	
	ram_drive.join('genotick-log-1234.txt').remove()
	ram_drive.join('genotick-log-1234.txt').write('xyz\nxyz\nTotal profit for market EURUSD-D: 1234.5 ticks, avg. 1.2 ticks / trade\nTotal profit for market XTIUSD-D: 100 ticks, avg. 2 ticks / trade\n\nTotal trades: 0, profitable trades: 1000');
	try:
		r = init_genotick.fetch_outcome(markets)
		#except a NoTradesError exception
		assert False
	except NoTradesError:
		pass
	
		
	
def test_clean(init_genotick,ram_drive):
	init_genotick.clean(str(ram_drive))
	assert ram_drive.join('profit_1234.csv').check(exists=1) == False
	assert ram_drive.join('genotick-log-1234.txt').check(exists=1) == False
	assert ram_drive.join('predictions_1234.csv').check(exists=1) == False
	