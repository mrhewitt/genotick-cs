import click
from visualizer.equityparser import EquityParser

@click.command()
@click.option('--period', default=20, help="Period for the Rolling Mean to apply to the equity curve")
@click.option('--filter', is_flag=True, help="Produce a filtered equity curve using given rolling mean")
@click.option('--multiplier', default=1, help="Use this to turn FX pip data into whole pips") 
@click.argument('profits', type=click.File('r'), required=True)
def cli(period,filter,multiplier,profits):
	"""
	Generate an equity curve graph from a Genotick profits CSV file
	"""
	
	ecurve = EquityParser( profits, multiplier )
	ecurve.show_equity_curve(period,filter);
