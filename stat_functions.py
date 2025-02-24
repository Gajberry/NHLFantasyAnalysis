from api_info import *
import matplotlib.pyplot as plt
import pandas as pd

def get_player_scores(data,scoring_weights,opp_id = None,):
    skater_data = data[data["Position"] != "GK"].copy()

    played_players = skater_data  # [skater_data['games_played so far']>=3]

    for stat_name in all_stats_names:
        played_players.loc[:,"sum scores " + stat_name] = 0
    for cat in scoring_weights:
        for stat_name in all_stats_names:
            played_players[cat + stat_name] = played_players[cat + stat_name].fillna(0)
            if opp_id is None:
                cat_team_mean = played_players[played_players["LeagueTeamID"].isna()][
                    cat + stat_name
                ].mean()
                cat_team_std = played_players[played_players["LeagueTeamID"].isna()][
                    cat + stat_name
                ].std()
            else:
                cat_team_mean = played_players[played_players["LeagueTeamID"] == opp_id][
                    cat + "AT"
                ].mean()
                cat_team_std = played_players[played_players["LeagueTeamID"] == opp_id][
                    cat + "AT"
                ].std()
            played_players[cat + " stat"] = (
                played_players[cat + stat_name] - cat_team_mean
            ) / cat_team_std
            
            played_players["sum scores " + stat_name] += (
                played_players[cat + " stat"] * scoring_weights[cat]
            )

    played_players = played_players[
        ["ID", "Name", "TeamID", "LeagueTeamID", "Position", "InjuryStatus"]
        + ["sum scores " + stat_name for stat_name in all_stats_names]
        + ["games_played" + stat_name for stat_name in all_stats_names]
    ]
    return played_players

