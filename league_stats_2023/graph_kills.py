import csv
import matplotlib.pyplot as plt
import sys
import datetime

def read_csv_data(file_path, team_name):
    kills, enemy_kills, game_dates, date_counter = [], [], [], {}
    with open(file_path, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["teamname"] == team_name and row["position"] == "team":
                kills.append(int(row["kills"]))
                enemy_kills.append(int(row["deaths"]))
                date = datetime.datetime.strptime(row["date"], '%Y-%m-%d %H:%M:%S')
                formatted_date = date.strftime("%d/%m")
                if formatted_date not in date_counter:
                    date_counter[formatted_date] = 1
                else:
                    date_counter[formatted_date] += 1
                game_dates.append(formatted_date + f" G{date_counter[formatted_date]}")
    return kills, enemy_kills, game_dates

def plot_kills(game_dates, kills):
    plt.plot(game_dates, kills, "bo")
    plt.plot(game_dates, kills, label="Kills")
    plt.xlabel("Game Dates")
    plt.ylabel("Kills")
    plt.title("Kills Over Games")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def main():
    if len(sys.argv) < 3:
        print("Usage: python graph_kills.py <team_name> <league>")
        sys.exit(1)

    team_name = sys.argv[1]
    league = sys.argv[2]
    file_path = f"{league.upper()}.csv"

    kills, enemy_kills, game_dates = read_csv_data(file_path, team_name)
    plot_kills(game_dates, kills)

if __name__ == "__main__":
    main()
