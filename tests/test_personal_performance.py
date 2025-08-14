import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the stats_visualization directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stats_visualization', 'visualizations'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestPersonalPerformance(unittest.TestCase):
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
                        'teamPosition': 'ADC',
                        'totalDamageDealtToChampions': 25000,
                        'goldEarned': 15000,
                        'win': True
                    }
                ]
            }
        }

    @patch('personal_performance.analyze.load_match_files')
    def test_load_player_match_data(self, mock_load_matches):
        from personal_performance import load_player_match_data
        
        mock_load_matches.return_value = [self.mock_match_data]
        
        result = load_player_match_data('test_puuid')
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.mock_match_data)

    @patch("matplotlib.pyplot.show")
    @patch('personal_performance.load_player_match_data')
    def test_plot_performance_trends(self, mock_load_data, mock_show):
        from personal_performance import plot_performance_trends
        
        mock_load_data.return_value = [self.mock_match_data]
        
        plot_performance_trends('test_puuid', 'TestPlayer')
        mock_show.assert_called_once()

    @patch("matplotlib.pyplot.show")
    @patch('personal_performance.load_player_match_data')
    def test_plot_champion_performance(self, mock_load_data, mock_show):
        from personal_performance import plot_champion_performance
        
        # Create multiple matches with same champion to meet minimum requirement
        mock_data = [self.mock_match_data, self.mock_match_data]
        mock_load_data.return_value = mock_data
        
        plot_champion_performance('test_puuid', 'TestPlayer')
        mock_show.assert_called_once()

if __name__ == "__main__":
    unittest.main()