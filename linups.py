import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from box_score import box_score, PM
import re


    # box_for_lineups, stints_by_lineup, events_by_lineup = plot3_lineup_prep(
    #     playTimesbyPlayer = playTimesbyPlayer1,
    #     play_by_play      = play_by_play,
    #     boxscore_         = our_stints[1],
    #     scoreMargins      = scoreMargins
    # )

from plots import mscatter, event_to_size_color_shape, LABLE_SIZE

from datetime import timedelta

def line_up_abbr(lineup_):
    # utility - takes CAPS from player names to make lineup name
    def _lu_small(name_):
        return re.sub('[^A-Z]', '', name_)

    l_key = list(map(lambda x: _lu_small(x), lineup_))
    l_key.sort()
    return '-'.join(l_key)

def plot3_lineup_prep(playTimesbyPlayer, play_by_play, boxscore_, scoreMargins):
    # create stints by line_up, from stints by per player

    players = list(playTimesbyPlayer)

    stints_by_player = []
    for player in players:
        stints = playTimesbyPlayer[player]
        for stint in stints:
            stint_start = int(stint[0])
            stint_duration = int(stint[1])
            stints_by_player.extend([[stint_start, stint_duration, player]])

    events_by_lineup = {}

    # create stints by line up.
    # Stints are the timespans that a player or lineup is playing.
    # Flattend player stints are sorted by time of stint start.
    # After you have 5 players the next stint cause some one to leave
    # and some one to enter.  The enter starts a new stint and
    # the leaving one close off the current stint. Add it to the list
    # of stints for this lineup and save this time as the start of
    # the next stint

    stints_by_lineup  = {}  # collected stints for a linup
    players_by_lineup = {}  # players in a linup
    bs_data_by_lineup = {}  # boxscore summary data for each lineup
    events_by_lineup  = {}  # shots, fouls, etc by lneup

    # create stints by lineup
    current_lineup = [] # collect players currently playing
    last_start = 0      # last time we started a stint

    for player_stint in sorted(stints_by_player, key=lambda x: x[0]):
        if len(current_lineup) != 5:
            current_lineup.extend([player_stint])
        else:
            broke = False
            player_names = list(np.array(current_lineup)[:, 2])
            key = line_up_abbr(player_names)
            for _player in current_lineup:

                pstart = _player[0]
                pduration = _player[1]
                pend = pstart + pduration

                if pend == player_stint[0]:
                    _span = player_stint[0] - last_start
                    if key in list(stints_by_lineup.keys()):
                        stints_by_lineup[key].extend([[last_start, _span]])

                    else:
                        if _span > 0:
                            stints_by_lineup[key] = [[last_start, _span]]
                            players_by_lineup[key] = player_names.copy()

                    last_start = player_stint[0]

                    current_lineup.remove(_player)
                    current_lineup.extend([player_stint])
                    broke = True
                    break

            if not broke:
                print('---not found', _player, last_start, current_lineup)

    # remove stints totaling less than xxx seconds
    MIN_STINT_TIME = 90
    lups =  list(stints_by_lineup.keys())
    for line_up in lups:
        if sum(np.array(stints_by_lineup[line_up])[:, 1]) < MIN_STINT_TIME:
            stints_by_lineup.pop(line_up)


    for line_up in stints_by_lineup:

        boxscore = box_score({})

        players_in_lineup = players_by_lineup[line_up]
        stints_in_lineup = stints_by_lineup[line_up]

        a_ = play_by_play['player1_name'].isin(players_in_lineup)
        b_ = play_by_play['player2_name'].isin(players_in_lineup)
        c_ = play_by_play['player3_name'].isin(players_in_lineup)

        def in_stint__(row):
            for stint in stints_in_lineup:
                # if (row.sec > stint[0]) & (row.sec <= (stint[0] + stint[1])):
                if stint[0] <= row.sec <= (stint[0] + stint[1]):
                    return True
            return False

        e_ = play_by_play.apply(lambda row: in_stint__(row), axis=1)

        ours = (a_ | b_ | c_) & e_
        plays_this_stint_this_player = play_by_play[ours]

        events_for_lineup = []
        for i, v in plays_this_stint_this_player.iterrows():
            if ours[i]:
                _ec, _es, _et, _ec2, _es2, _et2 = event_to_size_color_shape(players_in_lineup, v)
                if  _ec != None: events_for_lineup.extend([v.sec, _ec, _es, _et])
                if _ec2 != None: events_for_lineup.extend([v.sec, _ec2, _es2, _et2])

            else:
                print('WHAT')

        events_by_lineup[line_up] = events_for_lineup

        secs_total_this_lineup = sum(np.array(stints_in_lineup)[:, 1])

        def sm(x): return scoreMargins[x[0]] - scoreMargins[x[0]] + scoreMargins[x[1]]
        scoreMargin_this_lineup = sum(
            list(map(lambda x: sm(x), stints_by_lineup[line_up]))
        )

        boxscore.stuff_bs(plays_this_stint_this_player, players_in_lineup)

        boxscore.summary()

        bs_rows, bs_columns, bs_data = boxscore.get_bs_data(['TEAM'], all=True)
        bs_data[0][bs_columns.index('secs')] = secs_total_this_lineup
        bs_data[0][bs_columns.index(PM)] = scoreMargin_this_lineup
        bs_data_by_lineup[line_up] = bs_data[0]

    box_score_for_lineups = box_score({})
    l_players = list(bs_data_by_lineup.keys())
    box_score_for_lineups.add_players(l_players)
    for l_players in l_players:
        for index, item in enumerate(bs_columns):
            val = (
                bs_data_by_lineup[l_players][index]
                if item not in ['MIN', '3PT', 'FG', 'FT']
                else 0
            )
            box_score_for_lineups.set_item(l_players, item, val)

    box_score_for_lineups.summary()

    # undo damage done by make_summary which works for 5 players
    secs = box_score_for_lineups.get_item('TEAM', 'secs')
    box_score_for_lineups.set_item(
        'TEAM', 'MIN', str(timedelta(seconds=int(secs)))[2:4])

    plus_minus = box_score_for_lineups.get_item('TEAM', PM)
    box_score_for_lineups.set_item('TEAM', PM, plus_minus * 5)

    return box_score_for_lineups, stints_by_lineup, events_by_lineup


