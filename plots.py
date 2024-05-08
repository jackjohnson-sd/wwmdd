import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.path import Path
from matplotlib.textpath import TextToPath
from matplotlib.font_manager import FontProperties
from matplotlib import font_manager 
import matplotlib
from box_score import box_score
from json_settings import defaults

settings  = defaults()

stint_c     = settings.get('STINT_COLOR')       
bad_evnt    = settings.get('BAD_EVENT_COLOR')    
good_evnt   = settings.get('GOOD_EVENT_COLOR') 
grid_color  = settings.get('GRID_COLOR')
table_color = settings.get('TABLE_COLOR')


fp = FontProperties(family='sans-serif',size='xx-small')
fp.set_weight('light')

def get_marker(symbol):
    v, codes = TextToPath().get_text_path(fp, symbol)
    v = np.array(v)
    mean = np.mean([np.max(v,axis=0), np.min(v, axis=0)], axis=0)
    return Path(v-mean, codes, closed=False)

mrk = {
    'A': get_marker('A'),
    'D': get_marker('D'),
    'O': get_marker('O'),
    '1': get_marker('1'),
    '2': get_marker('2'),
    '3': get_marker('3'),
    'F': get_marker('F'),
    'B': get_marker('B'),
    'S': get_marker('S'),
    'T': get_marker('T'),
}

# print(matplotlib.get_data_path())

def is3(eventRecord):
    vis = eventRecord.homedescription
    hom = eventRecord.visitordescription
    return (str(vis) + str(hom)).find('3PT') != -1

def em_mi(_style, _color, _size, eventRecord, current_or_count):
    # helper to make 3PT makes a bigger shape on plots
    if _style == mrk['2'] and is3(eventRecord):
        _style = mrk['3']
    return _style, _color, _size    

def em_fg(_style, _color, _size, eventRecord, current_or_count):
    # helper to make 3PT makes a bigger shape on plots
    if _style == mrk['2'] and is3(eventRecord):
        _style = mrk['3']
    return _style, _color, _size    

def em_ft(_style, _color, _size, eventRecord, current_or_count):
    # differentiate made vs missed free throw by color
    if type(eventRecord.score) != type('a'): 
        _color= bad_evnt
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
    if is_or: _style = mrk['O']
    return _style, _color, _size

event_map = {
1: [ good_evnt, 30.0, mrk['2'],'FG',    good_evnt, 30.0, mrk['A'],'AST',  [1, 2], em_fg, 0.8,0.8],  # make, assist
2: [  bad_evnt, 30.0, mrk['2'],'MISS',  good_evnt, 30.0, mrk['B'],'BLK',  [1, 3], em_mi, 0.8,0.8],  # miss, block
3: [ good_evnt, 30.0, mrk['1'],'FT',    None, None, ',','',               [1],    em_ft, 0.8,0.8],  # free throw
4: [ good_evnt, 30.0, mrk['D'],'DREB',  None, None, ',','',               [1],    or_dr, 0.8,0.8],  # rebound
5: [ good_evnt, 30.0, mrk['S'],'STL',   bad_evnt,  30.0, mrk['T'],'TO',   [2, 1], None,  0.8,0.8],  # steal, turnover
6: [ bad_evnt,  30.0, mrk['F'],'PF',    None, None, 's','PF\'d',          [1, 2], None,  0.8,0.8],  # foul, fouled
8: [ stint_c,   15.0, 'o','SUB',        stint_c,  15.0, 'o','OUT',        [1, 2], None,  1.0,1.0],  # substitution
20:[ good_evnt, 30.0, mrk['O'],'OREB',  good_evnt, 30.0, mrk['3'],'3PT',  [1],    None,  0.8,0.8],
}

def event_legend():

    event_legend_map = [        # the order in which we show up in legend
        [20,1,1.5], [ 1,0,1.5], [3,0,1.5],    # 3PT  FG  FT 
        [ 2,0,1.5], [ 5,1,1.5], [6,0,1.5],    # MISS, TO, PF
        [ 1,1,1.5], [ 2,1,1.5], [5,0,1.5],    # ast ,blk,STL
        [ 4,0,1.5], [20,0,1.5], [8,0,2.0]     # dreb,oreb
    ]

    legend_elements = []
    
    for x in event_legend_map:
        e      = event_map[x[0]]
        offset = x[1] * 4
        l = Line2D([0], [0], 
                   lw                = 0, 
                   marker            = e[2 + offset], 
                   color             = e[    offset], 
                   label             = e[3 + offset], 
                   markerfacecolor   = e[    offset],  
                   markersize        = e[1 + offset]/8 * x[2])
        
        legend_elements.extend([l])

    legend_elements.extend([Line2D([0], [0], lw=1, color=stint_c, label=' STINT' )])
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
                        _size1  = _si * action[10]
                        _style1 = _st
                    else:   
                        _color2 = _co
                        _size2  = _si * action[11]
                        _style2 = _st

    # return c/si/st for both possible players
    return _color1, _size1, _style1, _color2, _size2, _style2,

