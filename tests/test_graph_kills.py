import unittest
import sys
import os
from unittest.mock import patch, mock_open

# Add the stats_visualization directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stats_visualization', 'visualizations'))
from graph_kills import read_csv_data, plot_kills

class TestGraphKills(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open, read_data="teamname,position,kills,deaths,date\nTeamA,team,10,5,2023-01-01 12:00:00\n")
    def test_read_csv_data(self, mock_file):
        kills, enemy_kills, game_dates = read_csv_data("dummy.csv", "TeamA")
        self.assertEqual(kills, [10])
        self.assertEqual(enemy_kills, [5])
        self.assertEqual(game_dates, ["01/01 G1"])

    @patch("matplotlib.pyplot.show")
    def test_plot_kills(self, mock_show):
        game_dates = ["01/01 G1", "02/01 G2"]
        kills = [10, 15]
        plot_kills(game_dates, kills)
        mock_show.assert_called_once()

if __name__ == "__main__":
    unittest.main()
