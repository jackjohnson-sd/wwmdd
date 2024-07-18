import os
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
          
from box_score import box_score,PM
from nba_colors import get_color, dimmer, brighter
from event_prep import event_to_size_color_shape, get_event_map

from settings import defaults 
from play_by_play import dump_pbp, box_score_dump,overlap_combos,overlap_dump
from utils import _ms,sec_to_period_time2,shorten_player_name,save_files


from loguru import logger

import settings

color_defaults = None

event_map = None

TEST_PLAYERS      = defaults.get('TEST_PLAYERS')   

def quitGame(): return input("Enter Q to quit or any other key to continue: ") == 'Q'

def do_plot(theplot):
    SUB_PLOTS = defaults.get('SUB_PLOTS') 
    if 'all' in SUB_PLOTS: return True
    if theplot in SUB_PLOTS: return True
    return False

# if not do_plot('tools'):
#     matplotlib.rcParams['toolbar'] = 'None' 


def stack_markers(yy_, sec_, color_):
    
    M2OFFSET       = color_defaults.get('MARKER_2_STACK_OFFSET')    # vertical offset for 2 markers at one place
    M3OFFSET       = color_defaults.get('MARKER_3_STACK_OFFSET')    # vertical offset for 3 markers at one place
    MKR_WIDTH      = color_defaults.get('MARKER_WIDTH')             # used to determine if markes will overlap
    STINT_COLOR_IN    = color_defaults.get('STINT_COLOR_IN')       
    STINT_COLOR_OUT   = color_defaults.get('STINT_COLOR_OUT')       
    # The SUB markers go first, we don't want to move them
    # around so skip to first non-SUB. This means we write 
    # on top of them. Which is what we want
    try:
        nsubs_ = list(map(lambda x:x not in [STINT_COLOR_IN,STINT_COLOR_OUT],color_ ))
        first_no_sub_item = nsubs_.index(True)
    except Exception as err:
        first_no_sub_item = 0

    # we stack 3 if we have them, then stack 2
    idx_max = len(sec_)
    idx = first_no_sub_item

    # a hopeless attempt to scale size based # players
    # more players means less space for our stack of 3
    m = 1 #nplayers_ / 14

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

def make_scoremargin(play_by_play):
    # create scoremargin for every second of the game all 14400 = 60 * 12 * 4
    # this is an issue when OT comes along  // TODO
    # score margin is 'TIE' otherwise +/- difference of score. TIE set to 0 for us
    # like most other data elements its None if it is not changed
    # score is  away - home
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
            now = int(v.sec)
            # print(v.sec,scoremargin,v.period,v.pctimestring,len(scoreMargins))
            away_score = int(v.score_home)
            home_score = int(v.score_away)
            if (now - lastscoretime) != 0:
                scoreMargins.extend([lastscorevalue] * (now - lastscoretime - 1))
                scoreMargins.extend([scoremargin])
                
                home_scores.extend([last_home_score] * (now - lastscoretime - 1))
                home_scores.extend([home_score])

                away_scores.extend([last_away_score] * (now - lastscoretime - 1))
                away_scores.extend([away_score])

            else: 
                try:
                    scoreMargins[-1] = scoremargin
                    # home_scores[-1] = home_score
                    # away_scores[-1] = away_score
                except: pass    
                            
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

    return scoreMargins, home_scores, away_scores

def plot_score(_ax, home_scores, away_scores, game_info):
    
    if not do_plot('score') : 
        _ax.yaxis.set_visible(False)
        _ax.xaxis.set_visible(False)
        # _ax.set_ylim(0, 0)

        for s in ['top', 'right', 'bottom', 'left']:
            _ax.spines[s].set_visible(False)

        return
    
    D1_color = dimmer(get_color(game_info['H']))
    D2_color = dimmer(get_color(game_info['A']))
       
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
    
def plot_scoremargin(_ax, _scoreMargins, _zorder, game_info ):

    if not do_plot('margin') :
        _ax.yaxis.set_visible(False)
        _ax.xaxis.set_visible(False)

        for s in ['top', 'right', 'bottom', 'left']:
            _ax.spines[s].set_visible(False)
            
        return

    home_color = dimmer(get_color(game_info['H']))
    away_color = dimmer(get_color(game_info['A']))
    
    import math
    mx = abs(max(_scoreMargins))
    mi = abs(min(_scoreMargins))
    m = max(mx, mi) * 3
    m = int(math.ceil(m/10) * 10)
    r = list(range(-m, m+10, 10))

    _ax.set_ylim(-m, m)
    _ax.yaxis.set_visible(False)
    _ax.xaxis.set_visible(False)
      
    _colors = list(map(lambda x: away_color if x < 0 else home_color, _scoreMargins))

    _ax.scatter(range(0, len(_scoreMargins)), _scoreMargins, color=_colors, s=.01, zorder=_zorder)

