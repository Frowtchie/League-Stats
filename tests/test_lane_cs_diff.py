from typing import Any, Dict, List

import pytest

from stats_visualization.visualizations.lane_cs_diff import (
    extract_lane_cs_diff_data,
    _infer_opponent,  # noqa: PLC2701 (accessing internal for targeted unit test)
)


@pytest.fixture
def mock_matches(monkeypatch: pytest.MonkeyPatch) -> List[Dict[str, Any]]:
    """Provide three synthetic matches (two usable, one missing opponent)."""

    def frame(
        ts: int,
        player_pid: int,
        opp_pid: int,
        p_cs: int,
        p_xp: int,
        p_gold: int,
        o_cs: int,
        o_xp: int,
        o_gold: int,
    ) -> Dict[str, Any]:
        return {
            "timestamp": ts,
            "participantFrames": {
                str(player_pid): {
                    "participantId": player_pid,
                    "minionsKilled": p_cs // 2,
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

    def build_match(
        game_creation: int,
        player_pid: int,
        opp_pid: int,
        player_cs10: int,
        player_cs15: int,
        opp_cs10: int,
        opp_cs15: int,
    ) -> Dict[str, Any]:
        timeline: Dict[str, Any] = {
            "info": {
                "frames": [
                    frame(
                        600_000 - 5_000,
                        player_pid,
                        opp_pid,
                        player_cs10 - 2,
                        2000,
                        2000,
                        opp_cs10 - 2,
                        1900,
                        1950,
                    ),
                    frame(
                        600_000 + 2_000,
                        player_pid,
                        opp_pid,
                        player_cs10,
                        2050,
                        2100,
                        opp_cs10,
                        1950,
                        2050,
                    ),
                    frame(
                        900_000 - 3_000,
                        player_pid,
                        opp_pid,
                        player_cs15 - 3,
                        3500,
                        3200,
                        opp_cs15 - 3,
                        3300,
                        3100,
                    ),
                    frame(
                        900_000 + 1_500,
                        player_pid,
                        opp_pid,
                        player_cs15,
                        3600,
                        3400,
                        opp_cs15,
                        3400,
                        3300,
                    ),
                ]
            }
        }
        return {
            "info": {
                "gameCreation": game_creation,
                "participants": [
                    {
                        "puuid": "player",
                        "teamId": 100,
                        "teamPosition": "TOP",
                        "participantId": player_pid,
                    },
                    {
                        "puuid": f"opp{game_creation}",
                        "teamId": 200,
                        "teamPosition": "TOP",
                        "participantId": opp_pid,
                    },
                ],
            },
            "timeline": timeline,
        }

    matches: List[Dict[str, Any]] = [
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

    def _load(_dir: str = "matches") -> List[Dict[str, Any]]:
        return matches

    monkeypatch.setattr("stats_visualization.analyze.load_match_files", _load)
    return matches


def test_infer_opponent() -> None:
    player: Dict[str, Any] = {"teamId": 100, "teamPosition": "MIDDLE"}
    participants: List[Dict[str, Any]] = [
        player,
        {"teamId": 200, "teamPosition": "MIDDLE", "puuid": "enemy"},
    ]
    opp = _infer_opponent(player, participants)
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
    def _load_empty(*_args: Any, **_kw: Any) -> List[Dict[str, Any]]:
        return [
            {
                "info": {
                    "gameCreation": 1,
                    "participants": [{"puuid": "player", "teamId": 100, "teamPosition": "TOP"}],
                }
            }
        ]

    monkeypatch.setattr("stats_visualization.analyze.load_match_files", _load_empty)
    data = extract_lane_cs_diff_data("player")
    assert data["match_indices"] == []
    assert data["opponent_missing"] == 1
    assert data["total_considered"] == 1
