import pandas as pd
import numpy as np
import itertools

import matplotlib.pyplot as plt
from datetime import datetime, timedelta

from utils import period_clock_seconds
from box_score import box_score
import re

def event_to_size_color_shape(player, eventRecord):

    def em_f1(_color, _size, eventRecord):
        # helper to make 3PT makes a bigger shape on plots
        vis = eventRecord.homedescription
        hom = eventRecord.visitordescription
        _size = 60.0 if (str(vis) + str(hom)).find('3PT') != -1 else 40.0
        return _color, _size    

    def em_f2(_color, _size, eventRecord):
        # differentiate made vs missed free throw by color
        if type(eventRecord.score) != type('a'): _color= 'red'
        return _color, _size
        
    event_map = {
        1: ['lime',   50.0, '*',   'aqua',   25.0, '^',   [1, 2], em_f1], # make, assist
        2: ['red',    20.0, 'v',   'lime',   25.0, '^',   [1, 3], None],  # miss, block
        3: ['lime',   30.0, 'p',   None,     None, ',',   [1],    em_f2], # free throw
        4: ['lime',   25.0, 'o',   None,     None, ',',   [1],    None],  # rebound
        5: ['lime',   25.0, 'd',   'pink',   25.0, 'v',   [1],    None],  # steal, turnover
        6: ['red',    20.0, 'x',   'lime',   10.0, 's',   [1, 2], None],  # foul,  fouled
        8: ['yellow', 10.0, 'o',   'yellow', 10.0, 'o',   [1, 2], None],  # substitution
    }

    # call with player or list of players
    players = [player] if type(player) != type([]) else player
    player_names = [eventRecord.player1_name, eventRecord.player2_name, eventRecord.player3_name]

    # return None's when this is not us
    _size1 = 0
    _color1 = None
    _style1 = ','

    _size2 = 0
    _color2 = None
    _style2 = ','

    if eventRecord.eventmsgtype in event_map.keys():
        # this is an event we want to report on
        action = event_map[eventRecord.eventmsgtype]

        # 1 or 2 players can be attached to this event
        for i, xx in enumerate(action[6]):
            index = i * 3  # for the moment color and size per event, 
            if player_names[xx - 1] in players:
                # its for us color and suze for event
                _co = action[index]
                _si = action[index + 1]
                _st = action[index + 2]
                if _co != None:
                    # if we need help figuring this out call helper
                    if action[7] != None: _co, _si = action[7](_co, _si, eventRecord)
            
                    # first person return in xxx1 all others xxx2
                    if i == 0:
                        _color1 = _co
                        _size1  = _si
                        _style1 = _st
                    else:   
                        _color2 = _co
                        _size2  = _si
                        _style2 = _st

    # return c/s for both possible players
    return _color1, _size1, _style1, _color2, _size2, _style2,

def shorten_player_name(what, max_length):
    # if name longer than max turns 'firstname lastname' to 'first_intial.lastname'
    if len(what) < max_length: return what
    if ' ' in what:
        return what[0] + ". " + what.split(" ")[1]
    return what

LABLE_SIZE = 9
COLWIDTH = 0.09
SCALE = 0.75

def plot3_boxscore(boxscore, ax, players):

    # comments here show up on mouseover
    bs_rows, bs_columns, bs_data = boxscore.get_bs_data(players + ["TEAM"])
    tc = [["black"] * len(bs_columns)] * len(bs_rows)
    trows = list(map(lambda x: shorten_player_name(x, 15), bs_rows))

    cws = [COLWIDTH] * len(bs_columns)
    cws[2] *= 1.2

    the_table = ax.table(
        cellText=bs_data,
        cellColours=tc,
        cellLoc="center",
        colWidths=cws,  # [COLWIDTH]*len(bs_columns),
        rowLabels=trows,
        # rowColours='k',
        rowLoc="right",
        colLabels=bs_columns,
        # colColours='k',
        colLoc="center",
        loc="center",
        edges="",
    )

    SCALE = 9 / len(bs_rows)
    the_table.scale(1.0, SCALE)
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(LABLE_SIZE)

