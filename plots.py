import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import re

from box_score import box_score


import numpy as np; np.random.seed(32)
from matplotlib.path import Path
from matplotlib.textpath import TextToPath
from matplotlib.font_manager import FontProperties
import matplotlib.pyplot as plt

# fp = FontProperties(fname=r"C:\Windows\Fonts\Font Awesome 5 Free-Solid-900.otf")
fp = FontProperties({'fontname':'Wingdings'})


# fig, ax = plt.subplots()

def get_marker(symbol):
    v, codes = TextToPath().get_text_path(fp, symbol)
    v = np.array(v)
    mean = np.mean([np.max(v,axis=0), np.min(v, axis=0)], axis=0)
    return Path(v-mean, codes, closed=False)

# x = np.random.randn(4,10)
# c = np.random.rand(10)
# s = np.random.randint(120,500, size=10)
# plt.scatter(*x[:2], s=s, c=c, marker=get_marker(symbols["cloud"]), 
#             edgecolors="none", linewidth=2)
# plt.scatter(*x[2:], s=s, c=c, marker=get_marker(symbols["fish"]), 
#             edgecolors="none", linewidth=2)   

aAa = get_marker('A')
aDa = get_marker('D')
aOa = get_marker('O') 
a1a = get_marker('1')
a2a = get_marker('2')
a3a = get_marker('3')
aFa = get_marker('F')
aBa = get_marker('B')
aSa = get_marker('S')
aTa = get_marker('T')

def is3(eventRecord):
    vis = eventRecord.homedescription
    hom = eventRecord.visitordescription
    return (str(vis) + str(hom)).find('3PT') != -1

def em_mi(_style, _color, _size, eventRecord, current_or_count):
    # helper to make 3PT makes a bigger shape on plots
    if _style == a2a and is3(eventRecord):
        _style = a3a
    return _style, _color, _size    

def em_fg(_style, _color, _size, eventRecord, current_or_count):
    # helper to make 3PT makes a bigger shape on plots
    if _style == a2a and is3(eventRecord):
        _style = a3a
    return _style, _color, _size    

def em_ft(_style, _color, _size, eventRecord, current_or_count):
    # differentiate made vs missed free throw by color
    if type(eventRecord.score) != type('a'): 
        _color= 'red'
    return _style, _color, _size
    
def or_dr(_style, _color, _size, eventRecord, current_or_count):
    
    s = str(eventRecord.visitordescription) + str(eventRecord.homedescription)
    or_count = re.search('Off:(.*) Def:', s).group(1)
    is_or = False
    try:
        is_or = current_or_count[eventRecord.player1_name] != or_count
    except Exception as err:
        is_or = or_count == 1
    current_or_count[eventRecord.player1_name] = or_count
    if is_or: _style = aOa
    return _style, _color, _size

ylo = 'darkgrey'; _1 = '$1$'; _2 = '$2$'; _3 = '$3$'  
ylo = 'darkgrey'; _1 = a1a; _2 = a2a; _3 = a3a  

event_map = {
    1: [ 'lime', 30.0, _2,'FG',      'lime', 30.0, aAa,'AST',     [1, 2], em_fg, 1.0], # make, assist
    2: [  'red', 30.0, _2,'MISS',    'lime', 30.0, aBa,'BLK',     [1, 3], em_mi, 1.0],  # miss, block
    3: [ 'lime', 30.0, _1,'FT',       None,   None, ',','',       [1],    em_ft, 1.0], # free throw
    4: [ 'lime', 30.0, aDa,'DREB',    None,   None, ',','',       [1],    or_dr, 1.0],  # rebound
    5: [ 'lime', 30.0, aSa,'STL',     'red',  30.0, aTa,'TO',     [2, 1], None,  1.0],  # steal, turnover
    6: [  'red', 30.0, aFa,'PF',      None,   None, 's','PF\'d',  [1, 2], None,  1.0],  # foul, fouled
    8: [    ylo, 15.0, 'o','SUB',     ylo,    15.0, 'o','OUT',    [1, 2], None,  1.0],  # substitution
    20:[ 'lime', 30.0, aOa,'OREB',    'lime', 30.0, _3,'3PT',     [1],    None,  1.0],
}


