"""Shared TypedDict data structures for visualization modules.

Renamed from `types.py` to avoid shadowing the Python stdlib module
`types`, which is imported by `typing`. The shadowing caused runtime
ImportError when running scripts directly.
"""

from __future__ import annotations

from typing import List, TypedDict, Dict
import datetime as _dt


class ObjectiveBreakdown(TypedDict):
    player_team: List[int]
    enemy_team: List[int]
    wins: List[bool]
    types: List[str]


class ObjectiveData(TypedDict):
    dragons: ObjectiveBreakdown
    barons: ObjectiveBreakdown
    heralds: ObjectiveBreakdown
    towers: ObjectiveBreakdown
    first_objectives: Dict[str, int]
    total_games: int


class EarlyGameData(TypedDict):
    first_blood_kills: int
    first_blood_deaths: int
    first_blood_assists: int
    first_tower_kills: int
    early_kills: List[int]
    early_deaths: List[int]
    early_cs: List[int]
    wins: List[bool]
    champions: List[str]
    roles: List[str]
    total_games: int


class BaronHeraldData(TypedDict):
    player_team_barons: List[int]
    enemy_team_barons: List[int]
    player_team_heralds: List[int]
    enemy_team_heralds: List[int]
    wins: List[bool]
    game_durations: List[float]
    total_games: int


class DrakeData(TypedDict):
    player_team_drakes: List[int]
    enemy_team_drakes: List[int]
    wins: List[bool]
    game_durations: List[float]
    total_games: int


class EconomyData(TypedDict):
    cs_per_min: List[float]
    gold_per_min: List[float]
    damage_per_gold: List[float]
    vision_score: List[int]
    game_durations: List[float]
    total_cs: List[int]
    total_gold: List[int]
    total_damage: List[int]
    roles: List[str]
    champions: List[str]
    wins: List[bool]
    items_purchased: List[int]
    total_games: int


class JungleData(TypedDict):
    first_clear_times: List[float]
    champions: List[str]
    wins: List[bool]
    game_durations: List[float]
    clear_efficiency: List[float]
    total_games: int
    jungle_games: int


class KillsData(TypedDict):
    kills: List[int]
    deaths: List[int]
    assists: List[int]
    kda_ratios: List[float]
    kill_participation: List[float]
    game_dates: List[_dt.datetime]
    game_durations: List[float]
    champions: List[str]
    wins: List[bool]
    total_games: int


class ChampionStats(TypedDict):
    kills: List[int]
    deaths: List[int]
    assists: List[int]
    kda: List[float]
    games: int
