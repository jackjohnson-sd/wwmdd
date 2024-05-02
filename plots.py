import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from datetime import timedelta
from box_score import box_score, PM
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
    1: [ 'lime', 50.0, '*',    'aqua', 25.0, '^',   [1, 2], em_f1], # make, assist
    2: [  'red', 20.0, 'v',    'lime', 25.0, '^',   [1, 3], None],  # miss, block
    3: [ 'lime', 30.0, 'p',      None, None, ',',   [1],    em_f2], # free throw
    4: [ 'lime', 25.0, 'o',      None, None, ',',   [1],    None],  # rebound
    5: [ 'lime', 25.0, 'd',    'pink', 25.0, 'v',   [1],    None],  # steal, turnover
    6: [  'red', 20.0, 'D',    'lime', 10.0, 's',   [1, 2], None],  # foul, fouled
    8: ['wheat', 10.0, 'o',   'wheat', 10.0, 'o',   [1, 2], None],  # substitution
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

    # return c/si/st for both possible players
    return _color1, _size1, _style1, _color2, _size2, _style2,

def shorten_player_name(what, max_length):
    # if name longer than max turns 'firstname lastname' to 'first_intial.lastname'
    if len(what) < max_length: return what
    if ' ' in what:
        return what[0] + '. ' + what.split(' ')[1]
    return what

LABLE_SIZE = 11
COLWIDTH = 0.09

def plot3_boxscore(boxscore, ax, players):
    # comments here show up on mouseover

    bs_rows, bs_columns, bs_data = boxscore.get_bs_data(players + ['TEAM'])

    tc = [['black'] * len(bs_columns)] * len(bs_rows)
    trows = list(map(lambda x: shorten_player_name(x, 12), bs_rows))

    cws = [COLWIDTH] * len(bs_columns)
    cws[1] *= 1.4
    cws[2] *= 1.4
    cws[3] *= 1.4

    the_table = ax.table(
        cellText      = bs_data,
        cellColours   = tc,
        cellLoc       = 'center',
        colWidths     = cws,  # [COLWIDTH]*len(bs_columns),
        rowLabels     = trows,
        # rowColours='k',
        rowLoc        = 'right',
        colLabels     = bs_columns,
        # colColours='k',
        colLoc        = 'center',
        loc           = 'center',
        edges         = '', 
    )

    SCALEY =  13 / (len(bs_rows))
    print(SCALEY, len(bs_rows))
    the_table.scale(0.92, SCALEY)
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(9.3)

    from matplotlib.font_manager import FontProperties
    for (row, col), cell in the_table.get_celld().items():
        if (col == -1):
            cell.set_text_props(fontproperties=FontProperties(size=9.5))
   
def mscatter(x,y,ax=None, m=None, **kw):
    import matplotlib.markers as mmarkers
    if not ax: ax=plt.gca()
    sc = ax.scatter(x, y, **kw)
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

Z_GRID = 0  # bottom
Z_SCRM = 1  
Z_HBAR = 2
Z_EVNT = 3

