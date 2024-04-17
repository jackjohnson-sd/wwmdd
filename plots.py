
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime,timedelta

from utils import period_clock_seconds
from box_score import bs_stuff_bs, bs_clean, bs_dump, bs_get_bs_data


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

def plot3(game, title, play_by_play, debug_str):

    playTimesbyPlayer = {}
    sumByPlayer = {}
    events_by_player = {}

    players = list(game[0].keys())

    starters = []
    for player in players:
        if game[0][player][0][0] == ['IN',1,'12:00']:
            starters += [player]

    bench = list(set(players) - set(starters))
    
    for player in starters + bench:
        usage = game[0][player]

        def timespantoSecs(a):
            period = int(a[0][1]) - 1
            game_clock = datetime.strptime('12:00','%M:%S') -  datetime.strptime(a[0][2], '%M:%S')
            start = period * 12 * 60 + game_clock.total_seconds()
            duration = a[1]
            return  (int(start),int(duration))
        
        a = list(map(lambda x:timespantoSecs(x),usage))
        b = sum(list(map(lambda x:x[1],a) ))
        playTimesbyPlayer[player] = a
        sumByPlayer[player] = b

        _events = []

        plays_for_player = play_by_play[0].query(f'player1_name == "{player}" or player2_name == "{player}"or player3_name == "{player}"')

        for i,v in plays_for_player.iterrows():
            period = v.period
            clock = v.pctimestring
            event = v.eventmsgtype
        
            sec = period_clock_seconds(['',period,clock]).total_seconds()
            event_color = eventToColor(player, v)
            event_size = eventToSize(player, v)
            _events.append([int(sec), event_color, event_size])
        
        events_by_player[player] = _events             

    def timeToString(t): return str(timedelta(seconds = t))[2:]    

    team_minutes_played = list(map(lambda a :timeToString(a[1]),sumByPlayer.items()))
    
    plt.style.use('dark_background')
    figure, axs = plt.subplots(2,1,figsize=(9.2, 7))

    rows, columns, bs_data = bs_get_bs_data()
    tc = [['black'] * len(columns)] * len(rows)

    the_table = axs[1].table(
        cellText= bs_data, 
        cellColours=tc, 
        cellLoc='center', 
        colWidths=[.0700]*len(columns), 
        rowLabels=rows, 
        #rowColours='k', 
        rowLoc='center', 
        colLabels=columns, 
        #colColours='k', 
        colLoc='center', 
        loc='center', 
        edges=''
        )
    axs[1].yaxis.set_visible(False)
    axs[1].xaxis.set_visible(False)
    axs[1].spines['top'].set_visible(False)
    axs[1].spines['right'].set_visible(False)
    axs[1].spines['bottom'].set_visible(False)
    axs[1].spines['left'].set_visible(False)

    labels = list(playTimesbyPlayer.keys())
    _data = list(playTimesbyPlayer.values())
 
    figure.canvas.manager.set_window_title(debug_str)
    ax = axs[0]
    ax.invert_yaxis()
    ax.yaxis.set_visible(True)
    ax.set_xlim(-25, (48 * 60) + 25)
    ax.set_xticks([0,12*60,24*60,36*60,48*60],['','','','',''])
    ax.grid(True, axis='x')
    ax.set_title(title, fontsize=10)
    #ax.set_xlabel('periods')
    ax.set_xticks([6*60, 18*60, 30*60,42*60], minor=True)
    ax.set_xticklabels(['-- Quarter 1 --','Q2','Q3','Q4'],minor=True)

    for i,label in enumerate(labels):

        data = playTimesbyPlayer[label]
        starts = list(map(lambda x:x[0],data))
        widths = list(map(lambda x:x[1],data))
        rects = ax.barh(label, widths, left=starts, color='plum', height=0.6)

        eventTimes = list(map(lambda x:x[0],events_by_player[label]))
        _colors =  list(map(lambda x: x[1], events_by_player[label])) 
        __sizes = list(map(lambda x: x[2], events_by_player[label]))
        ax.scatter(eventTimes,[i] * len(eventTimes), color=_colors, s=__sizes )

    y1, y2 = ax.get_ylim()
    x1, x2 = ax.get_xlim()
    ax2 = ax.twinx()
    ax2.set_ylim(y1, y2)

    ax2.set_yticks( range(0,len(team_minutes_played)),team_minutes_played )
    ax2.set_ylabel('minutes played')
    ax2.set_xlim(x1, x2)
 
    #plt.tight_layout()
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
 