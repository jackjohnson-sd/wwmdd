
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime,timedelta

from utils import period_clock_seconds
from box_score import box_score

LABLE_SIZE = 9
COLWIDTH = .085
SCALE = .75

def eventToSize (player, eventRecord):

    SMALL_P = 15.0
    MID___P = 25.0
    LARGE_P = 50.0

    p1Name = eventRecord.player1_name
    p2Name = eventRecord.player2_name
    p3Name = eventRecord.player3_name
    
    _size = MID___P

    match eventRecord.eventmsgtype:
        case 1: # make
            if player == p1Name: 
                vis = eventRecord.homedescription
                hom = eventRecord.visitordescription
                if (str(vis) + str(hom)).find('3PT') != -1:
                    _size = MID___P
                else: _size = LARGE_P

        case 2: # miss
            _size = LARGE_P

        case 3: # free throw
            if player == p1Name:
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

    match eventRecord.eventmsgtype:
        case 1: # make
            if player == p1Name: color = _GOOD  # make
            if player == p2Name: color = _GOOD  # assist

        case 2: # miss
            if player == p1Name: color = _BAD    # miss
            if player == p3Name: color = _GOOD  # block

        case 3: # free throw
            if player == p1Name:
                color = _GOOD if type(eventRecord.score) == type('a') else _BAD

        case 4: #rebound
            if player == p1Name: 
                color = _GOOD

        case 5: # steal
            if player == p1Name: color = _BAD  # turnover
            if player == p2Name: color = _GOOD  # steal

        case 6: # foul
            if player == p1Name: color = _BAD  # turnover
            if player == p2Name: color = _GOOD  # steal

        case 8: # substitution    
            color = _MEH

        case _: color = _MEH

    return color

def shorter(what, max_length):
    if len(what) < max_length : return what
    half = int(len(what)/2)
    return what[0:half-2] + '...' + what[-(half-2):]

def plot3_PBPnChart(axd, boxscore, players, R, playTimesbyPlayer, L, events_by_player):  

    bs_rows, bs_columns, bs_data = boxscore.get_bs_data( players + ['TEAM'])
    tc = [['black'] * len(bs_columns)] * len(bs_rows)

    trows = list(map(lambda x:shorter(x,14), bs_rows))

    the_table = axd[R].table(
        cellText= bs_data, 
        cellColours=tc, 
        cellLoc='center', 
        colWidths=[COLWIDTH]*len(bs_columns), 
        rowLabels= trows, 
        #rowColours='k', 
        rowLoc='right', 
        colLabels=bs_columns, 
        #colColours='k', 
        colLoc='center', loc='center', edges='' )

    SCALE = 9/len(bs_rows)
    the_table.scale(1.0, SCALE)
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(LABLE_SIZE)

    print('rows', len(bs_rows),'lable size', LABLE_SIZE, 'SCALE', SCALE, 'COLWIDTH', COLWIDTH)

    labels = list(playTimesbyPlayer.keys())
    
    for i,label in enumerate(labels):

        data = playTimesbyPlayer[label]
        starts = list(map(lambda x:x[0],data))
        widths = list(map(lambda x:x[1],data))
        rects = axd[L].barh(label, widths, left=starts, color='plum', height=.15, zorder=3)
    
        axd[L].scatter(
            events_by_player[label][0::3],
            [i] * len(events_by_player[label][0::3]), 
            color = events_by_player[label][1::3], 
            s = events_by_player[label][2::3], 
            marker = ',',
            zorder = 3 )

    axd[L].invert_yaxis()
    axd[L].yaxis.set_visible(False)
    axd[L].set_xlim(-50, (48 * 60) + 50)
    axd[L].set_xticks([0,12*60,24*60,36*60,48*60],['','','','',''])
    
    axd[L].set_xticks([6*60, 18*60, 30*60,42*60], minor=True)
    axd[L].set_xticklabels(['Q1','Q2','Q3','Q4'],minor=True)
    # axd[L].set_yticks( range(0,len(labels)), labels)

    axd[L].tick_params(axis='y',which='major', labelsize=LABLE_SIZE, pad=0, direction='in')
    axd[L].tick_params(axis='x',which='minor', labelsize=LABLE_SIZE, pad=0, direction='in')
    axd[L].grid(True, axis = 'x', color='darkgrey', linestyle='-', linewidth=2, zorder=0)
    axd[L].tick_params(axis=u'both', which=u'both',length=0)
    # axd[L].yaxis.tick_right()

