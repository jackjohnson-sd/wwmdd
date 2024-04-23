import pandas as pd
import numpy as np
import itertools

import matplotlib.pyplot as plt
from datetime import datetime,timedelta

from utils import period_clock_seconds
from box_score import box_score

LABLE_SIZE = 9
COLWIDTH = .09
SCALE = .75

def eventToSize (player, eventRecord):

    SMALL_P = 10.0
    MID___P = 20.0
    LARGE_P = 30.0

    p1Name = eventRecord.player1_name
    
    _size = MID___P

    players = [player] if type(player) != type([]) else player

    match eventRecord.eventmsgtype:
        case 1: # make
            if p1Name in players: 
                vis = eventRecord.homedescription
                hom = eventRecord.visitordescription
                if (str(vis) + str(hom)).find('3PT') != -1:
                    _size = MID___P
                else: _size = LARGE_P

        case 2: # miss
            _size = LARGE_P

        case 3: # free throw
            if p1Name in players:
                _size = MID___P
        
        case _: _size = SMALL_P
       
    return _size

def eventToColor (player, eventRecord):
    """                          player1      player2    player3 
        events  1 = make         shooter      assist 
                2 = miss         shooter                 block
                3 = Free throw   shooter      score = NULL if miss else changed score
                4 = rebound
                5 = steal        turn over    stealer
                6 = foul         fouled       fouler
                8 = SUB          OUT          IN
                10  jump ball    jumper1      jumper2    who got the ball
    """
    
    _MEH = 'yellow'
    _GOOD = 'lime'
    _BAD = 'red'

    color = _MEH

    p1Name = eventRecord.player1_name
    p2Name = eventRecord.player2_name
    p3Name = eventRecord.player3_name

    players = [player] if type(player) != type([]) else player
     
    match eventRecord.eventmsgtype:
        case 1: # make
            if p1Name in players: color = _GOOD  # make
            if p2Name in players: color = _GOOD  # assist

        case 2: # miss
            if p1Name in players: color = _BAD    # miss
            if p3Name in players: color = _GOOD  # block

        case 3: # free throw
            if p1Name in players:
                color = _GOOD if type(eventRecord.score) == type('a') else _BAD

        case 4: #rebound
            if p1Name in players: 
                color = _GOOD

        case 5: # steal
            if p1Name in players: color = _BAD  # turnover
            if p2Name in players: color = _GOOD  # steal

        case 6: # foul
            if p1Name in players: color = _BAD  # turnover
            if p2Name in players: color = _GOOD  # steal

        case 8: # substitution    
            color = _MEH

        case _: color = _MEH

    return color

def shorter(what, max_length):
    if len(what) < max_length : return what
    half = int(len(what)/2)
    return what[0] + '. ' + what.split(' ')[1] 
    return what[0:half-2] + '...' + what[-(half-2):]

def plot3_boxscore(boxscore, ax, players):

    bs_rows, bs_columns, bs_data = boxscore.get_bs_data( players + ['TEAM'])
    tc = [['black'] * len(bs_columns)] * len(bs_rows)
    trows = list(map(lambda x:shorter(x,14), bs_rows))
    
    cws = [COLWIDTH]*len(bs_columns)
    cws[2] *= 1.2

    # cws[4:9] *= 09

    the_table = ax.table(
        cellText    = bs_data, 
        cellColours = tc, 
        cellLoc     = 'center', 
        colWidths   = cws, #[COLWIDTH]*len(bs_columns), 
        rowLabels   = trows, 
        #rowColours='k', 
        rowLoc      = 'right', 
        colLabels   = bs_columns, 
        #colColours='k', 
        colLoc      = 'center', loc = 'center', edges= '' )

    SCALE = 9/len(bs_rows)
    the_table.scale(1.0, SCALE)
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(LABLE_SIZE)

def plot3_PBP_chart(playTimesbyPlayer, ax, events_by_player):  

    labels = list(playTimesbyPlayer.keys())
    
    for i,label in enumerate(labels):

        data = playTimesbyPlayer[label]
        starts = list(map(lambda x:x[0],data))
        widths = list(map(lambda x:x[1],data))
        rects = ax.barh(label, widths, left=starts, color='plum', height=.15, zorder=3)
    
        ax.scatter(
            events_by_player[label][0::3],
            [i] * len(events_by_player[label][0::3]), 
            color = events_by_player[label][1::3], 
            s = events_by_player[label][2::3], 
            marker = ',',
            zorder = 3 )

    ax.invert_yaxis()
    ax.yaxis.set_visible(False)
    ax.set_xlim(-50, (48 * 60) + 50)
    ax.set_xticks([0,12*60,24*60,36*60,48*60],['','','','',''])
    
    ax.set_xticks([6*60, 18*60, 30*60,42*60], minor=True)
    ax.set_xticklabels(['Q1','Q2','Q3','Q4'],minor=True)

    ax.tick_params(axis='y',which='major', labelsize=LABLE_SIZE, pad=0, direction='in')
    ax.tick_params(axis='x',which='minor', labelsize=LABLE_SIZE, pad=0, direction='in')
    ax.grid(True, axis = 'x', color='darkgrey', linestyle='-', linewidth=2, zorder=0)
    ax.tick_params(axis=u'both', which=u'both',length=0)

