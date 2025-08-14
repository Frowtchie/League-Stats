import unittest
import sys
import os
from unittest.mock import patch, Mock, mock_open
import json

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import league


class TestLeagueModule(unittest.TestCase):
    
    def test_load_player_config_from_env(self):
        """Test loading player config from environment variables"""
        with patch.dict(os.environ, {
            'PUUID_FROWTCH': 'test_puuid_1',
            'PUUID_OVEROWSER': 'test_puuid_2'
        }):
            config = league.load_player_config()
            self.assertEqual(config['Frowtch'], 'test_puuid_1')
            self.assertEqual(config['Overowser'], 'test_puuid_2')
    
    def test_load_player_config_fallback(self):
        """Test fallback to default config when no env vars set"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('league.logger'):
                config = league.load_player_config()
                self.assertIn('Frowtch', config)
                self.assertIn('Overowser', config)
                self.assertIn('Suro', config)
    
    @patch('league.requests.get')
    def test_fetch_match_data_success(self, mock_get):
        """Test successful match data fetch"""
        mock_response = Mock()
        mock_response.json.return_value = {'gameId': 12345}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = league.fetch_match_data('test_match_id', 'test_token')
        
        self.assertEqual(result, {'gameId': 12345})
        mock_get.assert_called_once()
    
    @patch('league.requests.get')
    def test_fetch_match_data_failure(self, mock_get):
        """Test match data fetch failure"""
        mock_get.side_effect = league.requests.exceptions.RequestException("API Error")
        
        with self.assertRaises(league.requests.exceptions.RequestException):
            league.fetch_match_data('test_match_id', 'test_token')
    
    @patch('league.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    @patch('league.json.dump')
    def test_save_match_data(self, mock_json_dump, mock_file, mock_mkdir):
        """Test saving match data to file"""
        test_data = {'gameId': 12345}
        
        league.save_match_data('test_match_id', test_data)
        
        mock_mkdir.assert_called_once_with(exist_ok=True)
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once_with(test_data, mock_file.return_value.__enter__.return_value, indent=4)
    
    @patch('league.requests.get')
    def test_fetch_match_history_success(self, mock_get):
        """Test successful match history fetch"""
        mock_response = Mock()
        mock_response.json.return_value = ['match1', 'match2', 'match3']
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = league.fetch_match_history('test_puuid', 3, 'test_token')
        
        self.assertEqual(result, ['match1', 'match2', 'match3'])
        mock_get.assert_called_once()
    
    @patch('league.fetch_match_data')
    @patch('league.save_match_data')
    def test_process_matches(self, mock_save, mock_fetch):
        """Test processing multiple matches"""
        mock_fetch.return_value = {'gameId': 12345}
        
        league.process_matches(['match1', 'match2'], 'test_token')
        
        self.assertEqual(mock_fetch.call_count, 2)
        self.assertEqual(mock_save.call_count, 2)


if __name__ == '__main__':
    unittest.main()