def plot3_PBP_chart(playTimesbyPlayer, ax, events_by_player, scoreMargins, flipper, _zorder = 0):

    _players = list(playTimesbyPlayer.keys())

    ax3 = ax.twinx()
    plot_3_scoremargin(ax3,scoreMargins,flipper, Z_SCRM)

    for i, _player in enumerate(_players):

        data = playTimesbyPlayer[_player]
        if len(data) > 0:
            starts = list(map(lambda x: x[0], data))
            widths = list(map(lambda x: x[1], data))
            rects = ax.barh(_player, widths, 
                            left = starts, 
                            color = 'saddlebrown', 
                            height = 0.05, 
                            zorder = Z_HBAR)
            
    ax.invert_yaxis()
    ax.yaxis.set_visible(False)
    ymin, ymax = ax.get_ylim()
    ax2 = ax.twinx() 

    nplyrs = len(_players) 
    ax2.set_ylim(ymax * 10, ymin * 10)

    ax2.tick_params(axis='both', which='both', labelsize=0, pad=0, direction='in')
    ax2.yaxis.set_visible(False)
    
    for i, _player in enumerate(_players):

        data = playTimesbyPlayer[_player]
        if len(data) > 0:

            evnt_cnt = len(events_by_player[_player][0::4])
            
            n = ((nplyrs - i-1) * 10)
            scatter = mscatter(
                events_by_player[_player][0::4],
                [n] * evnt_cnt,
                c  = events_by_player[_player][1::4], 
                s  = events_by_player[_player][2::4], 
                m  = events_by_player[_player][3::4], 
                ax = ax2,
                zorder = Z_EVNT,
                alpha = .7
                )
    
    ax.set_xlim(-50, (48 * 60) + 50)
    ax.set_xticks([0, 12 * 60, 24 * 60, 36 * 60, 48 * 60], ['', '', '', '', ''])
   
    ax.set_xticks([6 * 60, 18 * 60, 30 * 60, 42 * 60], minor = True)
    ax.set_xticklabels(['Q1', 'Q2', 'Q3', 'Q4'], minor = True)

    ax.tick_params(axis='x', which='both', labelsize=9, pad=13, length=0)
    ax.tick_params(axis='y', which='both', labelsize=0, length=0, pad=0, direction='out')
    ax.grid(True, axis='x', color='dimgrey', linestyle='-', linewidth=1, zorder= Z_GRID)
    
    for s in ['top', 'right', 'bottom', 'left']:
        ax3.spines[s].set_visible(False)
        ax2.spines[s].set_visible(False)

def plot_3_scoremargin(ax, scoreMargins, flipper, _zorder):

    if flipper:
        scoreMargins = list(map(lambda x: -x, scoreMargins))
    _colors = list(map(lambda x: 'maroon' if x < 0 else 'darkgreen', scoreMargins))

    ax.scatter(range(0, len(scoreMargins)), scoreMargins, color=_colors, s=1, zorder=_zorder)
    ax.set_xlim(0, (48 * 60) - 1)

    import math
    mx = abs(max(scoreMargins))
    mi = abs(min(scoreMargins))
    m = max(mx, mi)
    m = int(math.ceil(m/10) * 10)
    r = list(range(-m, m+10, 10))

    ax.set_yticks(r, r)
    ax.set_xticks([0, 12 * 60, 24 * 60, 36 * 60, 48 * 60], ['', '', '', '', ''])
    ax.yaxis.set_visible(False)

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
        if scoremargin == 'TIE':
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
    total_secs_playing_time = boxscore.sum_item('secs')
    t = str(timedelta(seconds=total_secs_playing_time)).split(':')

    debug_title = f'DEBUG {t[0]}:{t[1]}  {game_data.game_id}'
    title = f'{game_data.matchup_away} {int(game_data.pts_away)}-{int(game_data.pts_home)} {game_data.game_date[0:10]}'
    title = title + ' ' + debug_title
    return title

def plot3_prep(our_stints_by_date, play_by_play, scoreMargins):

    game = our_stints_by_date[0]
    boxscore = box_score(our_stints_by_date[1])

    players = list(game.keys())
    starters = []
    for player in players:
        if len(game[player]) > 0:
            if game[player][0][0][3] == 0:
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

        def timespantoSecs(a): return (a[0][3], a[1])
        playTimesbyPlayer[player] = list(map(lambda x: timespantoSecs(x), game[player]))

        _events = []

        a_ = play_by_play['player1_name'] == player
        b_ = play_by_play['player2_name'] == player
        c_ = play_by_play['player3_name'] == player

        ours = (a_ | b_ | c_)
        plays_for_player = play_by_play[ours]

        for i, v in plays_for_player.iterrows():

            _ec, _es, _et, _ec2, _es2, _et2 = event_to_size_color_shape(player, v)
            if _ec != None:
                _events.extend([v.sec, _ec, _es, _et ])
            if _ec2 != None:
                _events.extend([v.sec, _ec2, _es2, _et2])

        events_by_player[player] = _events

    boxscore.summary()

    return boxscore, playTimesbyPlayer, events_by_player, players