def plot3_stints(playTimesbyPlayer, ax, events_by_player):

    labels = list(playTimesbyPlayer.keys())

    for i, label in enumerate(labels):

        data = playTimesbyPlayer[label]
        starts = list(map(lambda x: x[0], data))
        widths = list(map(lambda x: x[1], data))
        rects = ax.barh(
            str(label), widths, left=starts, color='plum', height=0.15, zorder=3)

        scatter = mscatter(
            events_by_player[label][0::4],
            [i] * len(events_by_player[label][0::4]),
            c = events_by_player[label][1::4], 
            s = events_by_player[label][2::4], 
            m = events_by_player[label][3::4], 
            ax = ax,
            zorder = 3,
            alpha = [.5]* len(events_by_player[label][0::4]))

    ax.invert_yaxis()
    ax.yaxis.set_visible(False)
    ax.set_xlim(-50, (48 * 60) + 50)
    ax.set_xticks([0, 12 * 60, 24 * 60, 36 * 60, 48 * 60], ['', '', '', '', ''])

    ax.set_xticks([6 * 60, 18 * 60, 30 * 60, 42 * 60], minor=True)
    ax.set_xticklabels(['Q1', 'Q2', 'Q3', 'Q4'], minor=True)

    ax.tick_params(axis='both', which='both', labelsize=LABLE_SIZE, length=0, pad=0, direction='in')
    ax.grid(True, axis='x', color='darkgrey', linestyle='-', linewidth=1, zorder=0)
