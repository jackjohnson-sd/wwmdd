
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime,timedelta

from utils import period_clock_seconds
from box_score import box_score

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

# def plot3(game, title, play_by_play, debug_str,flipper):

# def plot3(game, title, play_by_play, debug_str,flipper):
def plot3( start_duration_by_date, game_data, HOME_TEAM, play_by_play):

    game = start_duration_by_date[0]
    boxscore = box_score(start_duration_by_date[1])

    players = list(game.keys())
    starters = []
    for player in players:
        if game[player][0][0] == ['IN',1,'12:00']:
            starters += [player]            
    bench = list(set(players) - set(starters))
    players = starters + bench

    # boxscore = box_score(start_duration_by_date[date][2])

    total_secs_playing_time = boxscore.sum_item('secs')
    t = str(timedelta(seconds=total_secs_playing_time)).split(':')
    debug_title = f'DEBUG {t[0]}:{t[1]}  {game_data.game_id}'

    title = f'{game_data.matchup_away} {int(game_data.pts_away)}-{int(game_data.pts_home)} {game_data.game_date[0:10]}'
    flipper = game_data.matchup_away.split(' ')[0] != HOME_TEAM
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
            # print(player,stint[3],stint[4],start,stop,stop-start)
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

    plt.style.use('dark_background')
    figure, axs = plt.subplots(2,1, figsize=(9.0,4.0))

    bs_rows, bs_columns, bs_data = boxscore.get_bs_data(starters + bench + ['TEAM'])
    tc = [['black'] * len(bs_columns)] * len(bs_rows)

    the_table = axs[1].table(
        cellText= bs_data, 
        cellColours=tc, 
        cellLoc='center', 
        colWidths=[.10]*len(bs_columns), 
        rowLabels=bs_rows, 
        #rowColours='k', 
        rowLoc='center', 
        colLabels=bs_columns, 
        #colColours='k', 
        colLoc='center', loc='center', edges='' )
    
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(9)

    axs[1].yaxis.set_visible(False)
    axs[1].xaxis.set_visible(False)

    axs[1].spines['top'].set_visible(False)
    axs[1].spines['right'].set_visible(False)
    axs[1].spines['bottom'].set_visible(False)
    axs[1].spines['left'].set_visible(False)

    labels = list(playTimesbyPlayer.keys())
 
    figure.canvas.manager.set_window_title(debug_title)
    ax = axs[0]
    
    ax.invert_yaxis()
    ax.yaxis.set_visible(True)
    ax.set_xlim(-100, (48 * 60) + 100)
    ax.set_xticks([0,12*60,24*60,36*60,48*60],['','','','',''])
    
    ax.set_title(title, fontsize=10)
    #ax.set_xlabel('periods')
    ax.set_xticks([6*60, 18*60, 30*60,42*60], minor=True)
    ax.set_xticklabels(['Q1','Q2','Q3','Q4'],minor=True)

    for i,label in enumerate(labels):

        data = playTimesbyPlayer[label]
        starts = list(map(lambda x:x[0],data))
        widths = list(map(lambda x:x[1],data))
        rects = ax.barh(label, widths, left=starts, color='plum', height=0.6, zorder=3)

        eventTimes = events_by_player[label][0::3]
        _colors = events_by_player[label][1::3] 
        __sizes = events_by_player[label][2::3]

        ax.scatter(eventTimes,[i] * len(eventTimes), color=_colors, s=__sizes , marker= ',',zorder=3 )

    y1, y2 = ax.get_ylim()
    x1, x2 = ax.get_xlim()
    ax2 = ax.twinx()
    #ax2.set_ylim(y1, y2)

    #ax2.set_yticks( range(0,len(player_minutes_played)),player_minutes_played )
    #ax2.tick_params(axis=u'both', which=u'both',length=0)
    _colors = list(map(lambda x:'red' if x < 0 else 'green'  ,scoreMargins))
    ax2.scatter(range(0,len(scoreMargins)),scoreMargins, color=_colors, s=6)
    ax2.set_yticks( range(-50,50,10), list(range(-50,50,10)))
    ax.tick_params(axis=u'both', which=u'both',length=0)
    
    #ax2.set_ylabel('minutes played')
    ax2.set_xlim(x1, x2)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)

    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['bottom'].set_visible(False)
    ax2.spines['left'].set_visible(False)

    ax.grid(True, axis = 'x', color='darkgrey', linestyle='-', linewidth=2, zorder=0)
    plt.tight_layout()
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
 