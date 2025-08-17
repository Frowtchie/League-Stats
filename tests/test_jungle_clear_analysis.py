import unittest
import sys
import os
from unittest.mock import patch
from typing import Any, Dict

# Add the stats_visualization directory to the path
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "stats_visualization", "visualizations"),
)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestJungleClearAnalysis(unittest.TestCase):
    def setUp(self) -> None:
        # Mock match data with jungle player
        self.mock_jungle_match = {
            "info": {
                "gameCreation": 1640995200000,
                "gameDuration": 1800,  # 30 minutes
                "participants": [
                    {
                        "puuid": "test_puuid",
                        "participantId": 1,
                        "teamId": 100,
                        "teamPosition": "JUNGLE",
                        "championName": "Graves",
                        "kills": 6,
                        "deaths": 2,
                        "assists": 8,
                        "totalMinionsKilled": 45,
                        "neutralMinionsKilled": 120,
                        "win": True,
                    }
                ],
            },
            "timeline": {
                "frames": [
                    {
                        "timestamp": 120000,  # 2 minutes
                        "events": [
                            {
                                "type": "ELITE_MONSTER_KILL",
                                "timestamp": 120000,
                                "killerId": 1,
                                "monsterType": "BLUE_GOLEM",
                            }
                        ],
                    },
                    {
                        "timestamp": 180000,  # 3 minutes
                        "events": [
                            {
                                "type": "NEUTRAL_MONSTER_KILL",
                                "timestamp": 180000,
                                "killerId": 1,
                                "monsterType": "GROMP",
                            },
                            {
                                "type": "NEUTRAL_MONSTER_KILL",
                                "timestamp": 195000,  # 3.25 minutes
                                "killerId": 1,
                                "monsterType": "RAPTOR",
                            },
                            {
                                "type": "ELITE_MONSTER_KILL",
                                "timestamp": 210000,  # 3.5 minutes
                                "killerId": 1,
                                "monsterType": "RED_LIZARD",
                            },
                        ],
                    },
                ]
            },
        }

        # Mock match data for non-jungle player
        self.mock_non_jungle_match = {
            "info": {
                "gameCreation": 1640995200000,
                "gameDuration": 1800,
                "participants": [
                    {
                        "puuid": "test_puuid",
                        "participantId": 1,
                        "teamId": 100,
                        "teamPosition": "BOT",
                        "championName": "Jinx",
                        "kills": 8,
                        "deaths": 3,
                        "assists": 5,
                        "totalMinionsKilled": 180,
                        "neutralMinionsKilled": 10,
                        "win": False,
                    }
                ],
            }
        }

    @patch("stats_visualization.visualizations.jungle_clear_analysis.analyze.load_match_files")
    def test_extract_jungle_clear_data_jungle_game(self, mock_load_matches):
        from jungle_clear_analysis import extract_jungle_clear_data

        mock_load_matches.return_value = [self.mock_jungle_match]

        result = extract_jungle_clear_data("test_puuid")

        self.assertEqual(result["total_games"], 1)
        self.assertEqual(result["jungle_games"], 1)
        self.assertEqual(len(result["first_clear_times"]), 1)
        self.assertEqual(result["champions"], ["Graves"])
        self.assertEqual(result["wins"], [True])

        # Check that clear time was calculated
        self.assertGreater(result["first_clear_times"][0], 0)

    @patch("stats_visualization.visualizations.jungle_clear_analysis.analyze.load_match_files")
    def test_extract_jungle_clear_data_non_jungle_game(self, mock_load_matches):
        from jungle_clear_analysis import extract_jungle_clear_data

        mock_load_matches.return_value = [self.mock_non_jungle_match]

        result = extract_jungle_clear_data("test_puuid")

        self.assertEqual(result["total_games"], 1)
        self.assertEqual(result["jungle_games"], 0)
        self.assertEqual(len(result["first_clear_times"]), 0)

    def test_calculate_clear_time_from_timeline(self):
        from jungle_clear_analysis import calculate_clear_time_from_timeline

        timeline = self.mock_jungle_match["timeline"]
        player_data = self.mock_jungle_match["info"]["participants"][0]

        clear_time = calculate_clear_time_from_timeline(timeline, player_data)

        # Should return the timestamp of the 4th jungle monster kill (3.0 minutes)
        self.assertIsNotNone(clear_time)
        self.assertAlmostEqual(clear_time, 3.0, places=1)

    def test_estimate_clear_time_from_stats_fast_clearer(self):
        from jungle_clear_analysis import estimate_clear_time_from_stats

        player_data = {
            "championName": "Graves",
            "neutralMinionsKilled": 120,
            "totalMinionsKilled": 180,
        }

        clear_time = estimate_clear_time_from_stats(player_data)

        self.assertIsNotNone(clear_time)
        self.assertLess(clear_time, 3.5)  # Fast clearer should be under 3.5 minutes

    def test_estimate_clear_time_from_stats_low_cs(self):
        from jungle_clear_analysis import estimate_clear_time_from_stats

        player_data = {
            "championName": "Graves",
            "neutralMinionsKilled": 5,  # Very low
            "totalMinionsKilled": 20,
        }

        clear_time = estimate_clear_time_from_stats(player_data)

        # Should return None for very low CS (likely not proper jungling)
        self.assertIsNone(clear_time)

    @patch("stats_visualization.visualizations.jungle_clear_analysis.analyze.load_match_files")
    @patch("matplotlib.pyplot.show")
    @patch("matplotlib.pyplot.savefig")
    def test_plot_jungle_clear_analysis_with_data(self, mock_savefig, mock_show, mock_load_matches):
        from jungle_clear_analysis import (
            plot_jungle_clear_analysis,
            extract_jungle_clear_data,
        )

        mock_load_matches.return_value = [self.mock_jungle_match]

        jungle_data = extract_jungle_clear_data("test_puuid")

        # Should not raise an exception
        plot_jungle_clear_analysis("TestPlayer", jungle_data)

        # Verify that savefig was called (plot was generated)
        mock_savefig.assert_called_once()

    @patch("stats_visualization.visualizations.jungle_clear_analysis.analyze.load_match_files")
    @patch("builtins.print")
    def test_plot_jungle_clear_analysis_no_jungle_games(self, mock_print, mock_load_matches):
        from jungle_clear_analysis import (
            plot_jungle_clear_analysis,
            extract_jungle_clear_data,
        )

        mock_load_matches.return_value = [self.mock_non_jungle_match]

        jungle_data = extract_jungle_clear_data("test_puuid")

        # Should print message about no jungle games
        plot_jungle_clear_analysis("TestPlayer", jungle_data)

        mock_print.assert_called_with("No jungle games found for TestPlayer")

    @patch("jungle_clear_analysis.plot_jungle_clear_analysis")
    @patch(
        "stats_visualization.visualizations.jungle_clear_analysis.league.ensure_matches_for_player"
    )
    @patch("stats_visualization.visualizations.jungle_clear_analysis.league.fetch_puuid_by_riot_id")
    @patch("stats_visualization.visualizations.jungle_clear_analysis.league.load_player_config")
    @patch("stats_visualization.visualizations.jungle_clear_analysis.analyze.load_match_files")
    def test_main_function_success(
        self,
        mock_load_matches,
        mock_config,
        mock_fetch_puuid,
        mock_ensure_matches,
        mock_plot,
    ):
        from jungle_clear_analysis import main
        import sys
        import os

        # Mock configuration and environment
        mock_config.return_value = {"TestPlayer": "test_puuid"}
        mock_load_matches.return_value = [self.mock_jungle_match]
        mock_ensure_matches.return_value = 1
        mock_fetch_puuid.return_value = "test_puuid"
        os.environ["RIOT_API_TOKEN"] = "dummy_token"

        # Mock command line arguments to use game_name and tag_line
        original_argv = sys.argv
        sys.argv = ["jungle_clear_analysis.py", "TestPlayer", "EUW"]

        try:
            main()
            mock_plot.assert_called_once()
        finally:
            sys.argv = original_argv
        # Clean up environment variable
        del os.environ["RIOT_API_TOKEN"]

    @patch("stats_visualization.visualizations.jungle_clear_analysis.league.load_player_config")
    @patch("stats_visualization.visualizations.jungle_clear_analysis.analyze.load_match_files")
    @patch("stats_visualization.visualizations.jungle_clear_analysis.plot_jungle_clear_analysis")
    @patch(
        "stats_visualization.visualizations.jungle_clear_analysis.league.ensure_matches_for_player"
    )
    @patch("stats_visualization.visualizations.jungle_clear_analysis.league.fetch_puuid_by_riot_id")
    @patch("builtins.print")
    def test_main_function_no_matches(
        self,
        mock_print,
        mock_fetch_puuid,
        mock_ensure_matches,
        mock_plot,
        mock_load_matches,
        mock_config,
    ):
        from jungle_clear_analysis import main
        import sys
        import os

        # Mock configuration and environment
        mock_config.return_value = {"TestPlayer": "test_puuid"}
        mock_load_matches.return_value = [self.mock_jungle_match]
        mock_ensure_matches.return_value = 0  # Simulate no matches found
        mock_fetch_puuid.return_value = "test_puuid"
        os.environ["RIOT_API_TOKEN"] = "dummy_token"

        # Mock command line arguments to use game_name and tag_line
        original_argv = sys.argv
        sys.argv = ["jungle_clear_analysis.py", "TestPlayer", "EUW"]

        try:
            main()
            mock_plot.assert_not_called()
            mock_print.assert_any_call("Failed to fetch or find any matches for TestPlayer#EUW.")
        finally:
            sys.argv = original_argv
            del os.environ["RIOT_API_TOKEN"]


if __name__ == "__main__":
    unittest.main()
