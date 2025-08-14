import csv
import matplotlib.pyplot as plt

# Read data from csv file
data = []
with open("LEC.csv", "r") as file:
    reader = csv.DictReader(file)
    for row in reader:
        data.append(row)

# Get data for firstblood and elemental drakes
team_firstblood = {}
team_firstbloodvictim = {}
for row in data:
    team = row["teamname"]
    try:
        firstblood = int(row["firstblood"])
    except ValueError:
        # Handle the error here, for example by logging or skipping the row
        continue
    try:
        firstbloodvictim = int(row["firstbloodvictim"])
    except ValueError:
        # Handle the error here, for example by logging or skipping the row
        continue

    
    if team not in team_firstblood:
        team_firstblood[team] = 0
    team_firstblood[team] += firstblood
    
    if team not in team_firstbloodvictim:
        team_firstbloodvictim[team] = 0
    team_firstbloodvictim[team] += firstbloodvictim

# Plot bar graph
teams = list(team_firstblood.keys())
firstblood_counts = [team_firstblood[team] for team in teams]
firstbloodvictim_counts = [team_firstbloodvictim[team] for team in teams]

x = range(len(teams))
fig, ax = plt.subplots()
bar_width = 0.35

bar1 = ax.bar(x, firstblood_counts, bar_width, label='Firstbloods')
bar2 = ax.bar([i + bar_width for i in x], firstbloodvictim_counts, bar_width, label='Firstblood Victims')

ax.set_xlabel("Team")
ax.set_ylabel("Count")
ax.set_xticks([i + bar_width / 2 for i in x], teams)
ax.legend()

plt.show()
