import unittest
from unittest.mock import patch, mock_open
from league_stats_2023.graph_drakes import read_drake_data, plot_drakes  # Updated import

class TestGraphDrakes(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open, read_data="teamname,elders,elementaldrakes\nTeamA,2,5\nTeamB,1,3\n")
    def test_read_drake_data(self, mock_file):
        team_elders, team_elemental_drakes = read_drake_data("dummy.csv")
        self.assertEqual(team_elders, {"TeamA": 2, "TeamB": 1})
        self.assertEqual(team_elemental_drakes, {"TeamA": 5, "TeamB": 3})

    @patch("matplotlib.pyplot.show")
    def test_plot_drakes(self, mock_show):
        team_elders = {"TeamA": 2, "TeamB": 1}
        team_elemental_drakes = {"TeamA": 5, "TeamB": 3}
        plot_drakes(team_elders, team_elemental_drakes)
        mock_show.assert_called_once()

if __name__ == "__main__":
    unittest.main()
