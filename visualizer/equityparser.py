#from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import pandas as pd

class EquityParser:

	pnl = False
	multiplier = 1
	mean_column = ''
	
	def __init__(self, profit_file, multiplier):
		self.pnl = pd.read_csv(profit_file,header=None,names=['date','cummulative','pertrade'],index_col=0,parse_dates=True)
		self.multiplier = multiplier
		self.pnl['cummulative'] = self.pnl['cummulative'].apply( lambda x: x*multiplier )
		self.pnl['pertrade'] = self.pnl['pertrade'].apply( lambda x: x*multiplier )
		
	def _apply_rolling_mean(self,period,data):
		self.mean_column = '{} Period Rolling Mean'.format(period)
		data[self.mean_column] = data['cummulative'].rolling(window=period).mean()
	
	def _render(self, df, filename):
		plot = df[['cummulative',self.mean_column]].plot(figsize=(16,6))
		plot.legend(['Equity',self.mean_column])
		plot.set_xlabel(None)
		plot.set_ylabel('Profit In Ticks')
		plot.yaxis_grid(True)
		plot.xaxis_grid(True)
		plot.get_figure().savefig(filename)
	
	def show_default_curve(self, period): 
		self.applyRollingMean(period,self.pnl)
		self.render(self.pnl,'equity.png')
		
	def show_filtered_curve(self, period):
		# track the state of the equity curve, true if we are above the mean, false if below
		system_active = True
		profits = []
		for index, row in self.pnl:
			# if system is active, apply the result of this trade to the filtered cummulative balance
			if system_active:
				# add this trade to the cumm profit and this day to the new equity curve
				cumm_profit += row['pertrade']
				profits.append([row['date'],cumm_profit])
				
				# if this trade took the default curve before the mean, stop trading for now
				if row['cummulative'] < row[self.mean_column]:
					system_active = False
			elif row['cummulative'] >= row[self.mean_column]:
				# this trade brought eq curve back above the mean, start trading again
				system_active = True
				
		# create new dataframe for the filtered curve and output it
		eq = pd.DataFrame(profits, columns = ['date','cummulative'])
		self.applyRollingMean(period,eq)
		self.render(eq,'filtered.png')
