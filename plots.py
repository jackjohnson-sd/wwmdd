import re
import matplotlib.pyplot as plt
import matplotlib
from box_score import box_score,PM

from play_by_play import dump_pbp
from nba_colors import get_color, dimmer 
from event_prep import event_legend, event_to_size_color_shape

from settings import defaults 

STINT_C     = defaults.get('STINT_COLOR')       
BAD_EVNT    = defaults.get('BAD_EVENT_COLOR')    
GOOD_EVNT   = defaults.get('GOOD_EVENT_COLOR') 
GRID_C      = defaults.get('GRID_COLOR')
TABLE_C     = defaults.get('TABLE_COLOR')
TABLE_COLOR       = defaults.get('TABLE_COLOR')
STINT_COLOR_PLUS  = defaults.get('STINT_COLOR_PLUS')
STINT_COLOR_MINUS = defaults.get('STINT_COLOR_MINUS')

BOX_COL_COLOR     = defaults.get('BOX_COL_COLOR')
BOX_COL_COLOR_ALT = defaults.get('BOX_COL_COLOR_ALT')

MRK_FONTSCALE  = defaults.get('MARKER_FONTSCALE')
MRK_FONTWEIGHT = defaults.get('MARKER_FONTWEIGHT')
GRID_LINEWIDTH   = defaults.get('GRID_linewidth')

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

def stack_markers(yy_, sec_, color_):
    
    M2OFFSET       = defaults.get('MARKER_2_STACK_OFFSET')    # vertical offset for 2 markers at one place
    M3OFFSET       = defaults.get('MARKER_3_STACK_OFFSET')    # vertical offset for 3 markers at one place
    MKR_WIDTH      = defaults.get('MARKER_WIDTH')             # used to determine if markes will overlap
    
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

    return scoreMargins, home_scores, away_scores

def plot_score(_ax, home_scores, away_scores, game_team_desc):
    
    (our_team, opp_team, top_team, bot_team, home_team, away_team) = game_team_desc
    
    D1_color = dimmer(get_color(home_team))
    D2_color = dimmer(get_color(away_team))
       
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
    
def plot_scoremargin(_ax, _scoreMargins, flipper, _zorder, game_team_desc ):
    
    (our_team, opp_team, top_team, bot_team, home_team, away_team) = game_team_desc
    
    home_color = dimmer(get_color(home_team))
    away_color = dimmer(get_color(away_team))
    
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
    
    _colors = list(map(lambda x: away_color if x < 0 else home_color, _scoreMargins))

    _ax.scatter(range(0, len(_scoreMargins)), _scoreMargins, color=_colors, s=.01, zorder=_zorder)

def get_title_and_friends(game_data, boxscore):
    
    DATA_SOURCE    = defaults.get('SOURCE')
    debug_title = f'{game_data.game_id} {DATA_SOURCE}'
    
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

def plot_quarter_score(home_scores, away_scores, axis, x,y, game_team_desc):
    
    (our_team, opp_team, top_team, bot_team, home_team, away_team) = game_team_desc
        
    quarter_end  =  [12*60, 24*60,36*60,48*60]
    quarter_start = [0,     12*60,24*60,36*60]

    lxoffset = 100
    lx0 = x + lxoffset + 130
    lx1 = lx0 + lxoffset 
    lx2 = lx1 + lxoffset
    lx3 = lx2 + lxoffset
    lx4 = lx3 + lxoffset + 20
    
    ly0 = y + 8
    
    location = [
        [[x,ly0],[lx0,ly0],[lx1,ly0],[lx2,ly0],[lx3,ly0], [lx4,ly0]],
        [[x, y], [lx0,  y],[lx1,  y],[lx2, y], [lx3,  y], [lx4,  y]],
                ]

    def qs_text(x,y,text, _color):
        axis.text(x, y, s = text,
            color = _color, 
            size = 24 / MRK_FONTSCALE, 
            va = 'center_baseline', 
            ha = 'left' # 'center',
            # fontweight = MRK_FONTWEIGHT
        )
        
    top_co = get_color(top_team)
    bot_co = get_color(bot_team)
    
    top_data = home_scores if top_team == home_team else away_scores
    bot_data = away_scores if bot_team == away_team else home_scores
    
    qs_text(x, ly0, top_team, top_co)
    qs_text(location[0][-1][0], ly0, str(top_data[-1]), top_co)

    qs_text(x, y, bot_team, bot_co)
    qs_text(location[1][-1][0], y, str(bot_data[-1]), bot_co)

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

def plot_box_score(axis, box_score, players):
    
    bs_rows, bs_columns, bs_data = box_score.get_bs_data(players +  [box_score._team_name])
    trows = list(map(lambda x: shorten_player_name(x, 12), bs_rows))

    trows.reverse()
    bs_data.reverse()

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

    def make_column_widths(col_label, test_ax):

        # 3-4 free throws vs.  3 assists type data
        rx = '00-00' if col_label in ['FG','REB','3PT','FT'] else '000'

        # gets tick width
        t = test_ax.text(0, 0, s = rx, 
            size = 22 / MRK_FONTSCALE, 
            # fontweight = MRK_FONTWEIGHT
        )
        
        transf = axis.transData.inverted()
        bb = t.get_window_extent()
        bb_xy = bb.transformed(transf)
        t.remove()
        # return text width in as yet unknown units
        # funky as REB is last of the 00-00 columns others are 000
        # the .9 is so we have space on wither side
        # we use this to center our values under our column labels
        return (bb_xy.x1 - bb_xy.x0) + (-50 if col_label == 'REB' else 0.9)

    column_widths = [470] + list(map(lambda x:make_column_widths(x,axis),bs_columns))
   
    def plot_boxscore_row(start, y, row):
        for idx,r in enumerate(row):
            axis.text(start, y, s = r,
                color = colors_4_col[idx], 
                size = 24 / MRK_FONTSCALE, 
                va = 'center_baseline', 
                # player names go left
                ha = 'left' if idx == 0 else 'center',
                # fontweight = MRK_FONTWEIGHT
            )

            start += column_widths[idx]

    ROW_START = 2880 + 30

    # does the column headers
    plot_boxscore_row(ROW_START,-5 + len(trows) * 10,[''] + bs_columns)

    for i, bs in enumerate(bs_data):
        start = ROW_START 
        y = -5 + ((i) * 10)
        plot_boxscore_row(start, y,[trows[i]] + bs)

