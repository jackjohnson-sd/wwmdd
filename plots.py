import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.path import Path
from matplotlib.textpath import TextToPath
from matplotlib.font_manager import FontProperties
import matplotlib
from box_score import box_score,PM

from play_by_play import dump_pbp
from settings import defaults
from nba_colors import get_color, dimmer 

settings  = defaults()

DBG_A       = settings.get('dbga')
DBG_B       = settings.get('dbgb')
DBG_C       = settings.get('dbgc')
DB_NAME     = settings.get('SOURCE')
SAVE_GAME_AS_CSV    = settings.get('SAVE_GAME_AS_CSV')
SAVE_GAME_DIR = settings.get('SAVE_GAME_DIR')

STINT_C     = settings.get('STINT_COLOR')       
BAD_EVNT    = settings.get('BAD_EVENT_COLOR')    
GOOD_EVNT   = settings.get('GOOD_EVENT_COLOR') 
GRID_C      = settings.get('GRID_COLOR')
TABLE_C     = settings.get('TABLE_COLOR')
TABLE_COLOR      = settings.get('TABLE_COLOR')
STINT_COLOR_PLUS = settings.get('STINT_COLOR_PLUS')
STINT_COLOR_MINUS = settings.get('STINT_COLOR_MINUS')

BOX_COL_COLOR = settings.get('BOX_COL_COLOR')
BOX_COL_COLOR_ALT = settings.get('BOX_COL_COLOR_ALT')

M2OFFSET       = settings.get('MARKER_2_STACK_OFFSET')    # vertical offset for 2 markers at one place
M3OFFSET       = settings.get('MARKER_3_STACK_OFFSET')    # vertical offset for 3 markers at one place
MKR_WIDTH      = settings.get('MARKER_WIDTH')             # used to determine if markes will overlap
MRK_FONTSCALE  = settings.get('MARKER_FONTSCALE')
MRK_FONTWEIGHT = settings.get('MARKER_FONTWEIGHT')
GRID_LINEWIDTH   = settings.get('GRID_linewidth')

fp = FontProperties(family='sans-serif',size='xx-small')
fp.set_weight('light')

def get_marker(symbol):
    v, codes = TextToPath().get_text_path(fp, symbol)
    v = np.array(v)
    mean = np.mean([np.max(v,axis=0), np.min(v, axis=0)], axis=0)
    return Path(v-mean, codes, closed=False)

mrk = {
    # 'A': get_marker('A'),
    'A': ['A'],
    'D': ['D'],
    'O': ['O'],
    '1': ['1'],
    '2': ['2'],
    '3': ['3'],
    'F': ['F'],
    'B': ['B'],
    'S': ['S'],
    'T': ['T'],
}

# print(matplotlib.get_data_path())

def is3(eventRecord):
    vis = eventRecord.homedescription
    hom = eventRecord.visitordescription
    return (str(vis) + str(hom)).find('3PT') != -1

def em_mi(_style, _color, _size, eventRecord, current_oreb_count, scoreMargins):
    # helper to make 3PT makes a bigger shape on plots
    if _style == mrk['2'] and is3(eventRecord):
        _style = mrk['3']
    return _style, _color, _size    

def em_fg(_style, _color, _size, eventRecord, current_oreb_count, scoreMargins):
    # helper to make 3PT makes a bigger shape on plots
    if _style == mrk['2'] and is3(eventRecord):
        _style = mrk['3']
    return _style, _color, _size    

def em_ft(_style, _color, _size, eventRecord, current_oreb_count, scoreMargins):
    # differentiate made vs missed free throw by color
    if type(eventRecord.score) != type('a'): 
        _color= BAD_EVNT
    return _style, _color, _size

def em_st(_style, _color, _size, eventRecord, current_oreb_count, scoreMargins):
    return _style, _color, _size
        