def get_title_and_friends(game_data):
        
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

    title = [
        f'{gds} {game_data.start_time}', 
        f'{game_data.matchup_away}'
        ]
    game_info = { 'T' : top_team, 'B' : bot_team, 'H' : team_home, 'A' : team_away, 'START' : game_data.start_time }
    
    DATA_SOURCE    = defaults.get('SOURCE')
    if 'WEB' in DATA_SOURCE:
        debug_title = f' WEB {gds} {game_data.matchup_away}'
    else:    
        debug_title = f'{game_data.game_id} {DATA_SOURCE}'

    return title, debug_title, game_info # top_team, bot_team, team_home, team_away

def plot_text(_ax_,x,y,text, _color,ha='left',scale=1.0):
    MRK_FONTSCALE     = color_defaults.get('MARKER_FONTSCALE')

    _ax_.text(x, y, s = text,
        color = _color, 
        size = scale * (24 / MRK_FONTSCALE), 
        va = 'center_baseline', 
        ha = 'left', # 'center',
        clip_on = False
        # fontweight = MRK_FONTWEIGHT
    )

def plot_quarter_score(home_scores, away_scores, axis, x,y, game_info):

    MRK_FONTSCALE     = color_defaults.get('MARKER_FONTSCALE')

    if not do_plot('periodscores'): return
    
    top_team = game_info['T']
    bot_team = game_info['B']
    home_team = game_info['H']
    away_team = game_info['A']
        
    quarter_end  =  [12*60, 24*60,36*60,48*60]
    quarter_start = [0,     12*60,24*60,36*60]

    lxoffset = 2
    lx0 = x + lxoffset + 1
    lx1 = lx0 + lxoffset 
    lx2 = lx1 + lxoffset
    lx3 = lx2 + lxoffset
    lx4 = lx3 + lxoffset + 1
    lx5 = lx4 + lxoffset
    lx6 = lx5 + lxoffset  
    
    ly0 = y - 22
    
    location = [
        [[x,ly0],[lx0,ly0],[lx1,ly0],[lx2,ly0],[lx3,ly0], [lx4,ly0], [lx5,ly0], [lx6,ly0]],
        [[x, y], [lx0,  y],[lx1,  y],[lx2, y], [lx3,  y], [lx4,  y], [lx5,  y], [lx6,  y]]
        ]

    def qs_text(x,y,text, _color):
        axis.text(x, y, s = text,
            color = _color, 
            size = 24 / MRK_FONTSCALE, 
            va = 'center_baseline', 
            ha = 'left', # 'center',
            clip_on = False
            # fontweight = MRK_FONTWEIGHT
        )
        
    top_co = brighter(get_color(top_team))
    bot_co = brighter(get_color(bot_team))
    
    top_data = home_scores if top_team == home_team else away_scores
    bot_data = away_scores if bot_team == away_team else home_scores
    
    qs_text(x, ly0, top_team, top_co)
    qs_text(location[0][5][0], ly0, str(top_data[-1]), top_co)

    qs_text(x, y, bot_team, bot_co)
    qs_text(location[1][5][0], y, str(bot_data[-1]), bot_co)

    for i,v in enumerate(quarter_end):
        home_q_end_score = home_scores[v-1]
        home_in_q_score = home_q_end_score - home_scores[quarter_start[i]]
 
        away_q_end_score = away_scores[v-1]
        away_in_q_score = away_q_end_score - away_scores[quarter_start[i]]
        
        lh = location[0][i+1]
        la = location[1][i+1]
        
        top_data = home_in_q_score if top_team == home_team else away_in_q_score
        bot_data = away_in_q_score if bot_team == away_team else home_in_q_score

        qs_text(lh[0], lh[1], top_data, top_co) 
        qs_text(la[0], la[1], bot_data, bot_co)

    # shooting percentage stuff
    # bs0 = (' ').join(bs_sum[0])
    # bs1 = (' ').join(bs_sum[1])
    
    # lh = location[0][-1]
    # la = location[1][-1]

    # qs_text(lh[0], lh[1], bs0, top_co) 
    # qs_text(la[0], la[1], bs1, bot_co) 
    
