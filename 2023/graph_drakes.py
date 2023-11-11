import csv
import matplotlib.pyplot as plt

# Read data from csv file
data = []
with open("LEC.csv", "r") as file:
    reader = csv.DictReader(file)
    for row in reader:
        data.append(row)

# Get data for elders and elemental drakes
team_elders = {}
team_elemental_drakes = {}
for row in data:
    team = row["teamname"]
    try:
        elders = int(row["elders"])
    except ValueError:
        # Handle the error here, for example by logging or skipping the row
        continue

    elemental_drakes = int(row["elementaldrakes"])
    
    if team not in team_elders:
        team_elders[team] = 0
    team_elders[team] += elders
    
    if team not in team_elemental_drakes:
        team_elemental_drakes[team] = 0
    team_elemental_drakes[team] += elemental_drakes

# Plot bar graph
teams = list(team_elders.keys())
dragon_counts = [team_elders[team] for team in teams]
elemental_drake_counts = [team_elemental_drakes[team] for team in teams]

x = range(len(teams))
fig, ax = plt.subplots()
bar_width = 0.35

bar1 = ax.bar(x, dragon_counts, bar_width, label='Elder Drakes')
bar2 = ax.bar([i + bar_width for i in x], elemental_drake_counts, bar_width, label='Elemental Drakes')

ax.set_xlabel("Team")
ax.set_ylabel("Count")
ax.set_xticks([i + bar_width / 2 for i in x], teams)
ax.legend()

plt.show()