def mscatter(x,y,ax=None, m=None, **kw):
    import matplotlib.markers as mmarkers
    if not ax: ax=plt.gca()
    sc = ax.scatter(x,y,**kw)
    if (m is not None) and (len(m)==len(x)):
        paths = []
        for marker in m:
            if isinstance(marker, mmarkers.MarkerStyle):
                marker_obj = marker
            else:
                marker_obj = mmarkers.MarkerStyle(marker)
            path = marker_obj.get_path().transformed(
                        marker_obj.get_transform())
            paths.append(path)
        sc.set_paths(paths)
    return sc

def plot3_PBP_chart(playTimesbyPlayer, ax, events_by_player):

    labels = list(playTimesbyPlayer.keys())

    for i, label in enumerate(labels):

        data = playTimesbyPlayer[label]
        starts = list(map(lambda x: x[0], data))
        widths = list(map(lambda x: x[1], data))
        rects = ax.barh(label, widths, left=starts, color="plum", height=0.15, zorder=3)

        evnt_cnt = len(events_by_player[label][0::4])

        scatter = mscatter(
            events_by_player[label][0::4],
            [i] * evnt_cnt,
            c  = events_by_player[label][1::4], 
            s  = events_by_player[label][2::4], 
            m  = events_by_player[label][3::4], 
            ax = ax,
            zorder = 3,
            alpha = [.7] * evnt_cnt)

    ax.invert_yaxis()
    ax.yaxis.set_visible(False)
    ax.set_xlim(-50, (48 * 60) + 50)
    ax.set_xticks([0, 12 * 60, 24 * 60, 36 * 60, 48 * 60], ["", "", "", "", ""])

    ax.set_xticks([6 * 60, 18 * 60, 30 * 60, 42 * 60], minor=True)
    ax.set_xticklabels(["Q1", "Q2", "Q3", "Q4"], minor=True)

    ax.tick_params(axis="y", which="major", labelsize=LABLE_SIZE, pad=0, direction="in")
    ax.tick_params(axis="x", which="minor", labelsize=LABLE_SIZE, pad=0, direction="in")
    ax.grid(True, axis="x", color="darkgrey", linestyle="-", linewidth=2, zorder=0)
    ax.tick_params(axis="both", which="both", length=0)

def plot3_stints(playTimesbyPlayer, ax, events_by_player):

    labels = list(playTimesbyPlayer.keys())

    for i, label in enumerate(labels):

        data = playTimesbyPlayer[label]
        starts = list(map(lambda x: x[0], data))
        widths = list(map(lambda x: x[1], data))
        rects = ax.barh(
            str(label), widths, left=starts, color="plum", height=0.15, zorder=3)

        scatter = mscatter(
            events_by_player[label][0::4],
            [i] * len(events_by_player[label][0::4]),
            c=events_by_player[label][1::4], 
            s=events_by_player[label][2::4], 
            m=events_by_player[label][3::4], 
            ax=ax,
            zorder = 3,
            alpha = [.5]* len(events_by_player[label][0::4]))

    ax.invert_yaxis()
    ax.yaxis.set_visible(False)
    ax.set_xlim(-50, (48 * 60) + 50)
    ax.set_xticks([0, 12 * 60, 24 * 60, 36 * 60, 48 * 60], ["", "", "", "", ""])

    ax.set_xticks([6 * 60, 18 * 60, 30 * 60, 42 * 60], minor=True)
    ax.set_xticklabels(["Q1", "Q2", "Q3", "Q4"], minor=True)

    ax.tick_params(axis="y", which="major", labelsize=LABLE_SIZE, pad=0, direction="in")
    ax.tick_params(axis="x", which="minor", labelsize=LABLE_SIZE, pad=0, direction="in")
    ax.grid(True, axis="x", color="darkgrey", linestyle="-", linewidth=1, zorder=0)
    ax.tick_params(axis="both", which="both", length=0)

