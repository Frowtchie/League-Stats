import unittest
import sys
import os
from unittest.mock import patch, MagicMock
import datetime

# Add the stats_visualization directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stats_visualization', 'visualizations'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestGraphKills(unittest.TestCase):
    def setUp(self):
        # Mock match data
        self.mock_match_data = {
            'info': {
                'gameCreation': 1640995200000,  # 2022-01-01 timestamp
                'gameDuration': 1800,  # 30 minutes
                'participants': [
                    {
                        'puuid': 'test_puuid',
                        'teamId': 100,
                        'kills': 5,
                        'deaths': 2,
                        'assists': 8,
                        'championName': 'TestChamp',
                        'win': True
                    },
                    {
                        'puuid': 'other_puuid',
                        'teamId': 100,
                        'kills': 3,
                        'deaths': 1,
                        'assists': 6
                    }
                ]
            }
        }

    @patch('graph_kills.analyze.load_match_files')
    def test_extract_kills_data(self, mock_load_matches):
        from graph_kills import extract_kills_data
        
        mock_load_matches.return_value = [self.mock_match_data]
        
        result = extract_kills_data('test_puuid')
        
        self.assertEqual(result['total_games'], 1)
        self.assertEqual(result['kills'], [5])
        self.assertEqual(result['deaths'], [2])
        self.assertEqual(result['assists'], [8])
        self.assertEqual(result['champions'], ['TestChamp'])
        self.assertEqual(result['wins'], [True])
        # KDA = (5 + 8) / max(2, 1) = 6.5
        self.assertEqual(result['kda_ratios'], [6.5])

    @patch("matplotlib.pyplot.show")
    @patch('graph_kills.extract_kills_data')
    def test_plot_kills_analysis(self, mock_extract, mock_show):
        from graph_kills import plot_kills_analysis
        
        mock_data = {
            'total_games': 2,
            'kills': [5, 3],
            'deaths': [2, 4],
            'assists': [8, 6],
            'kda_ratios': [6.5, 2.25],
            'kill_participation': [80, 75],
            'champions': ['TestChamp1', 'TestChamp2'],
            'wins': [True, False]
        }
        mock_extract.return_value = mock_data
        
        plot_kills_analysis('TestPlayer', mock_data)
        mock_show.assert_called_once()

if __name__ == "__main__":
    unittest.main()