def plot3_prep(our_durations_by_date, game_data, play_by_play, HOME ,isOpponent):

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

    total_secs_playing_time = boxscore.sum_item('secs')
    t = str(timedelta(seconds=total_secs_playing_time)).split(':')

    debug_title = f'DEBUG {t[0]}:{t[1]}  {game_data.game_id}'
    title =f'{game_data.matchup_away} {int(game_data.pts_away)}-{int(game_data.pts_home)} {game_data.game_date[0:10]}'

    title = title + ' ' + debug_title

    if isOpponent:
        flipper = game_data.matchup_away.split(' ')[0] != HOME
    else:
        flipper = game_data.matchup_away.split(' ')[0] == HOME

    boxscore.plus_minus_flip(flipper)

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
        if not flipper: scoremargin = -scoremargin
        now = period_clock_seconds(['',v.period, v.pctimestring])
        scoreMargins.extend([lastscorevalue]*(now-lastscoretime-1))
        scoreMargins.extend([scoremargin])
        lastscoretime = now
        lastscorevalue = scoremargin

    playTimesbyPlayer = {}
    events_by_player = {}
    
    for player in players:

        usage = game[player]

        for i, stint in enumerate(usage):
            start = scoreMargins[stint[3]]
            stop = scoreMargins[stint[4]]
            boxscore.add_plus_minus(player, start, stop)

        def timespantoSecs(a):
            start = period_clock_seconds(a[0])            
            return  (int(start),int(a[1]))
        
        a = list(map(lambda x:timespantoSecs(x),usage))
        b = sum(list(map(lambda x:x[1],a) ))
        playTimesbyPlayer[player] = a

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

    boxscore.add_player('TEAM')
    for n in boxscore._bsItems:
        v = boxscore.sum_item(n)
        boxscore.update('TEAM',n,v)
    boxscore.clean()
    tmp = boxscore.get_item('TEAM','MIN') 
    boxscore.set_item('TEAM','MIN',tmp[0:5])

    return boxscore, playTimesbyPlayer, events_by_player, scoreMargins, title, players 

def plot3( our_durations_by_date, game_data, HOME_TEAM, play_by_play, opponent_durations):

    boxscore1, playTimesbyPlayer1, events_by_player1, scoreMargins1, title1, players1 = \
    plot3_prep(our_durations_by_date, game_data, play_by_play, HOME_TEAM ,False)

    boxscore2, playTimesbyPlayer2, events_by_player2, scoreMargins2, title2, players2 = \
    plot3_prep(opponent_durations, game_data, play_by_play, HOME_TEAM ,True)

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
    
    plot3_PBPnChart(axd, boxscore1, players1, TR, playTimesbyPlayer1, TL, events_by_player1)
    plot3_PBPnChart(axd, boxscore2, players2, BR, playTimesbyPlayer2, BL, events_by_player2)
 
    figure.canvas.manager.set_window_title(title1)

    _colors = list(map(lambda x:'red' if x < 0 else 'green'  ,scoreMargins1))
    axd[MD].scatter(range(0,len(scoreMargins1)),scoreMargins1, color=_colors, s=6)
    axd[MD].set_xlim(-50, (48 * 60) + 50)

    mx = abs(max(scoreMargins1))
    mi = abs(min(scoreMargins1))
    m = (max(mx,mi))
    m = 5 - (m % 5) + m 
    axd[MD].set_yticks( range(-m,m+5,10), list(range(-m,m+5,10)))
    # axd[MD].set_xticks([6*60, 18*60, 30*60,42*60], minor=True)
    # axd[MD].set_xticklabels(['Q1','Q2','Q3','Q4'], minor=True)
    axd[MD].set_xticks([0,12*60,24*60,36*60,48*60],['','','','',''])
    axd[MD].tick_params(axis=u'both', which=u'both', length=0, labelsize=0, pad=0)
    axd[MD].grid(True, axis = 'both', color='darkgrey', linestyle='-', linewidth=1, zorder=0)
    # axd[MD].yaxis.set_visible(False)

    axr = axd[MD].twinx()
    for s in ['top','right','bottom','left']:
        axr.spines[s].set_visible(False)

    axr.yaxis.set_visible(True)
    axr.tick_params(axis=u'both', which=u'both', length=0, labelsize=LABLE_SIZE, pad=3)
    axr.set_yticks( range(-m,m+5,10), list(range(-m,m+5,10)))
    axr.set_ylabel("plus/minus")

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
        
    
    plt.tight_layout()
    plt.subplots_adjust(wspace=15.3,hspace=.105,right=0.98, left=0.02,top=0.96, bottom=0.02)
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
 