def plot_3_MID(ax, scoreMargins, flipper):

    if flipper:
        scoreMargins = list(map(lambda x: -x, scoreMargins))
    _colors = list(map(lambda x: "red" if x < 0 else "lime", scoreMargins))
    ax.scatter(range(0, len(scoreMargins)), scoreMargins, color=_colors, s=4)
    ax.set_xlim(-10, (48 * 60) + 10)

    mx = abs(max(scoreMargins))
    mi = abs(min(scoreMargins))
    m = max(mx, mi)
    m = 5 - (m % 5) + m
    ax.set_yticks(range(-m, m + 5, 10), list(range(-m, m + 5, 10)))
    # axd[MD].set_xticks([6*60, 18*60, 30*60,42*60], minor=True)
    # axd[MD].set_xticklabels(['Q1','Q2','Q3','Q4'], minor=True)
    ax.set_xticks([0, 12 * 60, 24 * 60, 36 * 60, 48 * 60], ["", "", "", "", ""])
    ax.tick_params(axis="both", which="both", length=0, labelsize=LABLE_SIZE, pad=3)
    ax.grid(True, axis="both", color="darkgrey", linestyle="-", linewidth=1, zorder=0)
    # axd[MD].yaxis.set_visible(False)

    axr = ax.twinx()
    for s in ["top", "right", "bottom", "left"]:
        axr.spines[s].set_visible(False)

    axr.yaxis.set_visible(True)
    axr.tick_params(axis="both", which="both", length=0, labelsize=LABLE_SIZE, pad=3)
    axr.set_yticks(range(-m, m + 5, 10), list(range(-m, m + 5, 10)))
    axr.set_ylabel('TEAM +/-')
  
def get_score_margin(play_by_play):
    # create scoremargin for every second of the game all 14400 = 60 * 12 * 4
    # this is an issue when OT comes along  // TODO
    # score margin is 'TIE' otherwise +/- difference of score. TIE set to 0 for us
    # like most other data elements its None if it is not changed
    scoreMargins = [0]
    lastscoretime = 0
    lastscorevalue = 0

    z = play_by_play.scoremargin.dropna().index
    for i, v in play_by_play.loc[z].iterrows():
        scoremargin = v.scoremargin
        if scoremargin == "TIE":
            scoremargin = 0
        scoremargin = int(scoremargin)
        # if not flipper: scoremargin = -scoremargin
        now = v.sec
        scoreMargins.extend([lastscorevalue] * (now - lastscoretime - 1))
        scoreMargins.extend([scoremargin])
        lastscoretime = now
        lastscorevalue = scoremargin

    return scoreMargins

def get_title(game_data, boxscore):
    total_secs_playing_time = boxscore.sum_item("secs")
    t = str(timedelta(seconds=total_secs_playing_time)).split(":")

    debug_title = f"DEBUG {t[0]}:{t[1]}  {game_data.game_id}"
    title = f"{game_data.matchup_away} {int(game_data.pts_away)}-{int(game_data.pts_home)} {game_data.game_date[0:10]}"
    title = title + " " + debug_title
    return title

def plot3_prep(our_stints_by_date, play_by_play, scoreMargins):

    game = our_stints_by_date[0]
    boxscore = box_score(our_stints_by_date[1])

    players = list(game.keys())
    starters = []
    for player in players:
        if len(game[player]) > 0:
            if game[player][0][0] == ["IN", 1, "12:00"]:
                starters += [player]

    bench = list(set(players) - set(starters))
    players = starters + bench

    playTimesbyPlayer = {}
    events_by_player = {}

    for player in players:

        for i, stint in enumerate(game[player]):
            start = scoreMargins[stint[3]]
            stop = scoreMargins[stint[4]]
            boxscore.add_plus_minus(player, start, stop)

        def timespantoSecs(a):
            start = period_clock_seconds(a[0])
            return (int(start), int(a[1]))

        playTimesbyPlayer[player] = list(map(lambda x: timespantoSecs(x), game[player]))

        _events = []

        plays_for_player = play_by_play.query(
            f'player1_name == "{player}" or player2_name == "{player}" or player3_name == "{player}"'
        )

        for i, v in plays_for_player.iterrows():

            _ec, _es, _et, _ec2, _es2, _et2 = event_to_size_color_shape(player, v)
            if _ec != None:
                _events.extend([v.sec, _ec, _es, _et ])
            if _ec2 != None:
                _events.extend([v.sec, _ec2, _es2, _et2])

        events_by_player[player] = _events

    boxscore.summary()

    return boxscore, playTimesbyPlayer, events_by_player, players

