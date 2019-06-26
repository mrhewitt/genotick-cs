#from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import pandas as pd


class EquityParser:

	def __init__(self, profit_file, multiplier):
		self.pnl = pd.read_csv(profit_file,header=None,names=['date','cummulative','pertrade'],index_col=0,parse_dates=True)
		self.multiplier = multiplier
		self.pnl['cummulative'] = self.pnl['cummulative'].apply( lambda x: x*multiplier )
		self.pnl['pertrade'] = self.pnl['pertrade'].apply( lambda x: x*multiplier )
		
		
	def _apply_rolling_mean(self,period,data):
		self.mean_column = '{} Period Rolling Mean'.format(period)
		data[self.mean_column] = data['cummulative'].rolling(window=period).mean()
	
	
	def _render(self, df, filename):
		plot = df[['cummulative',self.mean_column,'filtered']].plot(figsize=(16,6))
		plot.legend(['Cummulative Profit',self.mean_column,'Filtered'])
		plot.set_xlabel(None)
		plot.set_ylabel('Profit In Ticks')
		plot.yaxis.grid(True)
		plot.xaxis.grid(True)
		plot.get_figure().savefig(filename)
	
	
	def show_equity_curve(self, period, filtered): 

		if filtered:
			# track the state of the equity curve, true if we are above the mean, false if below
			system_active = True
			profits = []
			dates = []
			cumm_profit = 0
			self._apply_rolling_mean(period,self.pnl)
			for index,row in self.pnl.iterrows():
				# if system is active, apply the result of this trade to the filtered cummulative balance
				if system_active:
					# add this trade to the cumm profit and this day to the new equity curve
					cumm_profit += row['pertrade']
					profits.append(cumm_profit)
					dates.append(index)
					
					# if this trade took the default curve before the mean, stop trading for now
					if row['cummulative'] < row[self.mean_column]:
						system_active = False
				elif row['cummulative'] >= row[self.mean_column]:
					# this trade brought eq curve back above the mean, start trading again
					system_active = True
					profits.append(cumm_profit)
				else:
					profits.append(cumm_profit)
					
			# create new dataframe for the filtered curve and output it
	#		eq = pd.DataFrame(profits, columns = ['cummulative'], index=dates)
			self.pnl = self.pnl.assign( filtered = pd.Series(profits).values )
			
		self._render(self.pnl,'equity.png')