def plot_box_score(axis, box_score, players, bx_col_data):
        
    bs_rows, bs_columns, bs_data = box_score.get_bs_data(players +  [box_score._team_name])
    trows = list(map(lambda x: shorten_player_name(x, 12), bs_rows))

    trows.reverse()
    bs_rows.reverse()
    bs_data.reverse()

    BAD_EVNT          = color_defaults.get('BAD_EVENT_COLOR')   
    GOOD_EVNT         = color_defaults.get('GOOD_EVENT_COLOR') 
    BOX_COL_COLOR     = color_defaults.get('BOX_COL_COLOR')

    BOX_COL_COLOR     = color_defaults.get('BOX_COL_COLOR')
    BOX_COL_MAX_COLOR = color_defaults.get('BOX_COL_MAX_COLOR')
    TABLE_COLOR       = color_defaults.get('TABLE_COLOR')
    MRK_FONTSCALE     = color_defaults.get('MARKER_FONTSCALE')

    color_by_col_name = {
          'PTS' : BOX_COL_COLOR
        , 'MIN' : BOX_COL_COLOR
        , 'FG'  : BOX_COL_COLOR
        , '3PT' : BOX_COL_COLOR
        ,  'FT' : BOX_COL_COLOR        
        , 'REB' : BOX_COL_COLOR
        , 'BLK' : GOOD_EVNT
        , 'AST' : GOOD_EVNT
        , 'STL' : GOOD_EVNT
        ,  'TO' : BAD_EVNT
        ,  'PF' : BAD_EVNT
        ,   PM  : BOX_COL_COLOR
    }

    colors_4_col = [get_color(box_score._team_name)]
    for k in bs_columns:
        c = color_by_col_name[k] if k in list(color_by_col_name.keys()) else TABLE_COLOR
        colors_4_col.extend([c])

    bs_columns = [''] + bs_columns
 
    if type(bx_col_data[0]) != type(1):

        def make_column_widths_new(col_data, test_ax):
            
            def ln(x):
                t = test_ax.text(0, 0, s = x, size = 24 / MRK_FONTSCALE,        
                                va = 'center_baseline', 
                                ha = 'center')
                transf = axis.transData.inverted()
                bb = t.get_window_extent()
                bb_xy = bb.transformed(transf)
                t.remove()
                return (bb_xy.x1 - bb_xy.x0) * 0.66 # WTF
            
            a = list(map(lambda x:ln(x),col_data))
            return max(a)

        column_widthsnew  = [470] + list(map(lambda x:make_column_widths_new(x,axis), bx_col_data))
    else : 
        column_widthsnew  = bx_col_data
      
    def plot_boxscore_row(start, y, row, color = None):
        
        for idx,r in enumerate(row):
            if color == None:
                c = colors_4_col[idx]
                if idx > 0 and idx < len(bs_columns): 
                    if box_score.is_max(bs_columns[idx],r,row[0]):
                        c = BOX_COL_MAX_COLOR
                else: 
                    c = colors_4_col[idx]
            else: 
                c = color[idx]
            
            if idx != 0: start += column_widthsnew[idx]/2    
    
            axis.text(start, y, s = r,
                color = c, 
                size = 24 / MRK_FONTSCALE, 
                va = 'center_baseline', 
                # player names go left
                ha = 'left' if idx == 0 else 'center',
                # fontweight = MRK_FONTWEIGHT
            )

            start += int(column_widthsnew[idx])

    ROW_START = 2880 + 50

    doRows = do_plot('boxscore') 
    
    brighter_column_color = list(map(lambda x:brighter(x),colors_4_col))

    if doRows :
        # does the column headers
        # plot_boxscore_row(ROW_START,-5 + len(trows) * 10, bs_columns, color = brighter(BOX_COL_COLOR))
        plot_boxscore_row(ROW_START,-5 + len(trows) * 10, bs_columns, 
                          color = list(map(lambda x:brighter(x),brighter_column_color)))

    for i, bs in enumerate(bs_data):
        y = -5 + ((i) * 10)
        if doRows:
            c = None
            if i == 0:
                c = brighter_column_color
                
            plot_boxscore_row(ROW_START, y,[trows[i]] + bs,c)
        else:
            plot_boxscore_row(ROW_START, y,[trows[i]])
    
    return column_widthsnew

def plot_stints(axis, _y, play_times, flipper):

    if do_plot('stints') :
        
        STINT_COLOR       = color_defaults.get('STINT_COLOR')       
        STINT_COLOR_IN    = color_defaults.get('STINT_COLOR_IN')       
        STINT_COLOR_OUT   = color_defaults.get('STINT_COLOR_OUT')     
        STINT_COLOR_PLUS  = color_defaults.get('STINT_COLOR_PLUS')
        STINT_COLOR_MINUS = color_defaults.get('STINT_COLOR_MINUS')
  
        starts = list(map(lambda x: x[0], play_times))
        widths = list(map(lambda x: x[1], play_times))
        pms    = list(map(lambda x: x[2], play_times))
        
        for j, x in enumerate(starts):
            start = x
            axis.scatter(start, _y, marker = 'o', color=STINT_COLOR_IN, s=8.0)
            axis.scatter(start + widths[j],_y, marker = 'o', color=STINT_COLOR_OUT, s=8.0)

            sc = STINT_COLOR      
            if pms[j] > 2: sc = STINT_COLOR_PLUS if flipper else STINT_COLOR_MINUS
            elif pms[j] < -2: sc = STINT_COLOR_MINUS if flipper else STINT_COLOR_PLUS
            l = matplotlib.lines.Line2D([start, start + widths[j]], [_y, _y], lw = 1.0, ls= '-', c=sc)
            axis.add_line(l)                

