from typing import Any, Dict, List

import pytest

from stats_visualization.visualizations.lane_cs_diff import (
    extract_lane_cs_diff_data,
    _infer_opponent,  # type: ignore
)


@pytest.fixture
def mock_matches(monkeypatch: pytest.MonkeyPatch) -> List[Dict[str, Any]]:
    # Two matches with opponent, one missing opponent
    def build_match(game_creation: int, player_pid: int, opp_pid: int, player_cs10: int, player_cs15: int, opp_cs10: int, opp_cs15: int):  # type: ignore[return-type]
        # Minimal root timeline with frames near 10 and 15 minutes (600k ms, 900k ms)
        def frame(ts: int, p_cs: int, p_xp: int, p_gold: int, o_cs: int, o_xp: int, o_gold: int):  # type: ignore[return-type]
            return {
                "timestamp": ts,
                "participantFrames": {
                    str(player_pid): {
                        "participantId": player_pid,
                        "minionsKilled": p_cs // 2,  # split to test sum logic
                        "jungleMinionsKilled": p_cs - p_cs // 2,
                        "xp": p_xp,
                        "totalGold": p_gold,
                    },
                    str(opp_pid): {
                        "participantId": opp_pid,
                        "minionsKilled": o_cs // 2,
                        "jungleMinionsKilled": o_cs - o_cs // 2,
                        "xp": o_xp,
                        "totalGold": o_gold,
                    },
                },
            }
        # Provide two frames each side of target times to ensure closest selection
        timeline = {  # type: ignore[var-annotated]
            "info": {
                "frames": [
                    frame(600_000 - 5_000, player_cs10 - 2, 2000, 2000, opp_cs10 - 2, 1900, 1950),
                    frame(600_000 + 2_000, player_cs10, 2050, 2100, opp_cs10, 1950, 2050),
                    frame(900_000 - 3_000, player_cs15 - 3, 3500, 3200, opp_cs15 - 3, 3300, 3100),
                    frame(900_000 + 1_500, player_cs15, 3600, 3400, opp_cs15, 3400, 3300),
                ]
            }
        }
        return {  # type: ignore[return-value]
            "info": {
                "gameCreation": game_creation,
                "participants": [
                    {"puuid": "player", "teamId": 100, "teamPosition": "TOP", "participantId": player_pid},
                    {"puuid": f"opp{game_creation}", "teamId": 200, "teamPosition": "TOP", "participantId": opp_pid},
                ],
            },
            "timeline": timeline,
        }

    matches: List[Dict[str, Any]] = [  # type: ignore[assignment]
        build_match(2, 1, 2, 70, 110, 60, 100),
        build_match(3, 1, 2, 65, 105, 70, 115),
        {  # missing opponent
            "info": {
                "gameCreation": 1,
                "participants": [
                    {"puuid": "player", "teamId": 100, "teamPosition": "TOP", "participantId": 3},
                ],
            },
            "timeline": {"info": {"frames": []}},
        },
    ]

    def _load(_dir: str = "matches") -> List[Dict[str, Any]]:  # type: ignore[return-type]
        return matches  # type: ignore[return-value]

    monkeypatch.setattr("stats_visualization.analyze.load_match_files", _load)  # type: ignore[arg-type]
    return matches  # type: ignore[return-value]


def test_infer_opponent() -> None:
    player: Dict[str, Any] = {"teamId": 100, "teamPosition": "MIDDLE"}
    participants: List[Dict[str, Any]] = [
        player,
        {"teamId": 200, "teamPosition": "MIDDLE", "puuid": "enemy"},
    ]
    opp = _infer_opponent(player, participants)  # type: ignore[arg-type]
    assert opp and opp.get("puuid") == "enemy"


def test_extract_lane_cs_diff_data(mock_matches: List[Dict[str, Any]]) -> None:
    data = extract_lane_cs_diff_data("player")
    # Sorted by gameCreation: matchCreation 1 (skipped), 2, 3 -> indices 1,2
    assert data["match_indices"] == [1, 2]
    assert data["cs10"] == [70, 65]
    assert data["diff10"] == [10, -5]
    assert data["xp10"] and len(data["xp10"]) == 2
    assert data["gold10"] and len(data["gold10"]) == 2
    # Only one skipped due to missing opponent (the earliest match)
    assert data["opponent_missing"] == 1
    assert data["total_considered"] == 3


def test_extract_lane_cs_diff_data_missing_all(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "stats_visualization.analyze.load_match_files",
        lambda *_: [  # type: ignore[return-value]
            {"info": {"gameCreation": 1, "participants": [{"puuid": "player", "teamId": 100, "teamPosition": "TOP"}]}}
        ],
    )
    data = extract_lane_cs_diff_data("player")
    assert data["match_indices"] == []
    assert data["opponent_missing"] == 1
    assert data["total_considered"] == 1