def get_week_predictions(teams, played_players,games,skater_cats,scores,swapped_days,dropped_days,current_players,current_day=None,predict_tomorrow=False):
    
    g_team,opp_team = teams 
    current_g_scores,current_opp_scores = scores
    swapped_days_g,swapped_days_opp = swapped_days
    dropped_days_g,dropped_days_opp = dropped_days
    current_g_players,current_opp_players = current_players
    
    original_g_team = g_team.copy()
    original_opp_team = opp_team.copy()
    prop_distances = []
    overall_wins = 0
    pred_g_num_players = 0
    pred_opp_num_players = 0
    win_cats = []
    
    for ind, cat in enumerate(skater_cats):
        g_scores = []
        opp_scores = []
        current_day_passed = False
        next_day_passed = False
        pred_final_opp_score = current_opp_scores[cat]
        pred_final_g_score = current_g_scores[cat]
        if cat == "average_time_on_ice":
            g_num_players = []
            opp_num_players = []
            pred_g_num_players = 0
            pred_opp_num_players = 0
        for day in [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]:
            if day in swapped_days_g:
                for pair in swapped_days_g[day]:
                    drop = pair[0]
                    if drop is not None:
                        g_team_drop = g_team.drop(
                            g_team[g_team["Name"] == drop].iloc[0].name
                        )
                        if len(pair) == 2:
                            addition = pair[1]
                            g_team_add = played_players[played_players["Name"] == addition]
                            g_team = pd.merge(g_team_drop, g_team_add, how="outer")
                        else:
                            g_team = g_team_drop
                    else:
                        addition = pair[1]
                        g_team_add = played_players[played_players["Name"] == addition]
                        g_team = pd.merge(g_team, g_team_add, how="outer")
                    # print(g_team['Name'])

            day_games = games[games["Day"] == day]

            if day in dropped_days_g:
                drop_list = dropped_days_g[day]
            else:
                drop_list = []
            g_players_h = g_team[
                (g_team["Team"].isin(day_games["Home Team"]))
                & ~(g_team["Name"].isin(drop_list))
            ]
            g_players_a = g_team[
                (g_team["Team"].isin(day_games["Away Team"]))
                & ~(g_team["Name"].isin(drop_list))
            ]

            if cat == "average_time_on_ice":
                if len(g_num_players) == 0:
                    g_num_players.append(len(g_players_h) + len(g_players_a))
                else:
                    g_num_players.append(
                        g_num_players[-1] + len(g_players_h) + len(g_players_a)
                    )

            if len(g_scores) == 0:
                g_scores.append(g_players_h[cat].sum() + g_players_a[cat].sum())
            else:
                g_scores.append(
                    g_scores[-1] + g_players_h[cat].sum() + g_players_a[cat].sum()
                )

            if day in dropped_days_opp:
                drop_list = dropped_days_opp[day]
            else:
                drop_list = []

            opp_players_h = opp_team[
                opp_team["Team"].isin(day_games["Home Team"])
                & ~(opp_team["Name"].isin(drop_list))
            ]
            opp_players_a = opp_team[
                opp_team["Team"].isin(day_games["Away Team"])
                & ~(opp_team["Name"].isin(drop_list))
            ]
            if cat == "average_time_on_ice":
                if len(opp_num_players) == 0:
                    opp_num_players.append(len(opp_players_h) + len(opp_players_a))
                else:
                    opp_num_players.append(
                        opp_num_players[-1] + len(opp_players_h) + len(opp_players_a)
                    )

            if len(opp_scores) == 0:
                opp_scores.append(opp_players_h[cat].sum() + opp_players_a[cat].sum())
            else:
                opp_scores.append(
                    opp_scores[-1] + opp_players_h[cat].sum() + opp_players_a[cat].sum()
                )
            if current_day is None or current_day_passed:
                pred_final_opp_score += opp_players_h[cat].sum() + opp_players_a[cat].sum()
                pred_final_g_score += g_players_h[cat].sum() + g_players_a[cat].sum()
                pred_g_num_players += len(g_players_h) + len(g_players_a)
                pred_opp_num_players += len(opp_players_h) + len(opp_players_a)
                if not next_day_passed and predict_tomorrow:
                    print()
                    print(
                        f"predictions for today: {cat}, G: {pred_final_g_score},OPP: {pred_final_opp_score}"
                    )
                    next_day_passed = True
            if day == current_day:
                current_day_passed = True
                pred_g_num_players = current_g_players
                pred_opp_num_players = current_opp_players
        plt.figure(ind)
        plt.xlabel("Day of the week")
        plt.ylabel(cat)

        if cat == "average_time_on_ice":
            # print(pred_final_g_score,pred_final_opp_score,pred_g_num_players,pred_opp_num_players)
            if pred_g_num_players != 0:
                plt.plot(
                    [0, 7],
                    [
                        pred_final_g_score / pred_g_num_players,
                        pred_final_g_score / pred_g_num_players,
                    ],
                    "b.-",
                    label='final prediction g'
                )
                plt.plot(
                    [0, 7],
                    [
                        pred_final_opp_score / pred_opp_num_players,
                        pred_final_opp_score / pred_opp_num_players,
                    ],
                    "r.-",
                    label='final prediction opp'
                )
                if (
                    pred_final_g_score / pred_g_num_players
                    > pred_final_opp_score / pred_opp_num_players
                ):
                    print("win", cat, pred_final_g_score / pred_g_num_players / 60)
                    overall_wins += 1
            plt.plot(
                range(0, 8),
                [0] + [g_scores[i] / g_num_players[i] for i in range(len(g_scores))],
                c="b",
            )
            plt.plot(
                range(0, 8),
                [0] + [opp_scores[i] / opp_num_players[i] for i in range(len(opp_scores))],
                c="r",
            )
            plt.plot(
                [0, 7],
                [
                    current_g_scores[cat] / current_g_players,
                    current_g_scores[cat] / current_g_players,
                ],
                "b--",
                label='current g'
            )
            plt.plot(
                [0, 7],
                [
                    current_opp_scores[cat] / current_opp_players,
                    current_opp_scores[cat] / current_opp_players,
                ],
                "r--",
                label='current opp'
            )
            plt.ylim([16, 23])
            print()
            print(
                "End:",
                cat,
                "G",
                pred_final_g_score / pred_g_num_players,
                "Opp",
                pred_final_opp_score / pred_opp_num_players,
                "Diff",
                pred_final_g_score / pred_g_num_players
                - pred_final_opp_score / pred_opp_num_players,
                (
                    pred_final_g_score / pred_g_num_players
                    - pred_final_opp_score / pred_opp_num_players
                )
                / (pred_final_g_score / pred_g_num_players),
            )

        else:
            plt.plot(
                [0, 7],
                [
                    pred_final_g_score,
                    pred_final_g_score,
                ],
                "b.-",
                label='final prediction g'
            )
            plt.plot(
                [0, 7],
                [
                    pred_final_opp_score,
                    pred_final_opp_score,
                ],
                "r.-",
                label='final prediction opp'
            )
            plt.plot(range(0, 8), [0] + g_scores, c="b")
            plt.plot(range(0, 8), [0] + opp_scores, c="r")


            plt.plot(
                [0, 7],
                [
                    current_g_scores[cat],
                    current_g_scores[cat],
                ],
                "b--",
                label='current g'
            )
            plt.plot(
                [0, 7],
                [
                    current_opp_scores[cat],
                    current_opp_scores[cat],
                ],
                "r--",
                label='current opp'
            )

            if pred_final_g_score > pred_final_opp_score:
                win_cats.append(cat)
                overall_wins += 1
            print()
            print(
                "End:",
                cat,
                "G",
                pred_final_g_score,
                "Opp",
                pred_final_opp_score,
                "Diff",
                pred_final_g_score - pred_final_opp_score,
                (pred_final_g_score - pred_final_opp_score) / pred_final_g_score,
            )
        plt.title(f"{cat} predictions")
        plt.legend()
        g_team = original_g_team.copy()
        opp_team = original_opp_team.copy()
    return overall_wins,win_cats,(pred_g_num_players,pred_opp_num_players)

