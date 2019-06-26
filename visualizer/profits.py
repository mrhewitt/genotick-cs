from pandas import read_csv

class Profits:

	def __init__(self, csv_path):
		self.pnl = read_csv(csv_path,header=None,names=['date','cummulative','pertrade'],index_col=0,parse_dates=True)
	
	def get_net_profit(self):
		return self.pnl.cummulative.iloc[-1]
		
	def get_max_drawdown(self):
		return self.pnl.cummulative.min()
		
	def get_max_profit(self):
		return self.pnl.cummulative.max()
	
	def get_bigger_looser(self):
		return self.pnl.pertrade.min()
		
	def get_biggest_winner(self):
		return self.pnl.pertrade.max()
		
	def get_average_trade(self):
		return self.pnl.pertrade.mean()
		
	def get_average_looser(self):
		return self.pnl[self.pnl.pertrade<0].pertrade.mean()
		
	def get_average_winner(self):	
		return self.pnl[self.pnl.pertrade>0].pertrade.mean()
		
	def get_total_trades(self):
		return self.pnl[self.pnl.pertrade!=0].shape[0]
		
	def get_winning_trades(self):
		return self.pnl[self.pnl.pertrade>0].shape[0]
	
	def get_win_rate(self):
		return self.get_winning_trades()/self.get_total_trades()

		
	def get_total_real_trades(self):
		return self.pnl[self.pnl.pertrade!=0].shape[0]
		
	def get_winning_real_trades(self):
		return self.pnl[self.pnl.pertrade!=0].shape[0]
	
	def get_real_win_rate(self):
		return self.pnl[self.pnl.pertrade!=0].shape[0]
		
		
	def get_stats(self):
		return {'net_profit': self.get_net_profit(),
			    'max_drawdown': self.get_max_drawdown(),
			    'max_profit': self.get_max_profit(), 
				'biggest_looser': self.get_bigger_looser(),
				'biggest_winner': self.get_biggest_winner(),
				'average_trade': self.get_average_trade(),
				'average_looser': self.get_average_looser(),
				'average_winner': self.get_average_winner(),
				'total_trades': self.get_total_trades(),
				'winning_trades': self.get_winning_trades(),
				'win_rate': self.get_win_rate()
			}
				