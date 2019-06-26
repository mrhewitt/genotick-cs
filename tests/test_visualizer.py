import pytest
from visualizer.equityparser import EquityParser
from visualizer.profits import Profits


@pytest.fixture
def pid_files(tmpdir):
	tmp = tmpdir.mkdir("csv")
	tmp.join('profit_1234.csv').write("20190101,-10,-10\n20190102,10,20\n20190103,40,30\n20190104,20,-20\n")
	return tmp
	
def test_profit_stats(pid_files):
	p = Profits( str(pid_files) + "/profit_1234.csv" )
	assert p.get_net_profit() == 20
	assert p.get_total_trades() == 4
	assert p.get_max_drawdown() == -10
	assert p.get_max_profit() == 40
	assert p.get_bigger_looser() == -20
	assert p.get_biggest_winner() == 30
	assert p.get_average_trade() == 5
	assert p.get_average_looser() == -15
	assert p.get_average_winner() == 25
	assert p.get_winning_trades() == 2
	assert p.get_win_rate() == 0.5