def plot_events(axis2, _y, events):

    MRK_FONTSCALE     = color_defaults.get('MARKER_FONTSCALE')    
    
    if do_plot('events'):
        
        sec__     = events[0::4]
        color__   = events[1::4]
        size__    = events[2::4] 
        marker__  = events[3::4] 
        y__       = [_y] * len(sec__)

        stack_markers(y__, sec__, color__)

        for idx in range(0,len(sec__)):
            if type(marker__[idx]) != type([]):
                axis2.scatter(sec__[idx],y__[idx], marker = marker__[idx], color=color__[idx], s=size__[idx])
            else:
                axis2.text(sec__[idx],y__[idx], s = marker__[idx][0], color=color__[idx], 
                            size = size__[idx] / MRK_FONTSCALE, 
                            va = 'center_baseline', 
                            ha = 'center',
                            # fontweight = MRK_FONTWEIGHT
                            )

def play_by_play_chart(playTimesbyPlayer, ax, events_by_player, scoreMargins,  
                 x_labels = 'TOP',
                 bx_score = None,
                 bx_widths = None,
                 score    = None,
                 game_info = None,
                 bs_sum = None):

    Z_GRID = 0  # bottom
    Z_SCRM = 10  
    Z_HBAR = 20
    Z_EVNT = 30

    TABLE_COLOR       = color_defaults.get('TABLE_COLOR')
    GRID_LINEWIDTH    = color_defaults.get('GRID_linewidth')

    x_ticks = [0, 12 * 60, 24 * 60, 36 * 60, 48 * 60]
    ax.set_xlim(-50, (48 * 60) + 50)
    ax.set_xticks(x_ticks, ['', '', '', '', ''])
    ax.set_xticks([6 * 60, 18 * 60, 30 * 60, 42 * 60], minor = True)

    ax.xaxis.tick_top()  
    tls = ['Q1', 'Q2', 'Q3', 'Q4'] if x_labels == 'TOP' else ['', '', '', '']
    ax.set_xticklabels(tls, minor = True, color=TABLE_COLOR)

    ax.tick_params(axis='x', which='major', labelsize=0, pad=0,   length = 0)
    ax.tick_params(axis='x', which='minor', labelsize=9, pad=-20, length = 0)
    
    ax.tick_params(axis='y', which='both', labelsize=0, length=0, direction='in')
    # ax.grid(True, axis='x', color=GRID_C, linestyle='-', linewidth=GRID_LINEWIDTH, zorder= Z_GRID)
   
    _players = list(playTimesbyPlayer.keys())
    _player_cnt = len(_players)
    
    first_ytick = -5
    # +2 is header and team summary in table
    last_ytick = -5 + (10 * (_player_cnt + 2)) + 5

    GRID_C            = color_defaults.get('GRID_COLOR')

    for x in x_ticks:
        l1 = Line2D([x,x], [first_ytick-15,last_ytick-20], lw=GRID_LINEWIDTH, color=GRID_C, label='' )
        ax.add_line(l1)
    
    ax.set_ylim(first_ytick , last_ytick)

    ax2 = ax.twinx()        
    ax2.set_ylim(first_ytick , last_ytick)
    ax2.yaxis.set_visible(False)

    ax3 = ax.twinx()

    for s in ['top', 'right', 'bottom', 'left']:
        ax3.spines[s].set_visible(False)
        ax2.spines[s].set_visible(False)    

    # (our_team, opp_team, top_team, bot_team, home_team, away_team) = game_team_desc
    if bx_score._team_name == game_info['T']:
        plot_score(ax3, score[0], score[1], game_info)
    else:
        plot_scoremargin(ax3, scoreMargins, Z_SCRM, game_info)
    
    col_widths = []
    for i, _player in enumerate(_players):
        
        events = events_by_player[_player]
        play_times = playTimesbyPlayer[_player]
        _y = -5 + ((_player_cnt - i) * 10)
         
        plot_stints(ax, _y, play_times, bx_score.is_flipper())
        plot_events(ax2, _y, events)
        col_widths = plot_box_score(ax2,bx_score,_players, bx_widths)
    
    return col_widths

def plot_title_legend_Qs(_ax_, x, y, title, home_scores, away_scores, game_info):
    
    _ax_.set_xlim(0, 100)
    _ax_.set_ylim(100, 0)
     
    _ax_.tick_params(axis='both', which='major', labelsize=0, pad=0,   length = 0)
 
    _ax_.yaxis.set_visible(False)
    _ax_.xaxis.set_visible(False)
  
    c2xstart = x
    c2ystart = y
    
    TABLE_COLOR       = color_defaults.get('TABLE_COLOR')

    plot_text(_ax_, c2xstart, c2ystart, title[0],TABLE_COLOR,scale=1.1)
    plot_text(_ax_, c2xstart + 4,c2ystart -22,title[1],TABLE_COLOR, scale=1.1)
    
    plot_quarter_score(home_scores, away_scores, _ax_, c2xstart + 2, c2ystart + 50, game_info)

    if do_plot('legend'):
        plot_event_legend(_ax_,20,50)

