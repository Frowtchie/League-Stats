import csv
import matplotlib.pyplot as plt

def read_drake_data(file_path):
    team_elders, team_elemental_drakes = {}, {}
    with open(file_path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            team = row["teamname"]
            try:
                elders = int(row["elders"])
                elemental_drakes = int(row["elementaldrakes"])
            except ValueError:
                continue

            team_elders[team] = team_elders.get(team, 0) + elders
            team_elemental_drakes[team] = team_elemental_drakes.get(team, 0) + elemental_drakes
    return team_elders, team_elemental_drakes

def plot_drakes(team_elders, team_elemental_drakes):
    teams = list(team_elders.keys())
    elder_counts = [team_elders[team] for team in teams]
    elemental_counts = [team_elemental_drakes[team] for team in teams]

    x = range(len(teams))
    plt.bar(x, elder_counts, width=0.4, label="Elder Drakes", align="center")
    plt.bar(x, elemental_counts, width=0.4, label="Elemental Drakes", align="edge")
    plt.xticks(x, teams, rotation=45)
    plt.xlabel("Teams")
    plt.ylabel("Drakes")
    plt.title("Drakes by Team")
    plt.legend()
    plt.tight_layout()
    plt.show()

def main():
    file_path = "LEC.csv"
    team_elders, team_elemental_drakes = read_drake_data(file_path)
    plot_drakes(team_elders, team_elemental_drakes)

if __name__ == "__main__":
    main()