def removeLower(str): 
    regex = "[a-z .-]"
    return (re.sub(regex, "", str))

def shorten_player_name(what, max_length):
    # if name longer than max turns 'firstname lastname' to 'first_intial.lastname'
    if len(what) < max_length: return what

    if ' ' in what:
        ret_v = what[0] + '. ' + what.split(' ')[1]
        if len(ret_v) > max_length:
            return removeLower(ret_v)

        return what[0] + '. ' + what.split(' ')[1]
    return what

LABLE_SIZE = 11
COLWIDTH = 0.09

def P3_boxscore(boxscore, ax, players):
    # comments here show up on mouseover

    bs_rows, bs_columns, bs_data = boxscore.get_bs_data(players +  [boxscore._team_name])

    tc = [[table_color] * len(bs_columns)] * len(bs_rows)
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
        # rowColours    = 'r',
        rowLoc        = 'left',
        colLabels     = bs_columns,
        # colColours    = 'r',
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
    # print(index, SCALEY, len(bs_rows))
    the_table.scale(0.92, SCALEY)
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(9)

    table_cells = the_table.properties()['children']
    for cell in table_cells: 
        cell.get_text().set_color(table_color)

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

M2OFFSET = settings.get('M2OFFSET')
M3OFFSET = settings.get('M3OFFSET')
MKR_WIDTH = settings.get('MKR_WIDTH')

def fitMarkers(y_, sec_, color_, size_, marker_, nplayers_):
    
    # The SUB markers go first, we don't want to move them
    # around so skip to first non-SUB. This means we write 
    # on top of them. Which is what we want
    try:
        nsubs_ = list(map(lambda x:x != stint_c,color_ ))
        first_no_sub_item = nsubs_.index(True)
    except Exception as err:
        first_no_sub_item = 0

    # we stack 3 if we have them, then stack 2
    idx_max = len(sec_)
    idx = first_no_sub_item

    while idx < idx_max:

        m = nplayers_ / 14

        # each marker takes this number of seconds
        OPEN_SPACE = MKR_WIDTH

        start_index = idx
        idx += 1

        n = 1
        
        # find first opening where we have space
        while idx < idx_max:
            aval_space = OPEN_SPACE * (int(n/3) + 1)
            space_since_we_started =  sec_[idx] - sec_[start_index]
            if space_since_we_started < aval_space:
                n += 1
                idx += 1
            else: break

        # print(f'n:{n} start:{start_index} now:{idx} {space_since_we_started} {aval_space}')

        # idx is next available slot
        # number of items we need to place
        n = idx - start_index     
        slot_offset = OPEN_SPACE
        slot_position = 0
        slot_index = start_index
        while n > 0:

            available_slot = sec_[start_index] + (slot_position * slot_offset)

            if n >= 3:          # place 3 1 on line 2 staddle the one

                y_[slot_index] += M3OFFSET * m
                y_[slot_index + 2] -= M3OFFSET * m

                sec_[slot_index + 1] = available_slot 
                sec_[slot_index    ] = available_slot 
                sec_[slot_index + 2] = available_slot
                
                n -= 3
                slot_index += 3
                slot_position += 1
 
            elif n == 2:          # place 2 to straddle the line
                
                y_[slot_index    ] += M2OFFSET * m
                y_[slot_index + 1] -= M2OFFSET * m
             
                sec_[slot_index    ] = available_slot
                sec_[slot_index + 1] = available_slot 
                
                n -= 2
                slot_index += 2
                slot_position += 1

            elif n == 1:               

                sec_[slot_index    ] = available_slot                
                n -= 1
                

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
                            color = stint_c, 
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

            evnt_cnt = int(len(events_by_player[_player])/4)
            
            y__ = [((nplyrs - i - 1) * 10)] * evnt_cnt
            sec__     = events_by_player[_player][0::4]
            color__   = events_by_player[_player][1::4]
            size__    = events_by_player[_player][2::4] 
            marker__  = events_by_player[_player][3::4] 
