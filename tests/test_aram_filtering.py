import unittest
import sys
import os
from unittest.mock import patch
from typing import Any, Dict

# Add visualization scripts and project root to path
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "stats_visualization", "visualizations"
    ),
)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestAramFiltering(unittest.TestCase):
    def setUp(self) -> None:
        # Summoner's Rift match
        self.sr_match = {
            "info": {
                "gameMode": "CLASSIC",
                "participants": [{"puuid": "player_puuid", "teamId": 100, "win": True}],
                "teams": [
                    {"teamId": 100, "objectives": {"dragon": {"kills": 2}}},
                    {"teamId": 200, "objectives": {"dragon": {"kills": 1}}},
                ],
            }
        }
        # ARAM match (should be excluded by default)
        self.aram_match = {
            "info": {
                "gameMode": "ARAM",
                "participants": [
                    {"puuid": "player_puuid", "teamId": 100, "win": False}
                ],
                "teams": [
                    {"teamId": 100, "objectives": {"dragon": {"kills": 5}}},
                    {"teamId": 200, "objectives": {"dragon": {"kills": 0}}},
                ],
            }
        }

    @patch("graph_drakes.analyze.load_match_files")
    def test_drake_excludes_aram_by_default(self, mock_load):
        from graph_drakes import extract_drake_data

        mock_load.return_value = [self.sr_match, self.aram_match]
        data = extract_drake_data("player_puuid")
        self.assertEqual(data["total_games"], 1)
        self.assertEqual(data["player_team_drakes"], [2])

    @patch("graph_drakes.analyze.load_match_files")
    def test_drake_includes_aram_with_flag(self, mock_load):
        from graph_drakes import extract_drake_data

        mock_load.return_value = [self.sr_match, self.aram_match]
        data = extract_drake_data("player_puuid", include_aram=True)
        self.assertEqual(data["total_games"], 2)
        self.assertEqual(data["player_team_drakes"], [2, 5])


if __name__ == "__main__":
    unittest.main()