def line_up_abbr(lineup_):
    # utility - takes CAPS from player names to make lineup name
    def _lu_small(name_):
        return re.sub("[^A-Z]", "", name_)

    l_key = list(map(lambda x: _lu_small(x), lineup_))
    l_key.sort()
    return "-".join(l_key)

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

    current_lineup = []  # collect players currently playing
    last_start = 0  # last time we started a stint

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
                print("---not found", _player, last_start, current_lineup)

    lups =  list(stints_by_lineup.keys())
    for line_up in lups:
        if sum(np.array(stints_by_lineup[line_up])[:, 1]) < 120:
            stints_by_lineup.pop(line_up)

    for line_up in stints_by_lineup:

        boxscore = box_score({})

        players_in_lineup = players_by_lineup[line_up]
        stints_in_lineup = stints_by_lineup[line_up]

        a_ = play_by_play["player1_name"].isin(players_in_lineup)
        b_ = play_by_play["player2_name"].isin(players_in_lineup)
        c_ = play_by_play["player3_name"].isin(players_in_lineup)

        def in_stint__(row):
            for stint in stints_in_lineup:
                if (row.sec > stint[0]) & (row.sec <= (stint[0] + stint[1])):
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
                print("WHAT")

        events_by_lineup[line_up] = events_for_lineup

        secs_total_this_lineup = sum(np.array(stints_in_lineup)[:, 1])
        print(line_up,secs_total_this_lineup)
        def sm(x): return scoreMargins[x[0]] - scoreMargins[x[0]] + scoreMargins[x[1]]

        scoreMargin_this_lineup = sum(
            list(map(lambda x: sm(x), stints_by_lineup[line_up]))
        )

        boxscore.stuff_bs(plays_this_stint_this_player, players_in_lineup)

        boxscore.summary()

        bs_rows, bs_columns, bs_data = boxscore.get_bs_data(["TEAM"], all=True)
        bs_data[0][bs_columns.index("secs")] = secs_total_this_lineup
        bs_data[0][bs_columns.index("+/-")] = scoreMargin_this_lineup
        bs_data_by_lineup[line_up] = bs_data[0]

    box_score_for_lineups = box_score({})
    l_players = list(bs_data_by_lineup.keys())
    box_score_for_lineups.add_players(l_players)
    for l_players in l_players:
        for index, item in enumerate(bs_columns):
            val = (
                bs_data_by_lineup[l_players][index]
                if item not in ["MIN", "3PT", "FG", "FT"]
                else 0
            )
            box_score_for_lineups.set_item(l_players, item, val)

    box_score_for_lineups.summary()

    # undo damage done by make_summary which works for 5 players
    secs = box_score_for_lineups.get_item("TEAM", "secs")
    box_score_for_lineups.set_item(
        "TEAM", "MIN", str(timedelta(seconds=int(secs)))[2:4])

    plus_minus = box_score_for_lineups.get_item("TEAM", "+/-")
    box_score_for_lineups.set_item("TEAM", "+/-", plus_minus * 5)

    return box_score_for_lineups, stints_by_lineup, events_by_lineup

