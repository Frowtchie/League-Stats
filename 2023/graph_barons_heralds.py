import csv
import matplotlib.pyplot as plt
import sys

league = sys.argv[1]
# Read data from csv file
data = []
with open(league.upper()+".csv", "r") as file:
    reader = csv.DictReader(file)
    for row in reader:
        data.append(row)

# Get data for barons and elemental drakes
team_barons = {}
team_heralds = {}
for row in data:
    team = row["teamname"]
    try:
        barons = int(row["barons"])
    except ValueError:
        # Handle the error here, for example by logging or skipping the row
        continue
    try:
        heralds = int(row["heralds"])
    except ValueError:
        # Handle the error here, for example by logging or skipping the row
        continue
    
    if team not in team_barons:
        team_barons[team] = 0
    team_barons[team] += barons
    
    if team not in team_heralds:
        team_heralds[team] = 0
    team_heralds[team] += heralds

# Plot bar graph
teams = list(team_barons.keys())
baron_counts = [team_barons[team] for team in teams]
herald_counts = [team_heralds[team] for team in teams]

x = range(len(teams))
fig, ax = plt.subplots()
bar_width = 0.35

bar1 = ax.bar(x, baron_counts, bar_width, label='Barons')
bar2 = ax.bar([i + bar_width for i in x], herald_counts, bar_width, label='Heralds')

ax.set_xlabel("Team")
ax.set_ylabel("Count")
ax.set_xticks([i + bar_width / 2 for i in x], teams)
for i in range(5):
    ax.axhline(y=i, color='gray', linestyle='--')
ax.legend()

plt.show()
