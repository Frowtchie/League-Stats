import csv
import matplotlib.pyplot as plt
import sys
import datetime

team_name = sys.argv[1]
league = sys.argv[2]
kills = []
enemy_kills = []
game_dates = []
date_counter = {}

# Read the CSV file
with open(league.upper()+".csv", "r") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        if row["teamname"] == team_name and row["position"] == "team" :
            kills.append(int(row["kills"]))
            enemy_kills.append(int(row["deaths"]))
            date = datetime.datetime.strptime(row["date"], '%Y-%m-%d %H:%M:%S')
            formatted_date = date.strftime("%d/%m")
            if formatted_date not in date_counter:
                date_counter[formatted_date] = 1
            else:
                date_counter[formatted_date] += 1
            game_dates.append(formatted_date + f" G{date_counter[formatted_date]}")

# Create the line graph
plt.plot(game_dates, kills, "bo")
plt.plot(game_dates, kills, label = "Kills")
plt.plot(game_dates, enemy_kills, "r", label = "Enemy kills")
plt.xlabel("Game Dates")
plt.xticks(rotation=90, ha='right')
plt.ylabel("Number of Kills")
plt.title("Number of Kills per Game for " + team_name)
for i in range(10):
    plt.axhline(y=i*5, color='gray', linestyle='--')
for i in range(len(game_dates)):
    plt.axvline(x=i, color='gray', linestyle='dotted')
plt.legend()
plt.show()
