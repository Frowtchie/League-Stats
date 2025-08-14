import csv
import matplotlib.pyplot as plt
import sys

def read_objective_data(file_path):
    team_barons, team_heralds = {}
    with open(file_path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            team = row["teamname"]
            try:
                barons = int(row["barons"])
                heralds = int(row["heralds"])
            except ValueError:
                continue

            team_barons[team] = team_barons.get(team, 0) + barons
            team_heralds[team] = team_heralds.get(team, 0) + heralds
    return team_barons, team_heralds

def plot_objectives(team_barons, team_heralds):
    teams = list(team_barons.keys())
    baron_counts = [team_barons[team] for team in teams]
    herald_counts = [team_heralds[team] for team in teams]

    x = range(len(teams))
    plt.bar(x, baron_counts, width=0.4, label="Barons", align="center")
    plt.bar(x, herald_counts, width=0.4, label="Heralds", align="edge")
    plt.xticks(x, teams, rotation=45)
    plt.xlabel("Teams")
    plt.ylabel("Objectives")
    plt.title("Barons and Heralds by Team")
    plt.legend()
    plt.tight_layout()
    plt.show()

def main():
    if len(sys.argv) < 2:
        print("Usage: python graph_barons_heralds.py <league>")
        sys.exit(1)

    league = sys.argv[1]
    file_path = f"{league.upper()}.csv"
    team_barons, team_heralds = read_objective_data(file_path)
    plot_objectives(team_barons, team_heralds)

if __name__ == "__main__":
    main()