def event_legend():

    event_legend_map = [        # the order in which we show up in legend
        [20,1,1.5], [ 1,0,1.5], [3,0,1.5],    # 3PT  FG  FT 
        [ 2,0,1.5], [ 5,1,1.5], [6,0,1.5],    # MISS, TO, PF
        [ 1,1,1.5], [ 2,1,1.5], [5,0,1.5],    # ast ,blk,STL
        [ 4,0,1.5], [20,0,1.5], [8,0,2.0]     # dreb,oreb
    ]

    legend_elements = []
    # legend_elements.extend([Line2D([0], [0], lw=0, color='lime', marker='*', label='3PT', markerfacecolor='lime', markersize=7.5)])
    for x in event_legend_map:
        e = event_map[x[0]]
        offset = x[1] * 4
        l = Line2D([0], [0], 
                   lw = 0, 
                   marker = e[2+offset], 
                   color  = e[offset], 
                   label  = e[3+offset], 
                   markerfacecolor =e [offset],  
                   markersize = x[2] * e[1+offset]/8 )
        legend_elements.extend([l])

    legend_elements.extend([Line2D([0], [0], lw=1, color=ylo, label=' STINT' )])
    return legend_elements
            
def event_to_size_color_shape(player, eventRecord, current_or_count):

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
    # if eventRecord.eventmsgtype in [1,2,3,4]:                               ########
        # this is an event we want to report on
        action = event_map[eventRecord.eventmsgtype]

        # 1 or 2 players can be attached to this event
        for i, xx in enumerate(action[8]):
            index = i * 4  # for the moment color and size per event, 
            if player_names[xx - 1] in players:
                # its for us color and size for event
                _co = action[index]
                _si = action[index + 1]
                _st = action[index + 2]
                if _co != None:
                    # if we need help figuring this out call helper
                    if action[9] != None: 
                        _st,_co, _si = action[9](_st, _co, _si, eventRecord, current_or_count)
            
                    # first person return in xxx1 all others xxx2
                    _si *= action[10]
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

def P3_boxscore(boxscore, ax, players):
    # comments here show up on mouseover

    bs_rows, bs_columns, bs_data = boxscore.get_bs_data(players +  [boxscore._team_name])

    tc = [['black'] * len(bs_columns)] * len(bs_rows)
    trows = list(map(lambda x: shorten_player_name(x, 12), bs_rows))

    cws = [COLWIDTH] * len(bs_columns)
    cws[1] *= 1.4
    cws[2] *= 1.3
    cws[3] *= 1.4
    cws[4] *= 1.3

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
    
    _scale = [
        1.000,  1.000,  1.000,  1.000,  1.500, # 5,6,7,8,9  
        1.330,  1.192,  1.065,  0.970,  0.880, # 10,11,12,13,14  
        1.000]                                 # 15
    
    if len(bs_rows) < 5 : index = 0
    elif len(bs_rows) > 15: index = 10
    else: index = len(bs_rows) - 5
    SCALEY = _scale[index]
    # SCALEY =  13.2 / (len(bs_rows))
    print(index, SCALEY, len(bs_rows))
    the_table.scale(0.92, SCALEY)
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(9)

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

def P3_PBP_chart(playTimesbyPlayer, ax, events_by_player, scoreMargins, flipper, x_labels = 'TOP'):

    Z_GRID = 0  # bottom
    Z_SCRM = 10  
    Z_HBAR = 20
    Z_EVNT = 30

    ax3 = ax.twinx()
    P3_scoremargin(ax3, scoreMargins, flipper, Z_SCRM)

    _players = list(playTimesbyPlayer.keys())

    for i, _player in enumerate(_players):

        data = playTimesbyPlayer[_player]
        if len(data) > 0:
            starts = list(map(lambda x: x[0], data))
            widths = list(map(lambda x: x[1], data))
            rects = ax.barh(_player, widths, 
                            left = starts, 
                            color = ylo, 
                            height = 0.05, 
                            zorder = Z_HBAR)
            
    ax.invert_yaxis()
    ax.yaxis.set_visible(False)
    
    ymin, ymax = ax.get_ylim()

    ax2 = ax.twinx() 
    ax2.set_ylim(ymax * 10, ymin * 10)
    ax2.tick_params(axis='both', which='both', labelsize=0, pad=0, direction='in')
    ax2.yaxis.set_visible(False)
    
    nplyrs = len(_players) 

    for i, _player in enumerate(_players):

        data = playTimesbyPlayer[_player]
        if len(data) > 0:

            evnt_cnt = len(events_by_player[_player][0::4])
            
            y__ = [((nplyrs - i - 1) * 10)] * evnt_cnt
            sec__     = events_by_player[_player][0::4]
            color__   = events_by_player[_player][1::4]
            size__    = events_by_player[_player][2::4] 
            marker__  = events_by_player[_player][3::4] 

            for i in range(0,evnt_cnt-1):
                if sec__[i+1] - sec__[i] < 20:
                    if color__[i] != ylo and color__[i+1] != ylo:
                        y__[i] += 2.6
                        y__[i+1] -= 2.6 

            scatter = mscatter(
                sec__, y__, c = color__, s = size__, m = marker__, 
                ax = ax2,
                zorder = Z_EVNT,
                # alpha = .7
                )

    ax.set_xlim(-50, (48 * 60) + 50)
    ax.set_xticks([0, 12 * 60, 24 * 60, 36 * 60, 48 * 60], ['', '', '', '', ''])
   
    ax.set_xticks([6 * 60, 18 * 60, 30 * 60, 42 * 60], minor = True)
    ax.set_xticklabels(['Q1', 'Q2', 'Q3', 'Q4'], minor = True)
    
    if x_labels == 'TOP': ax.xaxis.tick_top()
    _lsize = 0 if x_labels == 'NONE' else 9

    ax.tick_params(axis='x', which='both', labelsize=_lsize, pad=3, length=0)
    ax.tick_params(axis='y', which='both', labelsize=0, length=0, pad=0, direction='out')
    ax.grid(True, axis='x', color='dimgrey', linestyle='-', linewidth=1.5, zorder= Z_GRID)
    
    for s in ['top', 'right', 'bottom', 'left']:
        ax3.spines[s].set_visible(False)
        ax2.spines[s].set_visible(False)

