#!/usr/bin/python3

import os
import pandas as pd
import numpy as np

directory_string = './Fantasy-Premier-League/data/20{0}-{1}/players/'
players_data = {}
player_names = set()
players = {}
index_count = 0
fields = ['assists', 'bonus', 'bps', 'clean_sheets', 'creativity', 'goals_conceded', 'goals_scored', 'ict_index', 'influence', 'minutes', 'opponent_team', 'own_goals', 'penalties_missed', 'penalties_saved', 'player', 'red_cards', 'round', 'saves', 'selected', 'team_a_score', 'team_h_score', 'threat',  'total_points', 'transfers_balance', 'transfers_in', 'transfers_out', 'value', 'was_home', 'yellow_cards', 'total_points']

for season in range(0, 4):
    formatted_string = directory_string.format(season + 16, season + 16 + 1)
    directory = os.fsencode(formatted_string)

    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        name = " ".join(filename.split('_')[:2])
        player_names.add(name)

        if name not in players:
            players[name] = index_count
            index_count = index_count + 1

        csv = pd.read_csv(formatted_string + filename + '/gw.csv', encoding = "UTF-8")
        csv['round'] = 38 * season + csv['round']
        csv['player'] = pd.Series([players[name]] * len(csv))
        csv = csv[fields]
        csv = csv.astype('float')

        if name not in players_data:
            players_data[name] = csv
        else:
            players_data[name] = pd.concat([players_data[name], csv])
            

players_data = { name : df for name, df.drop_duplicates(subset=['round'], keep='last') in players_data.items() if len(players_data[name]) > 1}

for name in players_data:
    players_data[name].to_csv('players/{0}.csv'.format(name), index=False)

print("Done collecting player data!")

name_mapping = {}
player_mapping = pd.read_csv('name_conversions.csv', encoding = "UTF-8")
for _, row in player_mapping.iterrows():
    name_mapping[row['bad_name']] = row['good_name']

directory_string = './Fantasy-Premier-League/data/20{0}-{1}/'

print('Done converting names!')

positions_and_teams={}
for season in range(0, 4):
    formatted_string = directory_string.format(season + 16, season + 16 + 1)

    csv = pd.read_csv(formatted_string + 'players_raw.csv', encoding = "UTF-8")
    for _, row in csv.iterrows():
        name = row['first_name'] + ' ' + row['second_name']
        name = name_mapping[name] if name in name_mapping else name
        
        position = row['element_type']
        team_id = row['team_code']
    
        if name not in positions_and_teams:
            positions_and_teams[name] = (position, [None] * 4)
        positions_and_teams[name][1][season] = team_id

print('Done collecting positions and teams')

gameweek_data=[[pd.DataFrame(columns=['name', 'team', 'position', 'value', 'total_points']) for i in range(0, 38)] for i in range(0,4)]

for name in players_data:
    for row in players_data[name].itertuples():
        convenient_round = int(row.round) - 1
        season = convenient_round // 38
        week = convenient_round % 38
        position = positions_and_teams[name][0]
        team = positions_and_teams[name][1][season]
        value = row.value
        total_points = row.total_points
        data = {'name' : name, 'team' : team, 'position' : position, 'value': value, 'total_points' : total_points}
        old_data = gameweek_data[season][week]
        gameweek_data[season][week] = old_data.append(data, ignore_index=True)

for season in range(0, 4):
    for week in range(0, 38):
        gameweek_data[season][week].to_csv('gw/{0}.csv'.format(38 * season + week + 1), index=False)
        
print('Done collecting gameweek data!')

df = pd.read_csv('gw/1.csv')

import pulp

all_players = { row.name : pulp.LpVariable(row.name, lowBound=0, upBound=1, cat="Integer") for row in df.itertuples() }

goal_keepers = { row.name : all_players[row.name] for row in df.itertuples() if row.position == 1}

defenders = { row.name : all_players[row.name] for row in df.itertuples() if row.position == 2}

mid_fielders = { row.name : all_players[row.name] for row in df.itertuples() if row.position == 3}

strikers = { row.name : all_players[row.name] for row in df.itertuples() if row.position == 4}

model = pulp.LpProblem("Trying", pulp.LpMaximize)

# Objective Function
model += pulp.lpSum( [all_players[row.name] * row.total_points for row in df.itertuples()] )

# 2 Goalkeepers, 5 defenders, 5 mid_fields, 5 strikers
model += pulp.lpSum( [goal_keepers[name] for name in goal_keepers] ) == 2

model += pulp.lpSum( [defenders[name] for name in defenders] ) == 5

model += pulp.lpSum( [mid_fielders[name] for name in mid_fielders] ) == 5

model += pulp.lpSum( [strikers[name] for name in strikers] ) == 3

# Cost Cap
model += pulp.lpSum( [all_players[row.name] * row.value for row in df.itertuples()] ) <= 1000

# Team Constraints
for team in df['team'].tolist():
    team_members = { row.name : all_players[row.name] for row in df.itertuples() if int(row.team) == int(team)}

    model += pulp.lpSum( [team_members[name] for name in team_members] ) <= 3

model.solve()
