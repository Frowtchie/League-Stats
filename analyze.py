#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Data analysis module for League of Legends match data.
Provides basic statistics and insights from saved match data.
"""

import json
import os
import argparse
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)


def load_match_files(matches_dir: str = "matches") -> List[Dict]:
    """
    Load all match data files from the matches directory.
    
    Args:
        matches_dir (str): Directory containing match JSON files
        
    Returns:
        List[Dict]: List of match data dictionaries
    """
    matches = []
    matches_path = Path(matches_dir)
    
    if not matches_path.exists():
        logger.warning(f"Matches directory {matches_dir} does not exist")
        return matches
    
    for file_path in matches_path.glob("*.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                match_data = json.load(f)
                matches.append(match_data)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load {file_path}: {e}")
    
    logger.info(f"Loaded {len(matches)} match files")
    return matches


def analyze_player_performance(matches: List[Dict], player_puuid: str) -> Dict[str, Any]:
    """
    Analyze performance statistics for a specific player.
    
    Args:
        matches (List[Dict]): List of match data
        player_puuid (str): PUUID of the player to analyze
        
    Returns:
        Dict[str, Any]: Performance statistics
    """
    stats = {
        'total_games': 0,
        'wins': 0,
        'losses': 0,
        'total_kills': 0,
        'total_deaths': 0,
        'total_assists': 0,
        'champions_played': Counter(),
        'roles_played': Counter(),
        'average_game_duration': 0,
        'total_damage': 0,
        'total_gold': 0
    }
    
    total_duration = 0
    
    for match in matches:
        if 'info' not in match or 'participants' not in match['info']:
            continue
            
        # Find the player's data in this match
        player_data = None
        for participant in match['info']['participants']:
            if participant.get('puuid') == player_puuid:
                player_data = participant
                break
        
        if not player_data:
            continue
            
        stats['total_games'] += 1
        
        # Basic stats
        if player_data.get('win', False):
            stats['wins'] += 1
        else:
            stats['losses'] += 1
            
        stats['total_kills'] += player_data.get('kills', 0)
        stats['total_deaths'] += player_data.get('deaths', 0)
        stats['total_assists'] += player_data.get('assists', 0)
        
        # Champion and role tracking
        champion = player_data.get('championName', 'Unknown')
        role = player_data.get('teamPosition', 'Unknown')
        stats['champions_played'][champion] += 1
        stats['roles_played'][role] += 1
        
        # Game metrics
        total_duration += match['info'].get('gameDuration', 0)
        stats['total_damage'] += player_data.get('totalDamageDealtToChampions', 0)
        stats['total_gold'] += player_data.get('goldEarned', 0)
    
    # Calculate averages
    if stats['total_games'] > 0:
        stats['win_rate'] = stats['wins'] / stats['total_games']
        stats['average_kda'] = (stats['total_kills'] + stats['total_assists']) / max(stats['total_deaths'], 1)
        stats['average_game_duration'] = total_duration / stats['total_games']
        stats['average_damage'] = stats['total_damage'] / stats['total_games']
        stats['average_gold'] = stats['total_gold'] / stats['total_games']
    
    return stats


def analyze_team_performance(matches: List[Dict]) -> Dict[str, Any]:
    """
    Analyze overall team performance metrics.
    
    Args:
        matches (List[Dict]): List of match data
        
    Returns:
        Dict[str, Any]: Team performance statistics
    """
    stats = {
        'total_matches': len(matches),
        'game_modes': Counter(),
        'game_types': Counter(),
        'average_duration': 0,
        'objectives': {
            'dragons': {'total': 0, 'avg_per_game': 0},
            'barons': {'total': 0, 'avg_per_game': 0},
            'heralds': {'total': 0, 'avg_per_game': 0},
            'towers': {'total': 0, 'avg_per_game': 0}
        }
    }
    
    total_duration = 0
    
    for match in matches:
        if 'info' not in match:
            continue
            
        info = match['info']
        
        # Game mode and type tracking
        stats['game_modes'][info.get('gameMode', 'Unknown')] += 1
        stats['game_types'][info.get('gameType', 'Unknown')] += 1
        
        # Duration tracking
        duration = info.get('gameDuration', 0)
        total_duration += duration
        
        # Objectives tracking (sum both teams)
        if 'teams' in info:
            for team in info['teams']:
                objectives = team.get('objectives', {})
                stats['objectives']['dragons']['total'] += objectives.get('dragon', {}).get('kills', 0)
                stats['objectives']['barons']['total'] += objectives.get('baron', {}).get('kills', 0)
                stats['objectives']['heralds']['total'] += objectives.get('riftHerald', {}).get('kills', 0)
                stats['objectives']['towers']['total'] += objectives.get('tower', {}).get('kills', 0)
    
    # Calculate averages
    if stats['total_matches'] > 0:
        stats['average_duration'] = total_duration / stats['total_matches']
        for obj_type in stats['objectives']:
            stats['objectives'][obj_type]['avg_per_game'] = (
                stats['objectives'][obj_type]['total'] / stats['total_matches']
            )
    
    return stats


def print_player_report(stats: Dict[str, Any], player_name: str):
    """Print a formatted player performance report."""
    print(f"\n{'='*50}")
    print(f"PLAYER PERFORMANCE REPORT: {player_name}")
    print(f"{'='*50}")
    
    print(f"\n📊 Overall Performance:")
    print(f"   Total Games: {stats['total_games']}")
    print(f"   Wins: {stats['wins']} | Losses: {stats['losses']}")
    print(f"   Win Rate: {stats.get('win_rate', 0):.1%}")
    
    print(f"\n⚔️ Combat Stats:")
    print(f"   Total K/D/A: {stats['total_kills']}/{stats['total_deaths']}/{stats['total_assists']}")
    print(f"   Average KDA: {stats.get('average_kda', 0):.2f}")
    
    print(f"\n🏆 Champions (Top 5):")
    for champion, count in stats['champions_played'].most_common(5):
        print(f"   {champion}: {count} games")
    
    print(f"\n🎯 Preferred Roles:")
    for role, count in stats['roles_played'].most_common():
        print(f"   {role}: {count} games")
    
    print(f"\n💰 Performance Metrics:")
    print(f"   Average Damage: {stats.get('average_damage', 0):,.0f}")
    print(f"   Average Gold: {stats.get('average_gold', 0):,.0f}")
    print(f"   Average Game Duration: {stats.get('average_game_duration', 0)//60:.0f}m {stats.get('average_game_duration', 0)%60:.0f}s")


def print_team_report(stats: Dict[str, Any]):
    """Print a formatted team performance report."""
    print(f"\n{'='*50}")
    print(f"TEAM PERFORMANCE ANALYSIS")
    print(f"{'='*50}")
    
    print(f"\n📈 Match Overview:")
    print(f"   Total Matches Analyzed: {stats['total_matches']}")
    print(f"   Average Game Duration: {stats['average_duration']//60:.0f}m {stats['average_duration']%60:.0f}s")
    
    print(f"\n🎮 Game Modes:")
    for mode, count in stats['game_modes'].most_common():
        print(f"   {mode}: {count} matches")
    
    print(f"\n🏹 Objectives Per Game (Average):")
    for obj_type, data in stats['objectives'].items():
        print(f"   {obj_type.title()}: {data['avg_per_game']:.1f}")


def main():
    """Main function for data analysis."""
    parser = argparse.ArgumentParser(description="Analyze League of Legends match data")
    parser.add_argument("--player", type=str, help="Player name to analyze (must exist in config)")
    parser.add_argument("--matches-dir", type=str, default="matches", 
                       help="Directory containing match JSON files")
    parser.add_argument("--team-analysis", action="store_true",
                       help="Show team-wide analysis instead of player-specific")
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Load matches
    matches = load_match_files(args.matches_dir)
    
    if not matches:
        print("No match data found. Run league.py first to fetch some matches.")
        return
    
    if args.team_analysis:
        # Team analysis
        team_stats = analyze_team_performance(matches)
        print_team_report(team_stats)
    else:
        # Player analysis
        if not args.player:
            print("Please specify a player name with --player")
            return
            
        # Load player config to get PUUID
        import sys
        sys.path.append('.')
        import league
        
        puuids = league.load_player_config()
        if args.player not in puuids:
            available_players = ", ".join(puuids.keys())
            print(f"Player '{args.player}' not found. Available: {available_players}")
            return
            
        player_puuid = puuids[args.player]
        player_stats = analyze_player_performance(matches, player_puuid)
        
        if player_stats['total_games'] == 0:
            print(f"No matches found for player {args.player}")
            return
            
        print_player_report(player_stats, args.player)


if __name__ == "__main__":
    main()