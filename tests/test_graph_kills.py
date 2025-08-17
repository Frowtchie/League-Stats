import unittest
from unittest.mock import patch
from typing import Any, Dict, List
import stats_visualization.visualizations.graph_kills as graph_kills


class TestGraphKills(unittest.TestCase):
    def tearDown(self):
        patch.stopall()

    def setUp(self) -> None:
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
                        "kills": 3,
                        "deaths": 1,
                        "assists": 6,
                        "championName": "OtherChamp",
                        "teamPosition": "SUPPORT",
                        "totalDamageDealtToChampions": 5000,
                        "goldEarned": 8000,
                        "win": False,
                    },
                ],
            }
        }

    def test_extract_kills_data(self) -> None:
        match_list: List[Dict[str, Any]] = [self.mock_match_data]
        with patch(
            "stats_visualization.visualizations.graph_kills.analyze.load_match_files",
            return_value=match_list,
        ):
            result = graph_kills.extract_kills_data(
                self.test_puuid,
                matches_dir="matches",
                include_aram=True,
                queue_filter=[420],
            )
            self.assertIn("total_games", result)
            self.assertIn("kills", result)
            self.assertIn("deaths", result)
            self.assertIn("assists", result)
            self.assertIn("champions", result)
            self.assertIn("wins", result)
            self.assertIn("kda_ratios", result)
            self.assertEqual(result["total_games"], 1)
            self.assertEqual(result["kills"], [5])
            self.assertEqual(result["deaths"], [2])
            self.assertEqual(result["assists"], [8])
            self.assertEqual(result["champions"], ["TestChamp"])
            self.assertEqual(result["wins"], [True])
            self.assertEqual(result["kda_ratios"], [6.5])

    def test_plot_kills_analysis(self) -> None:
        mock_data: Dict[str, Any] = {
            "total_games": 2,
            "kills": [5, 7],
            "deaths": [2, 3],
            "assists": [8, 9],
            "kda_ratios": [6.5, 5.3],
            "kill_participation": [70.0, 80.0],
            "game_dates": [None, None],
            "game_durations": [30, 25],
            "champions": ["TestChamp", "TestChamp2"],
            "wins": [True, False],
        }
        # Add all required keys for the plot function
        for key in [
            "kills",
            "deaths",
            "assists",
            "kda_ratios",
            "kill_participation",
            "game_dates",
            "game_durations",
            "champions",
            "wins",
            "total_games",
        ]:
            if key not in mock_data:
                mock_data[key] = [] if key != "total_games" else 0
        from typing import cast
        from stats_visualization.viz_types import KillsData

        typed_data = cast(KillsData, mock_data)
        with patch("matplotlib.pyplot.show") as mock_show:
            graph_kills.plot_kills_analysis("TestPlayer", typed_data)
            self.assertTrue(mock_show.called)


if __name__ == "__main__":
    unittest.main()