def plot_event_legend(ax,xstart,ystart):
    
    STINT_COLOR       = color_defaults.get('STINT_COLOR')       
    STINT_COLOR_PLUS  = color_defaults.get('STINT_COLOR_PLUS')
    STINT_COLOR_MINUS = color_defaults.get('STINT_COLOR_MINUS')
    BOX_COL_COLOR     = color_defaults.get('BOX_COL_COLOR')
    MRK_FONTSCALE     = color_defaults.get('MARKER_FONTSCALE')

    def stint1_marker(x_, y_, color, txt):
         
        l1 = Line2D([x_ - 1 , x_ + 1], [y_,y_], lw=2, color=color , label='' )
        ax.add_line(l1)

        ax.text(x_ + 2, y_, s = txt, 
            color=color, 
            size= 22 / MRK_FONTSCALE, 
            va = 'center', 
            ha = 'left',
            clip_on = False
            # fontweight = MRK_FONTWEIGHT
            )

    def stint_3marker(x_,y_):
        
        al1x = x_ - 5
        al2x = al1x + 1
        al3x = al2x + 1
        al4x = al3x + 1
        
        l1 = Line2D([al1x,al2x], [y_,y_], lw=2, color=STINT_COLOR_MINUS , label='' )
        l2 = Line2D([al2x,al3x], [y_,y_], lw=2, color=STINT_COLOR, label='' )
        l3 = Line2D([al3x,al4x], [y_,y_], lw=2, color=STINT_COLOR_PLUS , label='' )
        ax.add_line(l1)
        ax.add_line(l2)
        ax.add_line(l3)

        ax.text(al4x + 1,y_, s = 'STINT', 
            color = BOX_COL_COLOR, 
            size = 22 / MRK_FONTSCALE, 
            va = 'center', 
            ha = 'left',
            clip_on = False
            # fontweight = MRK_FONTWEIGHT
            )

    for s in ['top', 'right', 'bottom', 'left']:
        ax.spines[s].set_visible(False)
    
    xoff = 7
    x1 = xstart
    x2 = x1 + xoff 
    x3 = x2 + xoff
    x4 = x3 + xoff
    x5 = x4 + xoff
    # x6 = x5 + xoff
    # x7 = x6 + xoff
    # x8 = x7 + xoff
    # x9 = x8 + xoff
    # x10 = x9 + xoff
    
    yoff = 22
    y1 = ystart
    y2 = y1 + yoff 
    y3 = y2 + yoff 

    b_events = do_plot('events') 
    b_stints = do_plot('stints')
    
    event_legend_map = []
    if b_events and b_stints:
    
        event_legend_map = [    
            [20, 1, x1, y1],  # 3PT 
            [ 1, 0, x1, y2],  # FG
            [ 3, 0, x1, y3],  # FT
        
            [ 2, 0, x2, y1],  # MISS 
            [ 5, 1, x2, y2],  # TO
            [ 6, 0, x2, y3],  # PF
            
            [ 1, 1, x3, y1], # AST
            [ 5, 0, x3, y2],  # STL
            [ 2, 1, x3, y3],  # BLK
        
            [ 4, 0, x4, y1],  # OREB
            [20, 0, x4, y2], # DREB
            
            [ 8, 0, x5, y1],    # SUB
            [ 8, 1, x5, y2] 
            ]   
        stint_3marker(x5,y3)

    elif b_stints:
        
        event_legend_map = [    
            [ 8, 0, x1, y1],    # SUB
            [ 8, 1, x1, y2]    # SUB
        ]
        stint1_marker(x2,y1,STINT_COLOR_PLUS,'STINT PLUS')
        stint1_marker(x2,y2,STINT_COLOR_MINUS,'STINT MINUS')
        stint1_marker(x2,y3,STINT_COLOR,'STINT NEUTRAL')
                
    elif b_events:
        
        event_legend_map = [    
            [20, 1, x1, y1],  # 3PT 
            [ 1, 0, x1, y2],  # FG
            [ 3, 0, x1, y3],  # FT
        
            [ 2, 0, x2, y1],  # MISS 
            [ 5, 1, x2, y2],  # TO
            [ 6, 0, x2, y3],  # PF
            
            [ 1, 1, x3, y1], # AST
            [ 5, 0, x3, y2],  # STL
            [ 2, 1, x3, y3],  # BLK
        
            [ 4, 0, x4, y1],  # OREB
            [20, 0, x4, y2], # DREB    
        ]

    for k in event_legend_map:
        e = event_map[k[0]]
        offset = k[1] * 4
        label = e[3 + offset]
        x = k[2]
        y = k[3]
        if type(e[2 + offset]) == type([]):
            marker_ = e[2 + offset][0]
            ax.text(x-2,y, s = marker_, color=e[offset], 
                size= 20 / MRK_FONTSCALE, 
                va = 'center', 
                ha = 'left',
                # fontweight = MRK_FONTWEIGHT
                )
            
        else: 
            marker_ = e[2 + offset]
            ax.scatter(x-1.5,y-2, marker = marker_, color=e[offset], s= 26 / MRK_FONTSCALE)

        ax.text(x,y, s = label, 
            color=BOX_COL_COLOR, 
            size= 22 / MRK_FONTSCALE, 
            va = 'center', 
            ha = 'left',
            clip_on = False,
            # fontweight = MRK_FONTWEIGHT
            )
        
