import unittest
from unittest.mock import patch
from typing import Any, Dict, List
import stats_visualization.visualizations.graph_drakes as graph_drakes


class TestGraphDrakes(unittest.TestCase):
    def tearDown(self):
        patch.stopall()

    def setUp(self) -> None:
        # Use a consistent test PUUID
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
                "teams": [
                    {"teamId": 100, "objectives": {"dragon": {"kills": 3}}},
                    {"teamId": 200, "objectives": {"dragon": {"kills": 1}}},
                ],
            }
        }

    def test_extract_drake_data(self) -> None:
        match_list: List[Dict[str, Any]] = [self.mock_match_data]
        # Patch load_match_files within the scope of this test so match_list is defined
        with patch(
            "stats_visualization.visualizations.graph_drakes.analyze.load_match_files",
            return_value=match_list,
        ):
            result = graph_drakes.extract_drake_data(
                self.test_puuid,
                matches_dir="matches",
                include_aram=True,
                queue_filter=[420],
            )
            self.assertIn("total_games", result)
            self.assertIn("player_team_drakes", result)
            self.assertIn("enemy_team_drakes", result)
            self.assertIn("wins", result)
            self.assertEqual(result["total_games"], 1)
            self.assertEqual(result["player_team_drakes"], [3])
            self.assertEqual(result["enemy_team_drakes"], [1])
            self.assertEqual(result["wins"], [True])

    def test_plot_drake_analysis(self) -> None:
        # Provide mock data with at least one game to trigger plotting
        mock_data: Dict[str, Any] = {
            "total_games": 2,
            "player_team_drakes": [3, 2],
            "enemy_team_drakes": [1, 2],
            "wins": [True, False],
            "game_durations": [30, 25],
        }
        # Add all required keys for the plot function
        for key in [
            "player_team_drakes",
            "enemy_team_drakes",
            "wins",
            "game_durations",
            "total_games",
        ]:
            if key not in mock_data:
                mock_data[key] = [] if key != "total_games" else 0
        from typing import cast
        from stats_visualization.viz_types import DrakeData

        typed_data = cast(DrakeData, mock_data)
        with patch("matplotlib.pyplot.show") as mock_show:
            graph_drakes.plot_drake_analysis("TestPlayer", typed_data)
            self.assertTrue(mock_show.called)


if __name__ == "__main__":
    unittest.main()
