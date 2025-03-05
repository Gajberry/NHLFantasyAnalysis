## Functions to access data from the API and clean it.


import requests
import pandas as pd
import json

import sys
sys.path.append("..")
from base_python_files.api_info import *

def retrieve_espn_data(swid,espn_s2,league_id):
    url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/seasons/2025/segments/0/leagues/{league_id}?view=kona_player_info"

    filters = {
        "players": {
            "limit": 2000,
            "sortDraftRanks": {"sortPriority": 100, "sortAsc": True, "value": "STANDARD"},
        }
    }

    headers = {"x-fantasy-filter": json.dumps(filters)}

    r = requests.get(url, headers=headers, cookies={"SWID": swid, "espn_s2": espn_s2})
    return r.json()

def clean_data(d,all_cats = False):
    data = []
    for index, player in enumerate(d["players"]):
        player_id = player["id"]
        name = player["player"]["fullName"]
        teamId = player["player"]["proTeamId"]
        lteamId = int(player["onTeamId"])
        status = player["status"]
        try:
            injury_status = player["player"]["injuryStatus"]
        except:
            injury_status = None
        if status != "ONTEAM":
            lteamId = None

        eligible_slots = player["player"]["eligibleSlots"]
        position = ""
        if eligible_slots[0] == 3:
            if 0 in eligible_slots:
                position += "C"
            if 1 in eligible_slots:
                position += "LW"
            if 2 in eligible_slots:
                position += "RW"
        elif eligible_slots[0] == 4:
            position += "D"
        elif eligible_slots[0] == 5:
            position += "GK"
        else:
            print(f"Player has irregular eligible slots: {name} has slots {eligible_slots}")
        try:
            projections = {}
            for stat_group in player["player"]["stats"]:
                if stat_group["id"] == "102025":
                    projections = stat_group["stats"]
        except KeyError:
            projections = {}

        so_far = []
        for time_key_key in time_keys:
            try:
                for stat_group in player["player"]["stats"]:
                    if stat_group["id"] == time_keys[time_key_key]:
                        so_far.append(stat_group["stats"])
            except KeyError:
                pass

        all_stats = []
        for years_of_interest in [projections] + so_far:
            stats = {}
            if position != "GK":
                for term, key in non_gk_terms.items():
                    try:
                        stats[term] = years_of_interest[key]
                    except KeyError:
                        stats[term] = None
                if stats["average_time_on_ice"] is not None:
                    stats["average_time_on_ice"] = stats["average_time_on_ice"] / 60
            else:
                for term, key in gk_terms.items():
                    try:
                        stats[term] = years_of_interest[key]
                    except KeyError:
                        stats[term] = None

                # Special cases that require additional calculations:
                try:
                    stats["average_time_on_ice"] = (
                        years_of_interest["8"] / 60 / stats["games_played"]
                    )
                    stats["goals_on_average"] = (
                        stats["shots_at_them"]
                        * (1 - stats["save_percent"])
                        / years_of_interest["8"]
                    )
                except (KeyError, TypeError,ZeroDivisionError):
                    stats["average_time_on_ice"] = None
                    stats["goals_on_average"] = None
                    

            for stat, val in stats.items():
                if stat != "games_played" and val != None and stat != "average_time_on_ice":
                    if stats["games_played"] == 0:
                        stats[stat] = 0
                    else:
                        stats[stat] = val / stats["games_played"]
            all_stats.append(stats)

        new_line = [player_id, name, teamId, lteamId, position, injury_status]

        for stats in all_stats:
            new_line += list(dict(sorted(stats.items())).values())
        data.append(new_line)

        if index == 0:
            columns = ["ID", "Name", "TeamID", "LeagueTeamID", "Position", "InjuryStatus"]
            for stats, stats_name in zip(all_stats, all_stats_names):
                columns += [
                    x + stats_name for x in list(dict(sorted(stats.items())).keys())
                ]
    data = pd.DataFrame(data, columns=columns)

    for stat_name in all_stats_names:
        data["power play points" + stat_name] = (
            data["power play assists" + stat_name] + data["power play goals" + stat_name]
        )
        data["short handed points" + stat_name] = (
            data["short handed assists" + stat_name]
            + data["short handed goals" + stat_name]
        )
        data["FOPercent" + stat_name] = data["FOW" + stat_name] / (
            data["FOW" + stat_name] + data["FOL" + stat_name]
        )
    
    data = data.reset_index()
    return data

def retrieve_espn_matchup(swid,espn_s2,league_id,week):
    url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/seasons/2025/segments/0/leagues/{league_id}?view=mMatchup"

    r = requests.get(url,
                        cookies={"SWID": swid, "espn_s2": espn_s2})

    d = r.json()
    scoring_weights = {
        '13':'goals',
        '14':'assists',
        '15':'plus_minus',
        '17':'penalty_minutes',
        '23':'FOW',
        '27':'average_time_on_ice',
        '29':'shots_on_goal',
        '31':'hits',
        '32':'blocks',
        '38':'power play points'
    }
    team_scores = {}
    for matchup in d['schedule'][4*(week-1):4*week]:
        teams = [matchup['home'],matchup['away']]
        for team in teams:
            team_score_dict = {}
            team_score = team['cumulativeScore']['scoreByStat']
            for score_cat in team_score:
                # if team_score[score_cat]['ineligible']==False:
                if score_cat in scoring_weights:
                    if team_score[score_cat]['ineligible']==True:
                        team_score_dict[scoring_weights[score_cat]]=-0
                    else:
                        team_score_dict[scoring_weights[score_cat]]=team_score[score_cat]['score']
            team_scores[team['teamId']] = team_score_dict
    return team_scores