def plot3(our_stints, game_data, HOME_TEAM, play_by_play, opponent_stints):

    scoreMargins = get_score_margin(play_by_play)

    boxscore1, playTimesbyPlayer1, events_by_player1, players1 = plot3_prep(
        our_stints, play_by_play, scoreMargins
    )

    # box_for_lineups, stints_by_lineup, events_by_lineup = plot3_lineup_prep(
    #     playTimesbyPlayer = playTimesbyPlayer1,
    #     play_by_play      = play_by_play,
    #     boxscore_         = our_stints[1],
    #     scoreMargins      = scoreMargins
    # )

    boxscore2, playTimesbyPlayer2, events_by_player2, players2 = \
    plot3_prep(opponent_stints, play_by_play, scoreMargins)

    title = get_title(game_data, boxscore1)

    flipper = title[0:3] == HOME_TEAM

    boxscore1.plus_minus_flip(not flipper)
    boxscore2.plus_minus_flip(flipper)

    plt.style.use('dark_background')

    E1 = None
    TL = '2'
    TR = '3'
    MD = None
    E2 = '5'
    BL = '6'
    BR = '7'
    E3 = None

    layout = [
        [TL, TL, TL, TL, TL, TL, TR, TR, TR, TR],
        [TL, TL, TL, TL, TL, TL, TR, TR, TR, TR],
        [TL, TL, TL, TL, TL, TL, TR, TR, TR, TR],
        [E2, E2, E2, E2, E2, E2, E2, E2, E2, E2],
        [BL, BL, BL, BL, BL, BL, BR, BR, BR, BR],
        [BL, BL, BL, BL, BL, BL, BR, BR, BR, BR],
        [BL, BL, BL, BL, BL, BL, BR, BR, BR, BR],
    ]

    figure, axd = plt.subplot_mosaic(layout, figsize = (10.0, 6.0) )
    figure.canvas.manager.set_window_title(title)

    plot3_boxscore(boxscore1, axd[TR], players1)
    plot3_PBP_chart(playTimesbyPlayer1, axd[TL], events_by_player1, scoreMargins, flipper)
    axd[TR].sharey(axd[TL])

    # plot_3_MID(axd[MD], scoreMargins, flipper)

    plot3_PBP_chart(playTimesbyPlayer2, axd[BL], events_by_player2, scoreMargins, not flipper)
    plot3_boxscore(boxscore2, axd[BR], players2)
    axd[BR].sharey(axd[BL])

    # plot3_stints(stints_by_lineup, axd[BL], events_by_lineup)
    # plot3_boxscore(box_for_lineups, axd[BR], box_for_lineups.get_players()[0:-1])

    for r in [TL, TR, BL, BR, E1, E2, E3, MD]:
        if r != None:
            for s in ['top', 'right', 'bottom', 'left']:
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
        wspace=35, hspace=0.3, right=0.98, left=0.01, top=0.95, bottom=0.08
    )
    plt.show()

    plt.close('all')

def plot2(data):

    _data = data.filter(['play_by_play', 'pts_home'])
    _data['play_by_play'] = _data['play_by_play'].apply(
        lambda x: 15 if x.shape[0] == 0 else x.shape[0]
    )

    #  convert the index to datetime
    #  reindex! so we get spaces on dates with no game
    _data.index = pd.DatetimeIndex(_data.index)
    _data = _data.reindex(pd.date_range(_data.index[0], _data.index[-1]), fill_value=15)
    _data.index = _data.index.strftime('%b %d')

    fig, ax = plt.subplots()

    for l in _data:
        ax.bar(_data.index, list(_data[l]), label=l)

    plt.xticks(rotation=90)
    ax.set_xticks(ax.get_xticks()[::7])
    ax.legend(loc=2, title='PBP Data', ncols=3)

    plt.show()
    return

def plot1(data):

    plus_home = ['ast_home', 'stl_home', 'blk_home', 'tov_away']
    minus_home = ['ast_away', 'stl_away', 'blk_away', 'tov_home']

    _mp = data.filter(minus_home + plus_home)
    for key in _mp.keys():
        if key in minus_home:
            _mp[key] = _mp[key] * -1

    #  convert the index to datetime
    #  reindex! so we get 0 on dates with no game
    _mp.index = pd.DatetimeIndex(_mp.index)
    _mp = _mp.reindex(pd.date_range(_mp.index[0], _mp.index[-1]), fill_value=0)
    _mp.index = _mp.index.strftime('%b-%d')

    ax = _mp.plot.bar(stacked=True)
    ax.set_xticks(ax.get_xticks()[::7])
    ax.set_ylabel('plus/minus')
    ax.set_title('Thunder')
    ax.legend(loc=2, title='', ncol=2)
    return