def plot3_stints(playTimesbyPlayer, ax, events_by_player):  

    labels = list(playTimesbyPlayer.keys())
    
    for i,label in enumerate(labels):

        data = playTimesbyPlayer[label]
        starts = list(map(lambda x:x[0],data))
        widths = list(map(lambda x:x[1],data))
        rects = ax.barh(str(label), widths, left=starts, color='plum', height=.5, zorder=3)
    
        # ax.scatter(
        #     events_by_player[label][0::3],
        #     [i] * len(events_by_player[label][0::3]), 
        #     color = events_by_player[label][1::3], 
        #     s = events_by_player[label][2::3], 
        #     marker = ',',
        #     zorder = 3 )

    ax.invert_yaxis()
    ax.yaxis.set_visible(False)
    ax.set_xlim(-50, (48 * 60) + 50)
    ax.set_xticks([0,12*60,24*60,36*60,48*60],['','','','',''])
    
    ax.set_xticks([6*60, 18*60, 30*60,42*60], minor=True)
    ax.set_xticklabels(['Q1','Q2','Q3','Q4'],minor=True)

    ax.tick_params(axis='y',which='major', labelsize=LABLE_SIZE, pad=0, direction='in')
    ax.tick_params(axis='x',which='minor', labelsize=LABLE_SIZE, pad=0, direction='in')
    ax.grid(True, axis = 'x', color='darkgrey', linestyle='-', linewidth=1, zorder=0)
    ax.tick_params(axis=u'both', which=u'both',length=0)

def plot_3_MID(ax, scoreMargins,flipper):

    if flipper:
        scoreMargins = list(map(lambda x:-x,scoreMargins))    
    _colors = list(map(lambda x:'red' if x < 0 else 'lime' ,scoreMargins))
    ax.scatter(range(0,len(scoreMargins)),scoreMargins, color=_colors, s=4)
    ax.set_xlim(-50, (48 * 60) + 50)

    mx = abs(max(scoreMargins))
    mi = abs(min(scoreMargins))
    m = (max(mx,mi))
    m = 5 - (m % 5) + m 
    ax.set_yticks( range(-m,m+5,10), list(range(-m,m+5,10)))
    # axd[MD].set_xticks([6*60, 18*60, 30*60,42*60], minor=True)
    # axd[MD].set_xticklabels(['Q1','Q2','Q3','Q4'], minor=True)
    ax.set_xticks([0,12*60,24*60,36*60,48*60],['','','','',''])
    ax.tick_params(axis=u'both', which=u'both', length=0, labelsize=0, pad=0)
    ax.grid(True, axis = 'both', color='darkgrey', linestyle='-', linewidth=1, zorder=0)
    # axd[MD].yaxis.set_visible(False)

    axr = ax.twinx()
    for s in ['top','right','bottom','left']:
        axr.spines[s].set_visible(False)

    axr.yaxis.set_visible(True)
    axr.tick_params(axis=u'both', which=u'both', length=0, labelsize=LABLE_SIZE, pad=3)
    axr.set_yticks( range(-m,m+5,10), list(range(-m,m+5,10)))
    axr.set_ylabel("teams +/-'")

def get_score_margin(play_by_play):
     # create scoremargin for every second of the game all 14400 = 60 * 12 * 4
    # this is an issue when OT comes along  // TODO 
    # score margin is 'TIE' otherwise +/- difference of score. TIE set to 0 for us
    # like most other data elements its None if it is not changed
    scoreMargins = [0]
    lastscoretime = 0
    lastscorevalue = 0
    
    z = play_by_play.scoremargin.dropna().index
    for i,v in play_by_play.loc[z].iterrows():
        scoremargin = v.scoremargin
        if scoremargin == 'TIE': scoremargin = 0
        scoremargin = int(scoremargin)
        # if not flipper: scoremargin = -scoremargin
        now = period_clock_seconds(['',v.period, v.pctimestring])
        scoreMargins.extend([lastscorevalue]*(now-lastscoretime-1))
        scoreMargins.extend([scoremargin])
        lastscoretime = now
        lastscorevalue = scoremargin
    
    return scoreMargins
   