def plot_prep(_stints, game_data, scoreMargins, team = None, opponent = False, home_team = None):

    our_stints_by_player = _stints[0]
    boxscore = box_score(_stints[1])

    if opponent:
        teams = set(game_data.play_by_play.player1_team_abbreviation.dropna().to_list()[0:50])
        try:    teams.remove('')
        except: a = 1
        
        try: 
            teams.remove(team)
            team = list(teams)[0]
        except: 
            # when testing with only one team in the data 
            team = 'OKC'
        

    boxscore.set_team_name(team)
    boxscore.set_home_team_name(home_team)

    players = list(our_stints_by_player.keys())
    
    # this exercise is to have the starters first then bench sorted by playing time
    starters = []
    for player in players:
        # this should not be needed
        if len(our_stints_by_player[player]) > 0:
            # stint start from first stint of player that has stints, 0 means start of game
            if our_stints_by_player[player][0][1] == 0:
                starters += [player]

    bench = list(set(players) - set(starters))
    
    def fn(p) : return sum(list(map(lambda x:x[0],our_stints_by_player[p])))
    ben = sorted(bench, key = lambda x:fn(x))
    ben.reverse()
    
    players = starters + ben
    
    playTimesbyPlayer = {}
    events_by_player = {}
    current_oreb_count = {}    

    for player in players:

        def start_duration_pm(stint, player):
            # stint = [ length, start, stop ]
            
            start = int(stint[1])
            length = int(stint[0])
            
            startM = scoreMargins[start]
            stopM = scoreMargins[start+length]

            boxscore.add_plus_minus(player, startM, stopM)
            # start, duration, plus/minus
            return (start, length, startM - stopM)
            
        playTimesbyPlayer[player] = list(map(lambda x: start_duration_pm(x,player), our_stints_by_player[player]))

        _events = []

        a_ = game_data.play_by_play['player1_name'] == player
        b_ = game_data.play_by_play['player2_name'] == player
        c_ = game_data.play_by_play['player3_name'] == player

        ours = (a_ | b_ | c_)
        plays_for_player = game_data.play_by_play[ours]

        # for i, v in plays_for_player.iterrows():
        #     if v.eventmsgtype == 8:
        #         _ec, _es, _et, _ec2, _es2, _et2 = event_to_size_color_shape(player, v, current_oreb_count, scoreMargins)
        #         if _ec != None:  _events.extend([v.sec, _ec, _es, _et ])
        #         if _ec2 != None: _events.extend([v.sec, _ec2, _es2, _et2])

        for i, v in plays_for_player.iterrows():
            if v.eventmsgtype != 8:
                    
                _ec, _es, _et, _ec2, _es2, _et2 = event_to_size_color_shape(player, v, current_oreb_count, scoreMargins)
                if _ec != None:  _events.extend([v.sec, _ec, _es, _et ])
                if _ec2 != None: _events.extend([v.sec, _ec2, _es2, _et2])

        events_by_player[player] = _events

        try:
            # hack for getting ORS - Offensive ReboundS
            try: 
                n = int(current_oreb_count[player])
            except: n = 0
            boxscore.set_item(player,'ORS', n)
        except:
            pass
            # boxscore.set_item(player,'ORS', 0)

    boxscore.summary()

    return boxscore, playTimesbyPlayer, events_by_player

def plot_layout(title):
    
    E1 = None
    TL = '2'
    TR = '3'
    MD = None
    E2 = '5'
    BL = '6'
    BR = '7'
    E3 = None
    
    TX = TR if do_plot('boxscore') else TL
    BX = BR if do_plot('boxscore') else BL
        
    layout = [
        [TL, TL, TL, TL, TL, TL, TX, TX, TX, TR],
        [TL, TL, TL, TL, TL, TL, TX, TX, TX, TR],
        [TL, TL, TL, TL, TL, TL, TX, TX, TX, TR],
        [TL, TL, TL, TL, TL, TL, TX, TX, TX, TR],
        [E2, E2, E2, E2, E2, E2, E2, E2, E2, E2],
        [BL, BL, BL, BL, BL, BL, BX, BX, BX, BR],
        [BL, BL, BL, BL, BL, BL, BX, BX, BX, BR],
        [BL, BL, BL, BL, BL, BL, BX, BX, BX, BR],
        [BL, BL, BL, BL, BL, BL, BX, BX, BX, BR],
    ]

    figure, axd = plt.subplot_mosaic(layout, figsize = (10.0, 6.5) )   
    figure.canvas.manager.set_window_title(title)

    return figure, axd, E1,TL,TR,MD,E2,BL,BR,E3

