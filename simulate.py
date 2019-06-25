import yaml
import click
import os

from simulator.market import Market
from simulator.simulator import Simulate


@click.command()
@click.option('--market', default=None, help='Use this market, ignore market setting in config.yaml')
@click.option('--count', default=1, help='Number of markets to trade at once, selected randomly, use -1 to also randomize the count')
@click.option('--merge', default=None, help='Merge the data from a comma-delimited list of markets into main selected markets')
@click.option('--merge-count', default=None, help='Select [n] markets from --merge list randomly, -1 to also randomize the number selected') 
@click.option('--once', is_flag=True, help='Simulate a single iteration then exit')
@click.option('--random', is_flag=True, help='Use Genotick random settings option, ignore Genotick settings in config.yaml')
@click.option('--walkforward', default='', help='Do a walk-forward training simulation on the given market') 
@click.option('--go-live', default='', help='Prepare the given market for live trading and remove from simulation results')
@click.option('--result-directory', type=click.Path(), help="Directory to store results, defaults to results in current directory")
@click.option('--raw-directory', type=click.Path(), help="Location of raw data csv files, default to raw in current directory")
def cli(market, count, merge, merge_count, once, random, walkforward, go_live, result_directory, raw_directory):

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
		
		config['settings']['raw_directory'] = "raw" if raw_directory is None else raw_directory
		config['settings']['result_directory'] = "results" if result_directory is None else result_directory
		
		# build a list of markets to trade
		# this is a single entry if --market was given, otherwise picked as a random lize (default to 1)
		# from yaml markets option is given otherwise simply from the raw folder
		markets = Market(config)
		if market is None:
			markets.randomize(count)
		else:
			markets.use(market)
		
		# if a merge option is given, we additionally merge in the markets given as a comma-limited list
		# as additional columns onto the markets selected above. If merge_count is given they will be selected
		# randomly from the list given in --merge
		# note:  every market selected above (in cases of more than one market) will get same list of markets merged onto them
		#if merge is not None:
		#	markets.merge( merge.split(','), merge_count )
			
		#simulator = Simulate(config).run( markets ).process()	
		#if walkforward:	
		#	simulator.walkforward().process()
			

		# ensure all raw data is reversed, do this before each run in case new data files where dropped

		# small pause to give my old CPU a break!
		if not once:
		#	log("Run complete, sleeping...")
			time.sleep(15)
		else:
			# only running this once, so remove the lock file to automatically exit
			os.unlink('lock')
		