def or_dr(_style, _color, _size, eventRecord, current_oreb_count, scoreMargins):
    
    try:
        s = str(eventRecord.visitordescription) 
        s2 = str(eventRecord.homedescription)
        if s != s2: s += s2
        or_count = re.search('Off:(.*) Def:', s).group(1)
        is_or = False
        _player1 = eventRecord.player1_name
        if _player1 not in current_oreb_count.keys():
            current_oreb_count[_player1]  = 0 

        is_or = current_oreb_count[_player1] != or_count
        current_oreb_count[_player1] = or_count
        if is_or: _style = mrk['O']
    except Exception as err:
        print(err)

    return _style, _color, _size

event_map = {
1: [ GOOD_EVNT, 30.0, mrk['2'],'FG',    GOOD_EVNT, 30.0, mrk['A'],'AST',  [1, 2], em_fg, 0.8,0.8],  # make, assist
2: [  BAD_EVNT, 30.0, mrk['2'],'MISS',  GOOD_EVNT, 30.0, mrk['B'],'BLK',  [1, 3], em_mi, 0.8,0.8],  # miss, block
3: [ GOOD_EVNT, 30.0, mrk['1'],'FT',    None, None, ',','',               [1],    em_ft, 0.8,0.8],  # free throw
4: [ GOOD_EVNT, 30.0, mrk['D'],'DREB',  None, None, ',','',               [1],    or_dr, 0.8,0.8],  # rebound
5: [ GOOD_EVNT, 30.0, mrk['S'],'STL',   BAD_EVNT,  30.0, mrk['T'],'TO',   [2, 1], None,  0.8,0.8],  # steal, turnover
6: [ BAD_EVNT,  30.0, mrk['F'],'PF',    None, None, 's','PF\'d',          [1, 2], None,  0.8,0.8],  # foul, fouled
8: [ STINT_C,   15.0, 'o','SUB',        STINT_C,  15.0, 'o','OUT',        [1, 2], None,  1.0,1.0],  # substitution
20:[ GOOD_EVNT, 30.0, mrk['O'],'OREB',  GOOD_EVNT, 30.0, mrk['3'],'3PT',  [1],    None,  0.8,0.8],  # for legend
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
        if type(e[2 + offset]) == type([]):
            marker_ = '$'+e[2 + offset][0] +'$'
        else: 
            marker_ = e[2 + offset]
        l = Line2D([0], [0], 
                lw                = 0, 
                marker            = marker_, 
                color             = e[    offset], 
                label             = e[3 + offset], 
                markerfacecolor   = e[    offset],  
                markersize        = e[1 + offset]/8 * x[2])
    
        legend_elements.extend([l])

    legend_elements.extend([Line2D([0], [0], lw=1, color=STINT_C, label=' STINT' )])
    return legend_elements
            
def event_to_size_color_shape(player, eventRecord, current_oreb_count, scoreMargins):

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
                        _st,_co, _si = action[9](_st, _co, _si, eventRecord, current_oreb_count,scoreMargins)
            
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

def stack_markers(yy_, sec_, color_, nplayers_):
    
    # The SUB markers go first, we don't want to move them
    # around so skip to first non-SUB. This means we write 
    # on top of them. Which is what we want
    try:
        nsubs_ = list(map(lambda x:x != STINT_C,color_ ))
        first_no_sub_item = nsubs_.index(True)
    except Exception as err:
        first_no_sub_item = 0

    # we stack 3 if we have them, then stack 2
    idx_max = len(sec_)
    idx = first_no_sub_item

    # a hopeless attempt to scale size based # players
    # more players means less space for our stack of 3
    m = nplayers_ / 14

    # each marker takes this number of seconds to display
    open_space = MKR_WIDTH

    while idx < idx_max:

        start_index = idx
        idx += 1
        markers_to_place = 1
        
        # find first opening where we have space
        while idx < idx_max:
            needed_space = open_space * (int(markers_to_place/3) + 1)
            space_since_we_started =  sec_[idx] - sec_[start_index]
            if space_since_we_started < needed_space:
                markers_to_place += 1
                idx += 1
            else: break

        # idx is next available slot
        # markers_to_place = number of items we need to place
        
        slot_position = 0
        slot_index = start_index

        while markers_to_place > 0:

            available_slot = sec_[start_index] + (slot_position * open_space)

            if markers_to_place >= 3:          # place 3 1 on line 2 staddle the one

                yy_[slot_index] += M3OFFSET * m
                yy_[slot_index + 2] -= M3OFFSET * m

                sec_[slot_index + 1] = available_slot 
                sec_[slot_index    ] = available_slot 
                sec_[slot_index + 2] = available_slot
                
                markers_to_place -= 3
                slot_index += 3
                slot_position += 1
 
            elif markers_to_place == 2:          # place 2 to straddle the line
                
                yy_[slot_index    ] += M2OFFSET * m
                yy_[slot_index + 1] -= M2OFFSET * m
             
                sec_[slot_index    ] = available_slot
                sec_[slot_index + 1] = available_slot 
                
                markers_to_place -= 2
                slot_index += 2
                slot_position += 1

            elif markers_to_place == 1:               

                sec_[slot_index    ] = available_slot                
                markers_to_place = 0

def P3_PBP_chart(playTimesbyPlayer, ax, events_by_player, scoreMargins, flipper, 
                 x_labels = 'TOP',
                 bx_score = None,
                 score    = None,
                 game_team_desc = None):

    Z_GRID = 0  # bottom
    Z_SCRM = 10  
    Z_HBAR = 20
    Z_EVNT = 30

    ax.set_xlim(-50, (48 * 60) + 50)
    ax.set_xticks([0, 12 * 60, 24 * 60, 36 * 60, 48 * 60], ['', '', '', '', ''])
    ax.set_xticks([6 * 60, 18 * 60, 30 * 60, 42 * 60], minor = True)

    ax.xaxis.tick_top()  
    tls = ['Q1', 'Q2', 'Q3', 'Q4'] if x_labels == 'TOP' else ['', '', '', '']
    ax.set_xticklabels(tls, minor = True, color=TABLE_C)

    ax.tick_params(axis='x', which='major', labelsize=0, pad=0,   length = 0)
    ax.tick_params(axis='x', which='minor', labelsize=9, pad=-10, length = 0)
    
    ax.tick_params(axis='y', which='both', labelsize=0, length=0, direction='in')
    ax.grid(True, axis='x', color=GRID_C, linestyle='-', linewidth=GRID_LINEWIDTH, zorder= Z_GRID)
    
    ax3 = ax.twinx()

    (our_team, opp_team, top_team, bot_team, home_team, away_team) = game_team_desc
   
    if bx_score._team_name == top_team:         
        P3_score(ax3, score[0], score[1], game_team_desc)
    else:
        P3_scoremargin(ax3, scoreMargins, flipper, Z_SCRM, game_team_desc)

    _players = list(playTimesbyPlayer.keys())
    _player_cnt = len(_players)
    
    first_ytick = -5
    # +2 is header and team summary in table
    last_ytick = -5 + (10 * (_player_cnt + 2)) + 5

    ax.set_ylim(first_ytick , last_ytick)

    # ax2 is where we plot boxscore and events
    ax2 = ax.twinx()        
    ax2.set_ylim(first_ytick , last_ytick)
    ax2.yaxis.set_visible(False)
    
    for s in ['top', 'right', 'bottom', 'left']:
        ax3.spines[s].set_visible(False)
        ax2.spines[s].set_visible(False)    

    for i, _player in enumerate(_players):

        play_times = playTimesbyPlayer[_player]

        if len(play_times) == 0: print('No Data',_player)
        else:   
        # elif _player == 'Josh Giddey':    
            _y = -5 + ((_player_cnt - i) * 10) 
            
            starts = list(map(lambda x: x[0], play_times))
            widths = list(map(lambda x: x[1], play_times))
            pms    = list(map(lambda x: x[2], play_times))
            for j, x in enumerate(starts):
                start = x
                sc = STINT_C         
                if pms[j] > 2: sc = STINT_COLOR_PLUS if flipper else STINT_COLOR_MINUS
                elif pms[j] < -2: sc = STINT_COLOR_MINUS if flipper else STINT_COLOR_PLUS
                l = matplotlib.lines.Line2D([start, start + widths[j]], [_y, _y], lw = 1.0, ls= '-', c=sc)
                ax.add_line(l)                
            
            sec__     = events_by_player[_player][0::4]
            color__   = events_by_player[_player][1::4]
            size__    = events_by_player[_player][2::4] 
            marker__  = events_by_player[_player][3::4] 
            y__       = [_y] * len(sec__)
        
            stack_markers(y__, sec__, color__, _player_cnt)

            for idx in range(0,len(sec__)):
                 if type(marker__[idx]) != type([]):
                    ax2.scatter(sec__[idx],y__[idx], marker = marker__[idx], color=color__[idx], s=size__[idx])
                 else:
                    ax2.text(sec__[idx],y__[idx], s = marker__[idx][0], color=color__[idx], 
                             size=size__[idx] / MRK_FONTSCALE, 
                             va = 'center_baseline', 
                             ha = 'center',
                             fontweight = MRK_FONTWEIGHT
                             )

    bs_rows, bs_columns, bs_data = bx_score.get_bs_data(_players +  [bx_score._team_name])
    trows = list(map(lambda x: shorten_player_name(x, 12), bs_rows))

    color_by_col_name = {
          'PTS' : BOX_COL_COLOR
        , 'MIN' : BOX_COL_COLOR
        , 'FG'  : BOX_COL_COLOR
        , '3PT' : BOX_COL_COLOR
        , 'FT'  : BOX_COL_COLOR        
        , 'REB' : BOX_COL_COLOR
        , 'BLK' : GOOD_EVNT
        , 'AST' : GOOD_EVNT
        , 'STL' : GOOD_EVNT
        ,  'TO' : BAD_EVNT
        , 'PF'  : BAD_EVNT
        , PM    : BOX_COL_COLOR
    }

    colors_4_col = [get_color(bx_score._team_name)]
    for k in bs_columns:
        c = color_by_col_name[k] if k in list(color_by_col_name.keys()) else TABLE_COLOR
        colors_4_col.extend([c])

    def make_column_widths(col_label, test_ax):

        # 3-4 free throws vs.  3 assists type data
        rx = '00-00' if col_label in ['FG','REB','3PT','FT'] else '000'

        # gets tick width
        t = test_ax.text(0, 0, 
            s = rx, 
            size = 22 / MRK_FONTSCALE, 
            # fontweight = MRK_FONTWEIGHT
        )
        
        transf = ax2.transData.inverted()
        bb = t.get_window_extent()
        bb_xy = bb.transformed(transf)
        t.remove()
        # return text width in as yet unknown units
        # funky as REB is last of the 00-00 columns others are 000
        # the .9 is so we have space on wither side
        # we use this to center our values under our column labels
        return (bb_xy.x1 - bb_xy.x0) + (-50 if col_label == 'REB' else 0.9)

    column_widths = [470] + list(map(lambda x:make_column_widths(x,ax2),bs_columns))
   
    def plot_boxscore_row(start, y, row):
        for idx,r in enumerate(row):
            ax2.text(start, y, s = r,
                color = colors_4_col[idx], 
                size = 24 / MRK_FONTSCALE, 
                va = 'center_baseline', 
                ha = 'left' if idx == 0 else 'center',
                # fontweight = MRK_FONTWEIGHT
            )

            start += column_widths[idx]

    ROW_START = 2880 + 30

    # does the column headers
    plot_boxscore_row(ROW_START,-5 + len(trows) * 10,[''] + bs_columns)

    trows.reverse()
    bs_data.reverse()

    for i, bs in enumerate(bs_data):
        start = ROW_START 
        y = -5 + ((i) * 10)
        plot_boxscore_row(start, y,[trows[i]] + bs)

def P3_score(_ax, home_scores, away_scores, game_team_desc):
    
    (our_team, opp_team, top_team, bot_team, home_team, away_team) = game_team_desc
    # print(f'P3_score  US:{our_team} OPP:{opp_team} TT:{top_team} BT:{bot_team} HT:{home_team} AT:{away_team}')
    D1_color = dimmer(get_color(top_team))
    D2_color = dimmer(get_color(bot_team))
       
    import math
    mh = abs(max(home_scores))
    ma = abs(max(away_scores))
    m = max(mh, ma) 
    m = int(math.ceil(m/10) * 10)

    _ax.set_ylim(0, m)
    _ax.yaxis.set_visible(False)
    _ax.xaxis.set_visible(False)
  
    _ax.scatter(range(0, len(home_scores)), home_scores, color=D1_color, s=.01)
    _ax.scatter(range(0, len(away_scores)), away_scores, color=D2_color, s=.01)
    
def P3_scoremargin(_ax, _scoreMargins, flipper, _zorder, game_team_desc ):
    
    (our_team, opp_team, top_team, bot_team, home_team, away_team) = game_team_desc
    
    home_color = dimmer(get_color(top_team))
    away_color = dimmer(get_color(bot_team))

    import math
    mx = abs(max(_scoreMargins))
    mi = abs(min(_scoreMargins))
    m = max(mx, mi) * 3
    m = int(math.ceil(m/10) * 10)
    r = list(range(-m, m+10, 10))

    _ax.set_ylim(-m, m)
    _ax.yaxis.set_visible(False)
    _ax.xaxis.set_visible(False)
  
    # if flipper:
    #     _scoreMargins = list(map(lambda x: -x, _scoreMargins))
    
    c_minus = settings.get('PM_PLUS_COLOR')    
    c_plus  = settings.get('PM_MINUS_COLOR')   
    _colors = list(map(lambda x: away_color if x < 0 else home_color, _scoreMargins))

    _ax.scatter(range(0, len(_scoreMargins)), _scoreMargins, color=_colors, s=.01, zorder=_zorder)

def make_scoremargin(play_by_play):
    # create scoremargin for every second of the game all 14400 = 60 * 12 * 4
    # this is an issue when OT comes along  // TODO
    # score margin is 'TIE' otherwise +/- difference of score. TIE set to 0 for us
    # like most other data elements its None if it is not changed
    scoreMargins = [0]
    lastscoretime = 0
    lastscorevalue = 0
    home_scores = []
    away_scores = []
    last_home_score = 0
    last_away_score = 0
    
    z = play_by_play.scoremargin.dropna().index
    
    for i, v in play_by_play.loc[z].iterrows():
        scoremargin = v.scoremargin
        
        if scoremargin != '':
            if scoremargin == 'TIE' :
                scoremargin = 0
            scoremargin = int(scoremargin)
            #       ///////// this is a little broken  ////////
            now = int(v.sec)
            # print(v.sec,scoremargin,v.period,v.pctimestring,len(scoreMargins))
            home_score = int(v.score_home)
            away_score = int(v.score_away)
            if (now - lastscoretime) != 0:
                scoreMargins.extend([lastscorevalue] * (now - lastscoretime - 1))
                scoreMargins.extend([scoremargin])
                
                home_scores.extend([last_home_score] * (now - lastscoretime - 1))
                home_scores.extend([home_score])

                away_scores.extend([last_away_score] * (now - lastscoretime - 1))
                away_scores.extend([away_score])

            else: 
                scoreMargins[-1] = scoremargin
                home_scores[-1] = home_score
                away_scores[-1] = away_score
                
            lastscoretime = now
            lastscorevalue = scoremargin
            last_home_score = home_score
            last_away_score = away_score

    needed = 60*48 - len(scoreMargins) + 1
         
    if needed > 0:
        
        # print('needed scm',len(scoreMargins),needed) 
        scoreMargins.extend([lastscorevalue] * (needed + 2))
        home_scores.extend([last_home_score] * (needed + 2))        
        away_scores.extend([last_away_score] * (needed + 2))

    # print('l scm',len(scoreMargins))    
    return scoreMargins, home_scores, away_scores

def get_title_and_friends(game_data, boxscore):
    
    debug_title = f'{game_data.game_id} {DB_NAME}'
    
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
    gds = f'{gd[1]}/{gd[2]}/{gd[0]}'   # US date formate mm/dd/yyyy

    title = f'{gds}   {game_data.matchup_away}   {int(game_data.pts_away)}-{int(game_data.pts_home)}'
    return title, debug_title, top_team, bot_team, team_home, team_away

def P3_prep(our_stints, game_data, scoreMargins, team = None, opponent = False):

    our_stints_by_player = our_stints[0]
    boxscore = box_score(our_stints[1])

    players = list(our_stints_by_player.keys())
    starters = []
    for player in players:
        if len(our_stints_by_player[player]) > 0:
            # stint start from first stint of player that has stints, 0 means start of game
            if our_stints_by_player[player][0][1] == 0:
                starters += [player]

    if opponent:
        teams = set(game_data.play_by_play.player1_team_abbreviation.dropna().to_list()[0:10])
        teams.remove(team)
        try:    teams.remove('')
        except: a = 1
        
        team = list(teams)[0]
    
    boxscore.set_team_name(team)

    bench = list(set(players) - set(starters))
    players = starters + bench

    playTimesbyPlayer = {}
    events_by_player = {}

    current_oreb_count = {}    

    for player in players:

        def bosco(stint,player):
            # stint = [ length, start, stop ]
            
            start = int(stint[1])
            length = int(stint[0])
            
            startM = scoreMargins[start]
            stopM = scoreMargins[start+length]

            boxscore.add_plus_minus(player, startM, stopM)
            
            return (start, length, startM - stopM)
            
        playTimesbyPlayer[player] = list(map(lambda x: bosco(x,player), our_stints_by_player[player]))

        _events = []

        a_ = game_data.play_by_play['player1_name'] == player
        b_ = game_data.play_by_play['player2_name'] == player
        c_ = game_data.play_by_play['player3_name'] == player

        ours = (a_ | b_ | c_)
        plays_for_player = game_data.play_by_play[ours]

        for i, v in plays_for_player.iterrows():
            if v.eventmsgtype == 8:
                _ec, _es, _et, _ec2, _es2, _et2 = event_to_size_color_shape(player, v, current_oreb_count, scoreMargins)
                if _ec != None:  _events.extend([v.sec, _ec, _es, _et ])
                if _ec2 != None: _events.extend([v.sec, _ec2, _es2, _et2])

        for i, v in plays_for_player.iterrows():
            if v.eventmsgtype != 8:
                _ec, _es, _et, _ec2, _es2, _et2 = event_to_size_color_shape(player, v, current_oreb_count,scoreMargins)
                if _ec != None:  _events.extend([v.sec, _ec, _es, _et ])
                if _ec2 != None: _events.extend([v.sec, _ec2, _es2, _et2])

        events_by_player[player] = _events

        try:
            # hack for getting ORS - Offensive ReboundS
            boxscore.set_item(player,'ORS', int(current_oreb_count[player]))
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
    
    layout = [
        [TL, TL, TL, TL, TL, TL, TR, TR, TR, TR],
        [TL, TL, TL, TL, TL, TL, TR, TR, TR, TR],
        [TL, TL, TL, TL, TL, TL, TR, TR, TR, TR],
        [TL, TL, TL, TL, TL, TL, TR, TR, TR, TR],
        [E2, E2, E2, E2, E2, E2, E1, E1, E1, E1],
        [BL, BL, BL, BL, BL, BL, BR, BR, BR, BR],
        [BL, BL, BL, BL, BL, BL, BR, BR, BR, BR],
        [BL, BL, BL, BL, BL, BL, BR, BR, BR, BR],
        [BL, BL, BL, BL, BL, BL, BR, BR, BR, BR],
    ]

    figure, axd = plt.subplot_mosaic(layout, figsize = (10.0, 6.5) )
    
    figure.canvas.manager.set_window_title(title)

    return axd, E1,TL,TR,MD,E2,BL,BR,E3

def plot3(TEAM1, game_data, our_stints, opponent_stints):

    data_source = settings.get('SOURCE')
    if   'WEB:'  in data_source and SAVE_GAME_AS_CSV == 'ON': dump_pbp(game_data)
    
    scoreMargins, home_scores, away_scores = make_scoremargin(game_data.play_by_play)
            
    boxscore1, playTimesbyPlayer1, events_by_player1, players1 = \
    P3_prep(our_stints, game_data, scoreMargins, team=TEAM1)

    boxscore2, playTimesbyPlayer2, events_by_player2, players2 = \
    P3_prep(opponent_stints, game_data, scoreMargins, team=TEAM1, opponent=True)

    title, debug_title, top_team, bot_team, home_team, away_team = \
    get_title_and_friends(game_data, boxscore1)

    # top team = winner, bot_team = loser
    # home_team - plus/minus and score 
    # home ahead is + plus, if away 
    # score plot shown for winner needs home/away teams for colors
    # plus minus the same thing
    
    plt.style.use(settings.get('PLOT_COLOR_STYLE'))
    axd,E1,TL,TR,MD,E2,BL,BR,E3 = p3_layout(debug_title)

    # winning team goes on top 
    # TEAM1 is group1 data, opponennt is group2 data
    # away team gets the plus/minus flipped
    # plus minus is from the home team perspective

    _ad1_flip = False
    _ad2_flip = False
    
    if top_team == TEAM1:
        _ad1_ = axd[TL]
        _ad2_ = axd[BL]
        _ad1_label = 'TOP'
        _ad2_label = None
    else :
        _ad1_ = axd[BL]
        _ad2_ = axd[TL]
        _ad1_label = None
        _ad2_label = 'TOP'

    if TEAM1 == home_team:
        _ad2_flip = True
    else:
        _ad1_flip = True
            
    team_desc = (boxscore1._team_name, boxscore2._team_name, top_team, bot_team, home_team, away_team)
          
    # print('winner',top_team,' loser',bot_team,' home',home_team,' away',away_team)
    
    boxscore1.plus_minus_flip(_ad1_flip)
    P3_PBP_chart(playTimesbyPlayer1, _ad1_, events_by_player1, scoreMargins, 
                 flipper  = _ad1_flip, 
                 x_labels =_ad1_label,
                 bx_score = boxscore1,
                 score = [home_scores, away_scores],
                 game_team_desc = team_desc
                 )

    boxscore2.plus_minus_flip(_ad2_flip)
    P3_PBP_chart(playTimesbyPlayer2, _ad2_, events_by_player2, scoreMargins, 
                 flipper  = _ad2_flip, 
                 x_labels =_ad2_label,
                 bx_score = boxscore2,
                 score = [home_scores, away_scores],
                 game_team_desc = team_desc
                 )
    
    axd[E1].set_title(title, y=0.4, pad=-1, fontsize=9, color=TABLE_C)
    
    axd[E2].legend( 
        labelcolor = TABLE_C,
        fontsize ='small',
        markerfirst=True,
        ncols = 5,
        loc = 'center', 
        frameon = False,
        handletextpad= 0.10,
        handles = event_legend())

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
        wspace=3, hspace=0.1, right=0.98, left=0.01, top=0.99, bottom=0.015
    )

    plt.show()
    plt.close('all')