def P3_scoremargin(ax, _scoreMargins, flipper, _zorder):

    if flipper:
        _scoreMargins = list(map(lambda x: -x, _scoreMargins))
    _colors = list(map(lambda x: 'maroon' if x < 0 else 'darkgreen', _scoreMargins))

    ax.scatter(range(0, len(_scoreMargins)), _scoreMargins, color=_colors, s=1, zorder=_zorder)
    ax.set_xlim(0, (48 * 60) - 1)

    import math
    mx = abs(max(_scoreMargins))
    mi = abs(min(_scoreMargins))
    m = max(mx, mi)
    m = int(math.ceil(m/10) * 10)
    r = list(range(-m, m+10, 10))

    ax.set_yticks(r, r)
    ax.set_xticks([0, 12 * 60, 24 * 60, 36 * 60, 48 * 60], ['', '', '', '', ''])
    ax.yaxis.set_visible(False)

def make_scoremargin(play_by_play):
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
    
        now = v.sec
        scoreMargins.extend([lastscorevalue] * (now - lastscoretime - 1))
        scoreMargins.extend([scoremargin])
        lastscoretime = now
        lastscorevalue = scoremargin

    return scoreMargins

def get_title(game_data, boxscore):
    # total_secs_playing_time = boxscore.sum_item('secs')
    # t = str(timedelta(seconds=total_secs_playing_time)).split(':')

    debug_title = f'{game_data.game_id}'
    # debug_title = f'DEBUG {t[0]}:{t[1]}  {game_data.game_id}'
    # 
    w_home = game_data.wl_home
    team_home = game_data.team_abbreviation_home
    team_away = game_data.team_abbreviation_away

    if w_home == 'W':
        top_team = team_home
        bot_team = team_away
    else:
        top_team = team_away
        bot_team = team_home

    title = f'{game_data.matchup_away} {int(game_data.pts_away)}-{int(game_data.pts_home)} {game_data.game_date[0:10]}'
    title = title + '  ' + debug_title
    return title, top_team, bot_team, team_home

def P3_prep(our_stints_by_date, play_by_play, scoreMargins, team = None, opponent = False):

    game = our_stints_by_date[0]
    boxscore = box_score(our_stints_by_date[1])

    players = list(game.keys())
    starters = []
    for player in players:
        if len(game[player]) > 0:
            if game[player][0][0][3] == 0:
                starters += [player]

    if opponent:
        teams = set(play_by_play.player1_team_abbreviation.dropna().to_list()[0:10])
        teams.remove(team)
        team = list(teams)[0]
    
    boxscore.set_team_name(team)

    bench = list(set(players) - set(starters))
    players = starters + bench

    playTimesbyPlayer = {}
    events_by_player = {}

    # def dd(pl,st,se,stv,sev):
    #     print(f'{pl} st:{st} se:{se} stv:{stv} ste:{sev} PM:{sev-stv}')

    current_or_count = {}    

    for player in players:
            
        for i, stint in enumerate(game[player]):
            start = scoreMargins[stint[3]]
            stop = scoreMargins[stint[4]]
            # dd(player,stint[3],stint[4],start,stop)
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

            _ec, _es, _et, _ec2, _es2, _et2 = event_to_size_color_shape(player, v, current_or_count)
            if _ec != None:
                _events.extend([v.sec, _ec, _es, _et ])
            if _ec2 != None:
                _events.extend([v.sec, _ec2, _es2, _et2])

        events_by_player[player] = _events

        try:
            boxscore.set_item(player,'ORS', int(current_or_count[player]))
        except:
            pass
            # boxscore.set_item(player,'ORS', 0)

    boxscore.summary()

    return boxscore, playTimesbyPlayer, events_by_player, players