def play_time_check(title,bx1,bx2,stints1,stints2,game_data):
   
         
    # OKC @ BOS 04/03/2024 9:33 PM EST 15090 14400 NOK
    # NOP @ OKC 04/21/2024 11:22 PM EST 14400 15088 NOK
    m1 = int(bx1.get_team_secs_played())
    m2 = int(bx2.get_team_secs_played())
    
    if m1 == m2: 
        logger.info(f'{title[1]} {title[0]} {m1} OK')
        ret_value = True

    else:
        logger.error(f'{title[1]} {title[0]} {m1} {m2} NOK')
        ret_value = False

    return ret_value
        
def stints_as_csv(bx1,bx2,stints1,stints2,game_data):
    def xxx(stints,bx,labels):
    
        def ms(sec):
            m = int(sec / 60)
            s = int(sec % 60)
            return f'{m:02d}:{s:02d}'
        
        def get_oinks(player,stint,box):
            start = stint[1]
            stop  = stint[2]
            
            oinks = box._boxScore[player]['OINK']
            # print(start,stop,oinks)
            def fo(start,stop,oink):
                if oink[2] != None:
                    if oink[2] >= start:
                        if oink[2] <= stop:
                            return oink
                return None
            
            our_oinks = list(map(lambda x:fo(start,stop,x),oinks))
            while None in our_oinks: our_oinks.remove(None)
            
            oinks_sum = {}
            for oink in our_oinks:
                if oink[0] not in oinks_sum.keys():
                    oinks_sum[oink[0]] = 0
                oinks_sum[oink[0]] += int(oink[1])
                    
            return oinks_sum   
        
        def stint_dump(stints,player,box):
            s = ''
            if player in stints[0]:
                    
                stintw = stints[0][player]
                s = ''
                for stint in stintw:
                    bx._boxScore[player]['OINK']
                    tmp = f'{player},{bx._team_name},{sec_to_period_time2(stint[1]).replace(' ',':')},{sec_to_period_time2(stint[2]).replace(' ',':')},{ms(int(stint[0]))}'
                    oinks = get_oinks(player,stint,box)
                    oinks_str = ''
                    for o in labels:
                        v = oinks[o] if o in oinks.keys() else 0
                        oinks_str += ',' + str(v)
                    s += tmp + oinks_str
                    s += '\n'
            else:
                logger.error(f'Stints to csv error. {player} has no stints.')
            
            return s.strip()

        return '\n'.join(list(map(lambda x:f'{stint_dump(stints,x[0],bx)}',bx.get_names_items('secs'))))

    L2a = bx1._bsItemsA 
    L2b = bx1._bsItemsB
    L1 = 'player,player_team,start,end,duration,'
    L2 = L2a + L2b 
    a = xxx(stints1,bx1,L2)
    b = xxx(stints2,bx2,L2)
    
    t = game_data.matchup_home.split(' ')

    import os
    cwd = os.getcwd() + '/' + defaults.get('SAVE_GAME_DIR')
    
    fn = f'STINTS_{t[0]}v{t[2]}{game_data.game_date.replace('-','')}.csv'
    
    fn = os.path.join(cwd, fn) 
    
    if not(os.path.exists(cwd)): os.mkdir(cwd)   
    
    logger.info(f'Saving {os.path.basename(fn)}')
    
    fl_s = open(fn,"w")
    fl_s.write(L1 + (',').join(L2)+ '\n' + a + '\n' + b)
    fl_s.close()

    return True