def get_title(game_data, boxscore):
    total_secs_playing_time = boxscore.sum_item('secs')
    t = str(timedelta(seconds=total_secs_playing_time)).split(':')

    debug_title = f'DEBUG {t[0]}:{t[1]}  {game_data.game_id}'
    title =f'{game_data.matchup_away} {int(game_data.pts_away)}-{int(game_data.pts_home)} {game_data.game_date[0:10]}'
    title = title + ' ' + debug_title
    return title

def plot3_prep(our_durations_by_date, play_by_play, scoreMargins):

    game = our_durations_by_date[0]
    boxscore = box_score(our_durations_by_date[1])

    players = list(game.keys())
    starters = []
    for player in players:
        if len(game[player]) > 0:
            if game[player][0][0] == ['IN',1,'12:00']:
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
            return  (int(start),int(a[1]))
        
        playTimesbyPlayer[player] = list(map(lambda x:timespantoSecs(x), game[player]))

        _events = []

        plays_for_player = play_by_play.query(f'player1_name == "{player}" or player2_name == "{player}"or player3_name == "{player}"')

        for i,v in plays_for_player.iterrows():
            period = v.period
            clock = v.pctimestring
            event = v.eventmsgtype
        
            sec = period_clock_seconds(['',period,clock])
            event_color = eventToColor(player, v)
            event_size = eventToSize(player, v)
            _events.extend([int(sec), event_color, event_size])
        
        events_by_player[player] = _events             

    boxscore.make_summary()

    return boxscore, playTimesbyPlayer, events_by_player, players 

def plot3_lineup_prep(playTimesbyPlayer, play_by_play, boxscore_, scoreMargins):

    # create stints by line_up, we have play times per player
    players = list(playTimesbyPlayer)
    
    stints_by_player = []
    for player in players:
        stints = playTimesbyPlayer[player]
        for stint in stints:
            stint_start = int(stint[0])
            stint_duration = int(stint[1])
            stints_by_player.extend([[stint_start,stint_duration,player]])
    
    def line_up_abbr(lineup_):
        import re
        # just get the CAPS in the names players to make lineup name
        def _lu_small(name_): 
            return re.sub('[^A-Z]', '', name_)        
        l_key = list(map(lambda x:_lu_small(x),lineup_))
        l_key.sort()
        return '-'.join(l_key)

    boxscore = box_score({})
    events_by_lineup = {}

    # create stints by line up
    # flattend player stints are sorted by time of stint start
    # after you have 5 in the next stint cause some one to leave
    # and some one to enter.  The enter starts a new stint and
    # the leaving one close off at this time. Add it to the list 
    # of stints for this line and save this time as the start of
    # the next stint

    stints_by_lineup = {}
    players_in_lineup = {}

    data_by_lineup = {}
    
    current_lineup = []
    last_start = 0
    
    for player_stint in sorted(stints_by_player, key=lambda x: x[0]):
        if len(current_lineup) != 5:
            current_lineup.extend([player_stint])
        else:
            broke = False
            player_names = list(np.array(current_lineup)[:,2])
            key = line_up_abbr(player_names)
            for _player in current_lineup:
                if _player[0] + _player[1] == player_stint[0]:
                    if key in list(stints_by_lineup.keys()):
                        if player_stint[0]-last_start > 0:
                            # print('extend', last_start, player_stint[0]-last_start,key)
                            stints_by_lineup[key].extend([[last_start,player_stint[0] -last_start]])
                    else:
                        if player_stint[0] - last_start > 30:
                            stints_by_lineup[key] = [[last_start, player_stint[0]-last_start]]
                            players_in_lineup[key] = player_names.copy()
                            # print('start', last_start, stint[0] - last_start, key)
                  
                    last_start = player_stint[0]
                    
                    current_lineup.remove(_player)
                    current_lineup.extend([player_stint])
                    broke = True
                    break

            if not broke: 
                print('---not found',_player,last_start,current_lineup )        
  
    for line_up in stints_by_lineup:

        players_in_lineup = players_in_lineup[line_up]
        stints_in_lineup = stints_by_lineup[line_up]
        
        # create an unattached column with an index
        play_by_play['sec'] = play_by_play.apply(lambda row: period_clock_seconds(['',row.period, row.pctimestring]), axis=1)

        a_ = play_by_play['player1_name'].isin(players_in_lineup)
        b_ = play_by_play['player2_name'].isin(players_in_lineup)
        c_ = play_by_play['player3_name'].isin(players_in_lineup)

        def fx__(row):
            sec = row.sec
            for stint in stints_in_lineup:
                if sec > stint[0] and sec < stint[0] + stint[1]:
                    return True
            return False
        
        e_ = play_by_play.apply(lambda row: fx__(row), axis = 1)

        plays_this_stint_this_player = play_by_play[a_ | b_ |c_ & e_ ]

        events_by_lineup = []
        for i,v in plays_this_stint_this_player.iterrows():
            ec = eventToColor(players_in_lineup, v)
            es = eventToSize(players_in_lineup, v)
            events_by_lineup.extend([v.sec, ec, es])

        secs_total_this_lineup =  sum(np.array(stints_in_lineup)[:,1])

        def sm(x): 
            return scoreMargins[x[0]] - scoreMargins[x[0] + x[1]]
        stintMargin_this_lineup = sum(list(map(lambda x:sm(x),stints_by_lineup[line_up])))

        for player in players_in_lineup:
            boxscore.stuff_bs(plays_this_stint_this_player, [player])

        boxscore.make_summary()
        bs_rows, bs_columns, bs_data = boxscore.get_bs_data(['TEAM'])
        bs_data[0][bs_columns.index('+/-')] = stintMargin_this_lineup
        bs_data[0][bs_columns.index('MIN')] = secs_total_this_lineup
        data_by_lineup[line_up] = bs_data[0]
    
    bx = boxscore(data_by_lineup)
    #return boxscore, playTimesbyPlayer, events_by_player, players 
    return bx, stints_by_lineup

