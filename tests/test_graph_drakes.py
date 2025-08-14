import unittest
import sys
import os
from unittest.mock import patch, MagicMock
import json

# Add the stats_visualization directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stats_visualization', 'visualizations'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestGraphDrakes(unittest.TestCase):
    def setUp(self):
        # Mock match data
        self.mock_match_data = {
            'info': {
                'participants': [
                    {'puuid': 'test_puuid', 'teamId': 100, 'win': True}
                ],
                'teams': [
                    {
                        'teamId': 100,
                        'objectives': {
                            'dragon': {'kills': 3}
                        }
                    },
                    {
                        'teamId': 200, 
                        'objectives': {
                            'dragon': {'kills': 1}
                        }
                    }
                ]
            }
        }

    @patch('graph_drakes.analyze.load_match_files')
    def test_extract_drake_data(self, mock_load_matches):
        from graph_drakes import extract_drake_data
        
        mock_load_matches.return_value = [self.mock_match_data]
        
        result = extract_drake_data('test_puuid')
        
        self.assertEqual(result['total_games'], 1)
        self.assertEqual(result['player_team_drakes'], [3])
        self.assertEqual(result['enemy_team_drakes'], [1])
        self.assertEqual(result['wins'], [True])

    @patch("matplotlib.pyplot.show")
    @patch('graph_drakes.extract_drake_data')
    def test_plot_drake_analysis(self, mock_extract, mock_show):
        from graph_drakes import plot_drake_analysis
        
        mock_data = {
            'total_games': 2,
            'player_team_drakes': [3, 2],
            'enemy_team_drakes': [1, 2],
            'wins': [True, False],
            'game_durations': [30, 25]
        }
        mock_extract.return_value = mock_data
        
        plot_drake_analysis('TestPlayer', mock_data)
        mock_show.assert_called_once()

if __name__ == "__main__":
    unittest.main()