def plot3(our_stints, game_data, HOME_TEAM, play_by_play, opponent_stints):
        # create an attached column with an index
    play_by_play["sec"] = play_by_play.apply(
        lambda row: period_clock_seconds(["", row.period, row.pctimestring]), axis=1
    )

    scoreMargins = get_score_margin(play_by_play)

    boxscore1, playTimesbyPlayer1, events_by_player1, players1 = plot3_prep(
        our_stints, play_by_play, scoreMargins
    )

    box_for_lineups, stints_by_lineup, events_by_lineup = plot3_lineup_prep(
        playTimesbyPlayer = playTimesbyPlayer1,
        play_by_play      = play_by_play,
        boxscore_         = our_stints[1],
        scoreMargins      = scoreMargins
    )

    # boxscore2, playTimesbyPlayer2, events_by_player2, players2 = \
    # plot3_prep(our_stints, play_by_play, scoreMargins)

    title = get_title(game_data, boxscore1)

    flipper = title[0:3] == HOME_TEAM

    boxscore1.plus_minus_flip(not flipper)
    # boxscore2.plus_minus_flip(flipper)

    plt.style.use("dark_background")

    E1 = None
    TL = "2"
    TR = "3"
    MD = "4"
    E2 = "5"
    BL = "6"
    BR = "7"
    E3 = None

    layout = [
        [TL, TL, TL, TL, TL, TL, TR, TR, TR, TR],
        [MD, MD, MD, MD, MD, MD, MD, MD, MD, E2],
        [BL, BL, BL, BL, BL, BL, BR, BR, BR, BR],
    ]

    figure, axd = plt.subplot_mosaic(
        layout,
        figsize=(10.0, 6.0),
    )
    figure.canvas.manager.set_window_title(title)

    axd[TL].sharey(axd[TR])
    axd[BL].sharey(axd[BR])

    plot3_stints(stints_by_lineup, axd[BL], events_by_lineup)
    plot3_boxscore(box_for_lineups, axd[BR], box_for_lineups.get_players()[0:-1])

    plot3_PBP_chart(playTimesbyPlayer1, axd[TL], events_by_player1)
    plot3_boxscore(boxscore1, axd[TR], players1)

    # plot3_boxscore(boxscore2, axd[BR], players2)
    # plot3_PBP_chart(playTimesbyPlayer2, axd[BL], events_by_player2)

    plot_3_MID(axd[MD], scoreMargins, flipper)

    for r in [E1, E2, E3, TL, TR, BL, BR, MD]:
        if r != None:
            for s in ["top", "right", "bottom", "left"]:
                axd[r].spines[s].set_visible(False)

    for r in [E1, E2, E3, TL, TR, BL, BR, MD]:
        if r != None:
            axd[r].title.set_visible(False)

    for r in [E1, E2, E3, TR, BR]:
        if r != None:
            axd[r].yaxis.set_visible(False)
            axd[r].xaxis.set_visible(False)

    # plt.tight_layout()
    plt.subplots_adjust(
        wspace=35, hspace=0.2, right=0.98, left=0.00, top=0.95, bottom=0.05
    )
    plt.show()

    plt.close("all")

def plot2(data):

    _data = data.filter(["play_by_play", "pts_home"])
    _data["play_by_play"] = _data["play_by_play"].apply(
        lambda x: 15 if x.shape[0] == 0 else x.shape[0]
    )

    #  convert the index to datetime
    #  reindex! so we get spaces on dates with no game
    _data.index = pd.DatetimeIndex(_data.index)
    _data = _data.reindex(pd.date_range(_data.index[0], _data.index[-1]), fill_value=15)
    _data.index = _data.index.strftime("%b %d")

    fig, ax = plt.subplots()

    for l in _data:
        ax.bar(_data.index, list(_data[l]), label=l)

    plt.xticks(rotation=90)
    ax.set_xticks(ax.get_xticks()[::7])
    ax.legend(loc=2, title="PBP Data", ncols=3)

    plt.show()
    return

def plot1(data):

    plus_home = ["ast_home", "stl_home", "blk_home", "tov_away"]
    minus_home = ["ast_away", "stl_away", "blk_away", "tov_home"]

    _mp = data.filter(minus_home + plus_home)
    for key in _mp.keys():
        if key in minus_home:
            _mp[key] = _mp[key] * -1

    #  convert the index to datetime
    #  reindex! so we get 0 on dates with no game
    _mp.index = pd.DatetimeIndex(_mp.index)
    _mp = _mp.reindex(pd.date_range(_mp.index[0], _mp.index[-1]), fill_value=0)
    _mp.index = _mp.index.strftime("%b-%d")

    ax = _mp.plot.bar(stacked=True)
    ax.set_xticks(ax.get_xticks()[::7])
    ax.set_ylabel("plus/minus")
    ax.set_title("Thunder")
    ax.legend(loc=2, title="", ncol=2)
    return
