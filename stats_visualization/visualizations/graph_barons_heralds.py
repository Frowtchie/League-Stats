#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Personal baron and herald statistics visualization for League of Legends match data.
Analyzes baron and rift herald control from personal match history.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
import argparse
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
import league
import analyze


def extract_baron_herald_data(player_puuid: str, matches_dir: str = "matches") -> Dict[str, Any]:
    """
    Extract baron and herald data for a specific player from match history.
    
    Args:
        player_puuid (str): PUUID of the player
        matches_dir (str): Directory containing match JSON files
        
    Returns:
        Dict containing baron and herald statistics
    """
    matches = analyze.load_match_files(matches_dir)
    objective_data = {
        'player_team_barons': [],
        'enemy_team_barons': [],
        'player_team_heralds': [],
        'enemy_team_heralds': [],
        'wins': [],
        'game_durations': [],
        'total_games': 0
    }
    
    for match in matches:
        if 'info' not in match or 'participants' not in match['info']:
            continue
            
        # Find player's team ID
        player_team_id = None
        player_won = False
        
        for participant in match['info']['participants']:
            if participant.get('puuid') == player_puuid:
                player_team_id = participant.get('teamId')
                player_won = participant.get('win', False)
                break
                
        if player_team_id is None:
            continue
            
        objective_data['total_games'] += 1
        game_duration = match['info'].get('gameDuration', 0)
        objective_data['game_durations'].append(game_duration / 60)  # Convert to minutes
        objective_data['wins'].append(player_won)
        
        # Extract team objective counts
        if 'teams' in match['info']:
            player_barons = 0
            enemy_barons = 0
            player_heralds = 0
            enemy_heralds = 0
            
            for team in match['info']['teams']:
                objectives = team.get('objectives', {})
                baron_kills = objectives.get('baron', {}).get('kills', 0)
                herald_kills = objectives.get('riftHerald', {}).get('kills', 0)
                
                if team['teamId'] == player_team_id:
                    player_barons = baron_kills
                    player_heralds = herald_kills
                else:
                    enemy_barons = baron_kills
                    enemy_heralds = herald_kills
            
            objective_data['player_team_barons'].append(player_barons)
            objective_data['enemy_team_barons'].append(enemy_barons)
            objective_data['player_team_heralds'].append(player_heralds)
            objective_data['enemy_team_heralds'].append(enemy_heralds)
    
    return objective_data


def plot_baron_herald_analysis(player_name: str, objective_data: Dict[str, Any]):
    """
    Create comprehensive baron and herald analysis visualization.
    """
    if objective_data['total_games'] == 0:
        print(f"No games found for {player_name}")
        return
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # Average objectives comparison
    avg_player_barons = np.mean(objective_data['player_team_barons'])
    avg_enemy_barons = np.mean(objective_data['enemy_team_barons'])
    avg_player_heralds = np.mean(objective_data['player_team_heralds'])
    avg_enemy_heralds = np.mean(objective_data['enemy_team_heralds'])
    
    objectives = ['Barons', 'Heralds']
    player_avg = [avg_player_barons, avg_player_heralds]
    enemy_avg = [avg_enemy_barons, avg_enemy_heralds]
    
    x = np.arange(len(objectives))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, player_avg, width, label='Player Team', color='lightblue', alpha=0.7)
    bars2 = ax1.bar(x + width/2, enemy_avg, width, label='Enemy Team', color='lightcoral', alpha=0.7)
    
    ax1.set_ylabel('Average per Game')
    ax1.set_title(f'{player_name} - Baron & Herald Control Comparison')
    ax1.set_xticks(x)
    ax1.set_xticklabels(objectives)
    ax1.legend()
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{height:.2f}', ha='center', va='bottom')
    
    # Baron control distribution
    baron_diff = [p - e for p, e in zip(objective_data['player_team_barons'], 
                                       objective_data['enemy_team_barons'])]
    ax2.hist(baron_diff, bins=range(-4, 5), alpha=0.7, color='purple', edgecolor='black')
    ax2.axvline(0, color='red', linestyle='--', label='Even Baron Control')
    ax2.set_xlabel('Baron Advantage (Player Team - Enemy Team)')
    ax2.set_ylabel('Number of Games')
    ax2.set_title(f'{player_name} - Baron Control Distribution')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Herald control distribution
    herald_diff = [p - e for p, e in zip(objective_data['player_team_heralds'], 
                                        objective_data['enemy_team_heralds'])]
    ax3.hist(herald_diff, bins=range(-3, 4), alpha=0.7, color='orange', edgecolor='black')
    ax3.axvline(0, color='red', linestyle='--', label='Even Herald Control')
    ax3.set_xlabel('Herald Advantage (Player Team - Enemy Team)')
    ax3.set_ylabel('Number of Games')
    ax3.set_title(f'{player_name} - Herald Control Distribution')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Win rate correlation with major objectives
    # Calculate total major objectives (barons + heralds)
    player_total_obj = [b + h for b, h in zip(objective_data['player_team_barons'], 
                                             objective_data['player_team_heralds'])]
    enemy_total_obj = [b + h for b, h in zip(objective_data['enemy_team_barons'], 
                                           objective_data['enemy_team_heralds'])]
    
    win_rates = {'Behind': [], 'Even': [], 'Ahead': []}
    for p_obj, e_obj, win in zip(player_total_obj, enemy_total_obj, objective_data['wins']):
        if p_obj < e_obj:
            win_rates['Behind'].append(win)
        elif p_obj == e_obj:
            win_rates['Even'].append(win)
        else:
            win_rates['Ahead'].append(win)
    
    categories = []
    wr_values = []
    colors = []
    
    for category, wins in win_rates.items():
        if wins:
            categories.append(f'{category}\n({len(wins)} games)')
            wr_values.append(sum(wins) / len(wins) * 100)
            if category == 'Behind':
                colors.append('red')
            elif category == 'Even':
                colors.append('yellow')
            else:
                colors.append('green')
    
    if categories:
        bars4 = ax4.bar(categories, wr_values, color=colors, alpha=0.7)
        ax4.set_ylabel('Win Rate (%)')
        ax4.set_title(f'{player_name} - Win Rate by Major Objective Control')
        ax4.set_ylim(0, 100)
        
        # Add percentage labels
        for bar, wr in zip(bars4, wr_values):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{wr:.1f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.show()


def main():
    """Main function for baron and herald analysis visualization."""
    parser = argparse.ArgumentParser(description="Generate personal baron and herald statistics visualization")
    parser.add_argument("player", type=str, help="Player name to analyze (must exist in config)")
    parser.add_argument("--matches-dir", type=str, default="matches", 
                       help="Directory containing match JSON files")
    
    args = parser.parse_args()
    
    # Load player config to get PUUID
    puuids = league.load_player_config()
    if args.player not in puuids:
        available_players = ", ".join(puuids.keys())
        print(f"Player '{args.player}' not found. Available: {available_players}")
        return
        
    player_puuid = puuids[args.player]
    
    # Extract objective data
    print(f"Analyzing baron and herald data for {args.player}...")
    objective_data = extract_baron_herald_data(player_puuid, args.matches_dir)
    
    if objective_data['total_games'] == 0:
        print(f"No matches found for {args.player}")
        return
    
    # Generate visualization
    plot_baron_herald_analysis(args.player, objective_data)


if __name__ == "__main__":
    main()