def plot_stints_events(axis, axis2, _y, play_times, events, flipper):
    starts = list(map(lambda x: x[0], play_times))
    widths = list(map(lambda x: x[1], play_times))
    pms    = list(map(lambda x: x[2], play_times))
    for j, x in enumerate(starts):
        start = x
        sc = STINT_C         
        if pms[j] > 2: sc = STINT_COLOR_PLUS if flipper else STINT_COLOR_MINUS
        elif pms[j] < -2: sc = STINT_COLOR_MINUS if flipper else STINT_COLOR_PLUS
        l = matplotlib.lines.Line2D([start, start + widths[j]], [_y, _y], lw = 1.0, ls= '-', c=sc)
        axis.add_line(l)                
    
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
                        size=size__[idx] / MRK_FONTSCALE, 
                        va = 'center_baseline', 
                        ha = 'center',
                        fontweight = MRK_FONTWEIGHT
                        )

def play_by_play_chart(playTimesbyPlayer, ax, events_by_player, scoreMargins, flipper, 
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
   
    _players = list(playTimesbyPlayer.keys())
    _player_cnt = len(_players)
    
    first_ytick = -5
    # +2 is header and team summary in table
    last_ytick = -5 + (10 * (_player_cnt + 2)) + 5

    ax.set_ylim(first_ytick , last_ytick)

    ax2 = ax.twinx()        
    ax2.set_ylim(first_ytick , last_ytick)
    ax2.yaxis.set_visible(False)

    ax3 = ax.twinx()

    for s in ['top', 'right', 'bottom', 'left']:
        ax3.spines[s].set_visible(False)
        ax2.spines[s].set_visible(False)    

    (our_team, opp_team, top_team, bot_team, home_team, away_team) = game_team_desc
    if bx_score._team_name == top_team:
        plot_score(ax3, score[0], score[1], game_team_desc)
    else:
        plot_scoremargin(ax3, scoreMargins, flipper, Z_SCRM, game_team_desc)
        plot_quarter_score(score[0], score[1], ax, 2000, (_player_cnt+1)*10, game_team_desc)
    
    for i, _player in enumerate(_players):
        
        events = events_by_player[_player]
        play_times = playTimesbyPlayer[_player]
        _y = -5 + ((_player_cnt - i) * 10)
         
        plot_stints_events(ax,ax2, _y, play_times, events, flipper)
        
    plot_box_score(ax2,bx_score,_players)
    
def plot_prep(our_stints, game_data, scoreMargins, team = None, opponent = False):

    our_stints_by_player = our_stints[0]
    boxscore = box_score(our_stints[1])

    if opponent:
        teams = set(game_data.play_by_play.player1_team_abbreviation.dropna().to_list()[0:10])
        teams.remove(team)
        try:    teams.remove('')
        except: a = 1
        
        team = list(teams)[0]

    boxscore.set_team_name(team)

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

def plot_layout(title):
    
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

    DATA_SOURCE    = defaults.get('SOURCE')
    SAVE_GAME_AS_CSV = defaults.get('SAVE_GAME_AS_CSV')

    if 'WEB:' in DATA_SOURCE and SAVE_GAME_AS_CSV == 'ON': dump_pbp(game_data)
    
    scoreMargins, home_scores, away_scores = make_scoremargin(game_data.play_by_play)
            
    boxscore1, playTimesbyPlayer1, events_by_player1, players1 = \
    plot_prep(our_stints, game_data, scoreMargins, team=TEAM1)

    boxscore2, playTimesbyPlayer2, events_by_player2, players2 = \
    plot_prep(opponent_stints, game_data, scoreMargins, team=TEAM1, opponent=True)

    title, debug_title, top_team, bot_team, home_team, away_team = \
    get_title_and_friends(game_data, boxscore1)

    # top team = winner, bot_team = loser
    # home_team - plus/minus and score 
    # home ahead is + plus, if away 
    # score plot shown for winner needs home/away teams for colors
    # plus minus the same thing
    
    plt.style.use(defaults.get('PLOT_COLOR_STYLE'))
    axd,E1,TL,TR,MD,E2,BL,BR,E3 = plot_layout(debug_title)

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
    play_by_play_chart(playTimesbyPlayer1, _ad1_, events_by_player1, scoreMargins, 
                 flipper  = _ad1_flip, 
                 x_labels =_ad1_label,
                 bx_score = boxscore1,
                 score = [home_scores, away_scores],
                 game_team_desc = team_desc
                 )

    boxscore2.plus_minus_flip(_ad2_flip)
    play_by_play_chart(playTimesbyPlayer2, _ad2_, events_by_player2, scoreMargins, 
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
        loc = 'center left', 
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