def plot3(TEAM1, game_data, our_stints, opponent_stints):
    
    global color_defaults 
    color_defaults = settings.colors
    
    global event_map
    event_map = get_event_map()

    matplotlib.rcParams.update(matplotlib.rcParamsDefault)
    if not do_plot('tools'):
        matplotlib.rcParams['toolbar'] = 'None' 

    if defaults.get('SAVE_RAW_GAME_AS_CSV'):
        def Merge(dict1, dict2): return {**dict1, **dict2}
        merged_game_stints = Merge(our_stints[0], opponent_stints[0])
        dump_pbp(game_data, merged_game_stints, do_raw=True)

    if defaults.get('SAVE_GAME_AS_CSV'):
        def Merge(dict1, dict2): return {**dict1, **dict2}
        merged_game_stints = Merge(our_stints[0], opponent_stints[0])
        dump_pbp(game_data, merged_game_stints)

    # top team = winner, bot_team = loser
    # home_team affects plus/minus and score 
    # VERIFY  home ahead is positive in plus/minus if ahead,  
  
    title, debug_title, game_info = get_title_and_friends(game_data)

    scoreMargins, home_scores, away_scores = make_scoremargin(game_data.play_by_play)
        
    boxscore1, playTimesbyPlayer1, events_by_player1 = \
    plot_prep(our_stints, game_data, scoreMargins, team=TEAM1, home_team=game_info['H'])

    boxscore2, playTimesbyPlayer2, events_by_player2 = \
    plot_prep(opponent_stints, game_data, scoreMargins, team=TEAM1, opponent=True, home_team=game_info['H'])
    
    do_stint = play_time_check(title, boxscore1, boxscore2, our_stints[0], opponent_stints[0],game_data)
    
    if not defaults.get('SHOW_PLOT'): logger.debug('Plot display disabled.')
    else:
        plt.style.use(color_defaults.get('PLOT_COLOR_STYLE'))
        figure,axd,E1,TL,TR,MD,E2,BL,BR,E3 = plot_layout(debug_title)

        # winning team goes on top 
        # TEAM1 is group1 data, opponennt is group2 data
        
        if game_info['T'] == TEAM1:
            _ad1_ = axd[TL]
            _ad2_ = axd[BL]
            _ad1_label = 'TOP'
            _ad2_label = None
        else :
            _ad1_ = axd[BL]
            _ad2_ = axd[TL]
            _ad1_label = None
            _ad2_label = 'TOP'
        
        b1 = boxscore1.shooting_percentages(boxscore1._team_name)
        b2 = boxscore2.shooting_percentages(boxscore2._team_name)

        ts1 = boxscore1.ts_percentage(boxscore1._team_name) 
        ts2 = boxscore2.ts_percentage(boxscore2._team_name)    
        
        bs_sum = [b1 + [ts1], b2 + [ts2]]

        box_scores_data_by_col = list(map(lambda x:x[0]+x[1],zip(boxscore1.get_colwidths(),boxscore2.get_colwidths())))

        colwidths = play_by_play_chart(playTimesbyPlayer1, _ad1_, events_by_player1, scoreMargins, 
                x_labels =_ad1_label,
                bx_score = boxscore1,
                bx_widths = box_scores_data_by_col,
                score = [home_scores, away_scores],
                game_info = game_info,
                bs_sum = bs_sum)
        
        play_by_play_chart(playTimesbyPlayer2, _ad2_, events_by_player2, scoreMargins, 
                    x_labels =_ad2_label,
                    bx_score = boxscore2,
                    bx_widths = colwidths,
                    score = [home_scores, away_scores],
                    game_info = game_info,
                    bs_sum = bs_sum)

        plot_title_legend_Qs(axd[E2],70,52, title, home_scores, away_scores, game_info)
        
        for r in [TL, TR, BL, BR, E1, E2, E3, MD]:
            if r != None:
                for s in ['top', 'right', 'bottom', 'left']:
                    axd[r].spines[s].set_visible(False)

        for r in [E3, TL, TR, BL, BR, MD]:
            if r != None:
                axd[r].title.set_visible(False)

        for r in [E1, E2, E3, TR, BR]:
            if r != None:
                axd[r].yaxis.set_visible(False)
                axd[r].xaxis.set_visible(False)
        
        plt.subplots_adjust(
            wspace=3, hspace=0.1, right=0.98, left=0.01, top=0.99, bottom=0.025
        )

        n = defaults.get('SHOW_PAUSE')
        if n == -1: plt.show(block=True)
        else: plt.pause(n) 
           
        if defaults.get('SAVE_PLOT_IMAGE'):
            img_type = defaults.get('SAVE_PLOT_TYPE')
            img_dpi  = defaults.get('SAVE_PLOT_DPI')

            cwd = os.getcwd() + '/' + defaults.get('SAVE_PLOT_DIR')
            t = game_data.matchup_home.split(' ')
            fn = f'{t[0]}v{t[2]}{game_data.game_date.replace('-','')}.{img_type}'
            
            if not(os.path.exists(cwd)): os.mkdir(cwd)

            fn = os.path.join(cwd, fn) 
            plt.draw()
            logger.info(f'saving image file {os.path.basename(fn)}')
            figure.savefig(fn, dpi=img_dpi)
            
        plt.close('all')

    if defaults.get('MAKE_BOX'): 
        box_score_dump(boxscore1,boxscore2,game_data)
            
    if defaults.get('SHOW_OVERLAP'): #team_abbreviation:
        overlap_dump(overlap_combos(our_stints), game_data, boxscore1)
        overlap_dump(overlap_combos(opponent_stints), game_data, boxscore2)

    if defaults.get('SAVE_STINTS_AS_CVS'):
        stints_as_csv(boxscore1,boxscore2,our_stints,opponent_stints ,game_data)

""  