##############################################################################################
            fitMarkers(y__,sec__, color__, size__, marker__, nplyrs)

            scatter = mscatter(
                sec__, y__, c = color__, s = size__, m = marker__, 
                ax = ax2,
                zorder = Z_EVNT,
                # alpha = .7
                )

    ax.set_xlim(-50, (48 * 60) + 50)
    ax.set_xticks([0, 12 * 60, 24 * 60, 36 * 60, 48 * 60], ['', '', '', '', ''])
   
    ax.set_xticks([6 * 60, 18 * 60, 30 * 60, 42 * 60], minor = True)

    ax.xaxis.tick_top()  
    tls = ['Q1', 'Q2', 'Q3', 'Q4'] if x_labels == 'TOP' else ['', '', '', '']
    ax.set_xticklabels(tls, minor = True, color=table_color)

    ax.tick_params(axis='x', which='both', labelsize=9, pad=3, length=0)
    ax.tick_params(axis='y', which='both', labelsize=0, length=0, pad=0, direction='out')
    ax.grid(True, axis='x', color=grid_color, linestyle='-', linewidth=1.5, zorder= Z_GRID)
    
    for s in ['top', 'right', 'bottom', 'left']:
        ax3.spines[s].set_visible(False)
        ax2.spines[s].set_visible(False)

def P3_scoremargin(ax, _scoreMargins, flipper, _zorder):

    if flipper:
        _scoreMargins = list(map(lambda x: -x, _scoreMargins))
    
    c_minus = settings.get('PM_PLUS_COLOR')    
    c_plus  = settings.get('PM_MINUS_COLOR')   
    _colors = list(map(lambda x: c_minus if x < 0 else c_plus, _scoreMargins))

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

    gd = game_data.game_date[0:10].split('-')
    gds = f'{gd[1]}/{gd[2]}/{gd[0]}'
    title = f'{gds}   {game_data.matchup_away}   {int(game_data.pts_away)}-{int(game_data.pts_home)}   '
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
            if v.eventmsgtype == 8:
                _ec, _es, _et, _ec2, _es2, _et2 = event_to_size_color_shape(player, v, current_or_count,)
                if _ec != None:  _events.extend([v.sec, _ec, _es, _et ])
                if _ec2 != None: _events.extend([v.sec, _ec2, _es2, _et2])

        for i, v in plays_for_player.iterrows():
            if v.eventmsgtype != 8:
                _ec, _es, _et, _ec2, _es2, _et2 = event_to_size_color_shape(player, v, current_or_count,)
                if _ec != None:  _events.extend([v.sec, _ec, _es, _et ])
                if _ec2 != None: _events.extend([v.sec, _ec2, _es2, _et2])
#################################################################################
# 28 spacing non overlapping "B"s
        # if player == 'Josh Giddey':
        #     for i in range(0,28,4):
        #         _events[i + 0] = 120 + 12 * i/4
        #         _events[i + 1] = _events[21]
        #         _events[i + 2] = _events[22]
        #         _events[i + 3] = mrk['B']
        #         print(i,20 + 9 * i)
        #     _events = _events[0:28]
        # else: _events = []

##################################################################################
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

    plt.style.use(settings.get('PLOT_COLOR_STYLE'))

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
        _ad1_label = 'TOP'
        _ad2_label = None
    else :
        _ad1_ = (axd[BL],axd[BR])
        _ad2_ = (axd[TL],axd[TR])
        _ad2_label = 'TOP'
        _ad1_label = None

    if TEAM_1 == home_team:
        _ad2_flip = True
    else:
        _ad1_flip = True


    # print(f'tt:{top_team} bt:{bot_team} ht:{home_team} g1f:{_ad1_flip} g2f:{_ad2_flip}')
    P3_PBP_chart(playTimesbyPlayer1, _ad1_[0], events_by_player1, scoreMargins, 
                 flipper  = _ad1_flip, 
                 x_labels =_ad1_label)
    
    boxscore1.plus_minus_flip(_ad1_flip)
    P3_boxscore(boxscore1, _ad1_[1], players1)
    # axd[TR].sharey(axd[TL])

    P3_PBP_chart(playTimesbyPlayer2, _ad2_[0], events_by_player2, scoreMargins, 
                 flipper  = _ad2_flip, 
                 x_labels =_ad2_label)
    
    boxscore2.plus_minus_flip(_ad2_flip)
    P3_boxscore(boxscore2, _ad2_[1], players2)
    # axd[BR].sharey(axd[BL])

    axd[E1].set_title(title, y=0.4, pad=-1, fontsize=9, color=table_color)
    
    axd[E2].legend( 
        labelcolor = table_color,
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