def plot3( our_durations_by_date, game_data, HOME_TEAM, play_by_play, opponent_durations):

    scoreMargins = get_score_margin(play_by_play)

    boxscore1, playTimesbyPlayer1, events_by_player1, players1 = \
    plot3_prep(our_durations_by_date, play_by_play, scoreMargins)

    # stints_by_lineup = plot3_lineup_prep(
    #     playTimesbyPlayer = playTimesbyPlayer1, 
    #     play_by_play = play_by_play, 
    #     boxscore_    = our_durations_by_date[1],
    #     scoreMargins = scoreMargins)

    boxscore2, playTimesbyPlayer2, events_by_player2, players2 = \
    plot3_prep(opponent_durations, play_by_play, scoreMargins)

    title = get_title(game_data, boxscore1)

    flipper = title[0:3] == HOME_TEAM

    boxscore1.plus_minus_flip(not flipper)
    boxscore2.plus_minus_flip(flipper)

    plt.style.use('dark_background')

    E1 = None 
    TL = '2'
    TR = '3'
    MD = '4'
    E2 = '5'
    BL = '6'
    BR = '7'
    E3 = None
    
    layout = [
        [TL, TL,TL,TL,TL, TL, TR,TR,TR,TR],
        [MD, MD,MD,MD,MD, MD, E2,E2,E2,E2],
        [BL, BL,BL,BL,BL, BL, BR,BR,BR,BR],
        ]
    
    figure, axd = plt.subplot_mosaic(layout, figsize=(10.0,6.0), )
    figure.canvas.manager.set_window_title(title)
    
    axd[TL].sharey(axd[TR])
    # axd[BL].sharey(axd[BR])
    
    plot3_boxscore(boxscore1, axd[TR], players1)
    plot3_boxscore(boxscore2, axd[BR], players2)

    # plot3_stints(stints_by_lineup, axd[BL], None)
    plot3_PBP_chart(playTimesbyPlayer1, axd[TL], events_by_player1)
    plot3_PBP_chart(playTimesbyPlayer2, axd[BL], events_by_player2)
 
    plot_3_MID(axd[MD], scoreMargins, flipper)

    for r in [E1,E2,E3,TL,TR,BL,BR,MD]:
        if r != None:
            for s in ['top','right','bottom','left']:
                axd[r].spines[s].set_visible(False)

    for r in [E1,E2,E3,TL,TR,BL,BR,MD]:
        if r != None:
            axd[r].title.set_visible(False)
    
    for r in [E1,E2,E3,TR,BR]:
        if r != None:
            axd[r].yaxis.set_visible(False)    
            axd[r].xaxis.set_visible(False)    
        
    # plt.tight_layout()
    plt.subplots_adjust(wspace=35, hspace=.2, right=.98, left=0.00, top=0.95, bottom=0.05)
    plt.show()

    plt.close('all')

def plot2(data):
        
    _data = data.filter(['play_by_play','pts_home'])  
    _data['play_by_play'] = _data['play_by_play'].apply(
        lambda x: 15 if x.shape[0] == 0 else x.shape[0])

    #  convert the index to datetime
    #  reindex! so we get spaces on dates with no game
    _data.index = pd.DatetimeIndex(_data.index)
    _data = _data.reindex(pd.date_range(_data.index[0], _data.index[-1]), fill_value=15)
    _data.index = _data.index.strftime('%b %d')

    fig, ax = plt.subplots()    
    
    for l in _data:
        ax.bar(_data.index, list(_data[l]), label= l)  

    plt.xticks(rotation=90)
    ax.set_xticks(ax.get_xticks()[::7])
    ax.legend(loc =2, title='PBP Data',ncols=3)

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
    ax.legend(loc =2, title='',ncol=2)
    return
 