def p3_layout(title):
    
    E1 = '1'
    TL = '2'
    TR = '3'
    MD = None
    E2 = '5'
    BL = '6'
    BR = '7'
    E3 = None
    
    E1,TL,TR,MD,E2,BL,BR,E3

    layout = [
        [TL, TL, TL, TL, TL, TL, TR, TR, TR, TR],
        [TL, TL, TL, TL, TL, TL, TR, TR, TR, TR],
        [TL, TL, TL, TL, TL, TL, TR, TR, TR, TR],
        [E2, E2, E2, E2, E2, E2, E1, E1, E1, E1],
        [BL, BL, BL, BL, BL, BL, BR, BR, BR, BR],
        [BL, BL, BL, BL, BL, BL, BR, BR, BR, BR],
        [BL, BL, BL, BL, BL, BL, BR, BR, BR, BR],
    ]

    figure, axd = plt.subplot_mosaic(layout, figsize = (10.0, 6.0) )
    figure.canvas.manager.set_window_title(title)

    return axd, E1,TL,TR,MD,E2,BL,BR,E3

def plot3(our_stints, game_data, TEAM_1, play_by_play, opponent_stints):

    scoreMargins = make_scoremargin(play_by_play)

    boxscore1, playTimesbyPlayer1, events_by_player1, players1 = \
    P3_prep(our_stints, play_by_play, scoreMargins, team=TEAM_1)

    boxscore2, playTimesbyPlayer2, events_by_player2, players2 = \
    P3_prep(opponent_stints, play_by_play, scoreMargins, team=TEAM_1, opponent=True)

    title, top_team, bot_team, home_team = get_title(game_data, boxscore1)

    plt.style.use('dark_background')

    axd,E1,TL,TR,MD,E2,BL,BR,E3= p3_layout(title)

    # winning team goes on top 
    # TEAM1 is group1 data, opponennt is group2 data
    # away team gets the plus/minus flipped
    # plus minus is from the home team perspective

    _ad1_flip = False
    _ad2_flip = False
    
    if top_team == TEAM_1:
        _ad1_ = (axd[TL],axd[TR])
        _ad2_ = (axd[BL],axd[BR])
    else :
        _ad2_ = (axd[TL],axd[TR])
        _ad1_ = (axd[BL],axd[BR])

    if TEAM_1 == home_team:
        _ad2_flip = True
    else:
        _ad1_flip = True


    # print(f'tt:{top_team} bt:{bot_team} ht:{home_team} g1f:{_ad1_flip} g2f:{_ad2_flip}')
    P3_PBP_chart(playTimesbyPlayer1, _ad1_[0], events_by_player1, scoreMargins, flipper = _ad1_flip)
    boxscore1.plus_minus_flip(_ad1_flip)
    P3_boxscore(boxscore1, _ad1_[1], players1)
    # axd[TR].sharey(axd[TL])

    P3_PBP_chart(playTimesbyPlayer2, _ad2_[0], events_by_player2, scoreMargins, flipper = _ad2_flip, x_labels='NONE')
    boxscore2.plus_minus_flip(_ad2_flip)
    P3_boxscore(boxscore2, _ad2_[1], players2)
    # axd[BR].sharey(axd[BL])

    axd[E1].set_title(title, y=0.4, pad=-1, fontsize=9)
    
    axd[E2].legend( 
        fontsize ='small',
        markerfirst=True,
        ncols = 5,
        loc = 'center', 
        frameon = False,
        handletextpad= 0.10,
        handles = event_legend())

    # P3_stints(stints_by_lineup, axd[BL], events_by_lineup)
    # P3_boxscore(box_for_lineups, axd[BR], box_for_lineups.get_players()[0:-1])

    for r in [TL, TR, BL, BR, E1, E2, E3, MD]:
        if r != None:
            for s in ['top', 'right', 'bottom', 'left']:
                axd[r].spines[s].set_visible(False)

    for r in [E2, E3, TL, TR, BL, BR, MD]:
        if r != None:
            axd[r].title.set_visible(False)

    for r in [E1, E2, E3, TR, BR]:
        if r != None:
            axd[r].yaxis.set_visible(False)
            axd[r].xaxis.set_visible(False)
    
    plt.subplots_adjust(
        wspace=35, hspace=0.4, right=0.98, left=0.01, top=0.95, bottom=0.08
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
