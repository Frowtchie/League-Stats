import unittest
import sys
import os
from unittest.mock import patch

# Add visualization scripts and project root to path
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "stats_visualization", "visualizations"),
)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestQueueFiltering(unittest.TestCase):
    def setUp(self) -> None:
        # Ranked Solo (420)
        self.ranked_solo_match = {
            "info": {
                "gameMode": "CLASSIC",
                "queueId": 420,
                "gameCreation": 1700000000000,
                "participants": [
                    {
                        "puuid": "player_puuid",
                        "teamId": 100,
                        "kills": 5,
                        "deaths": 2,
                        "assists": 3,
                        "win": True,
                    }
                ],
            }
        }
        # Normal Draft (430)
        self.normal_draft_match = {
            "info": {
                "gameMode": "CLASSIC",
                "queueId": 430,
                "gameCreation": 1700001000000,
                "participants": [
                    {
                        "puuid": "player_puuid",
                        "teamId": 100,
                        "kills": 2,
                        "deaths": 5,
                        "assists": 1,
                        "win": False,
                    }
                ],
            }
        }

    @patch("graph_kills.analyze.load_match_files")
    def test_queue_filter_includes_only_specified_ids(self, mock_load):
        from graph_kills import extract_kills_data

        mock_load.return_value = [self.ranked_solo_match, self.normal_draft_match]
        data = extract_kills_data("player_puuid", queue_filter=[420])
        self.assertEqual(data["total_games"], 1)
        self.assertEqual(len(data["kills"]), 1)
        self.assertEqual(data["kills"][0], 5)

    @patch("graph_kills.analyze.load_match_files")
    def test_ranked_only_shortcut(self, mock_load):
        from graph_kills import extract_kills_data

        mock_load.return_value = [self.ranked_solo_match, self.normal_draft_match]
        # Simulate ranked-only by passing both solo/flex queue IDs
        data = extract_kills_data("player_puuid", queue_filter=[420, 440])
        # Only solo matches present matching the filter
        self.assertEqual(data["total_games"], 1)


if __name__ == "__main__":
    unittest.main()
