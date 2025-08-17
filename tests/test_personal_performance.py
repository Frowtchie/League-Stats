import matplotlib
import unittest
from unittest.mock import patch
from typing import Any, Dict, List
from stats_visualization.visualizations import personal_performance

matplotlib.use("Agg")


class TestPersonalPerformance(unittest.TestCase):
    def tearDown(self):
        patch.stopall()

    def setUp(self) -> None:
        # Mock match data with all required fields and types
        self.test_puuid: str = "player_puuid"
        self.mock_match_data: Dict[str, Any] = {
            "info": {
                "gameMode": "CLASSIC",
                "queueId": 420,
                "gameCreation": 1700000000000,
                "gameDuration": 1800,
                "participants": [
                    {
                        "puuid": self.test_puuid,
                        "teamId": 100,
                        "kills": 5,
                        "deaths": 2,
                        "assists": 8,
                        "championName": "TestChamp",
                        "teamPosition": "ADC",
                        "totalDamageDealtToChampions": 25000,
                        "goldEarned": 15000,
                        "win": True,
                    },
                    {
                        "puuid": "other_puuid",
                        "teamId": 200,
                        "kills": 2,
                        "deaths": 5,
                        "assists": 3,
                        "championName": "OtherChamp",
                        "teamPosition": "SUPPORT",
                        "totalDamageDealtToChampions": 5000,
                        "goldEarned": 8000,
                        "win": False,
                    },
                ],
            }
        }

    def test_load_player_match_data(self) -> None:
        with patch(
            "stats_visualization.visualizations.personal_performance.analyze.load_match_files"
        ) as mock_load_matches:
            mock_load_matches.return_value = [self.mock_match_data]
            result = personal_performance.load_player_match_data(self.test_puuid)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0], self.mock_match_data)

    def test_plot_performance_trends(self) -> None:
        # Provide at least one match with correct puuid to trigger plotting
        with patch(
            "stats_visualization.visualizations.personal_performance.load_player_match_data"
        ) as mock_load_data, patch("matplotlib.pyplot.show") as mock_show:
            mock_load_data.return_value = [self.mock_match_data]
            print(
                "[TEST DEBUG] plot_performance_trends mock_data:",
                [self.mock_match_data],
            )
            personal_performance.plot_performance_trends(self.test_puuid, "TestPlayer")
            print(
                "[TEST DEBUG] plot_performance_trends mock_show.called:",
                mock_show.called,
            )
            self.assertTrue(mock_show.called)

    def test_plot_champion_performance(self) -> None:
        # Provide at least two matches with correct puuid and same champion
        import copy

        match1: Dict[str, Any] = copy.deepcopy(self.mock_match_data)
        match2: Dict[str, Any] = copy.deepcopy(self.mock_match_data)
        mock_data: List[Dict[str, Any]] = [match1, match2]
        with patch(
            "stats_visualization.visualizations.personal_performance.load_player_match_data"
        ) as mock_load_data, patch("matplotlib.pyplot.show") as mock_show:
            mock_load_data.return_value = mock_data
            print("[TEST DEBUG] plot_champion_performance mock_data:", mock_data)
            personal_performance.plot_champion_performance(self.test_puuid, "TestPlayer")
            print(
                "[TEST DEBUG] plot_champion_performance mock_show.called:",
                mock_show.called,
            )
            self.assertTrue(mock_show.called)


if __name__ == "__main__":
    unittest.main()
