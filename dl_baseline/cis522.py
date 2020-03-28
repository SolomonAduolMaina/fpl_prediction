#!/usr/bin/python3

import os
import pandas as pd
import numpy as np

directory_string = '../Fantasy-Premier-League/data/20{0}-{1}/players/'
players_data = {}
player_gameweek_index = {}
index_count = 0
fields = ['assists', 'bonus', 'bps', 'clean_sheets', 'creativity', 'goals_conceded', 'goals_scored', 'ict_index', 'influence', 'minutes', 'opponent_team', 'own_goals', 'penalties_missed', 'penalties_saved', 'red_cards', 'saves', 'team_a_score', 'team_h_score', 'threat', 'total_points', 'value', 'was_home', 'yellow_cards']

for season in range(0, 4):
    formatted_string = directory_string.format(season + 16, season + 16 + 1)
    directory = os.fsencode(formatted_string)

    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        name = " ".join(filename.split('_')[:2])
        if name not in players_data:
            players_data[name] = pd.DataFrame()

        for game_week in range(0, 38):
            player_gameweek_index[(name, season, game_week)] = index_count
            index_count = index_count + 1

        csv = pd.read_csv(formatted_string + filename + '/gw.csv', encoding = "ISO-8859-1")
        csv = csv[fields]
        index = pd.Series([player_gameweek_index[name, season, game_week] for game_week in range(len(csv))])
        csv['index'] = index
        players_data[name] = pd.concat([players_data[name], csv])
