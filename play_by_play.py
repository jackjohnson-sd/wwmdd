
from utils import secDiff

def dump_play_by_play(players,events,pbp):

    for player in players:
        print()
        print(player,' -----------------')
        subs = pbp[0].query(
            f'(eventmsgtype == 8) and (player1_name == "{player}" or player2_name == "{player}")'
            )
        if subs.shape[0] == 0: print('dump_play_by_play() Error A', player, e.eventnum, e.game_id)
        else:
            for key,e in subs.iterrows():
                print(
                    f'{e.period} {e.pctimestring:<5} IN:{e.player2_name:<20} OUT:{e.player1_name:<20} {e.homedescription}'
                )

def getTimeSpansByPlayer(games,players):
    _timeSpans = {}  # collect timespans played by this player
    for player in players:
        _timeSpans[player] = []
        for x in games.index:
            z = games.loc[x]
            p1 = z['player1_name']
            p2 = z['player2_name']
            if (p1 == player) or (p2 == player):
                t = 'IN' if p2 == player else "OUT"
                _timeSpans[player].append([t,z.period,z.pctimestring]) 
    return _timeSpans

def getTimeSpansByPlayerX(playbyplay, players):

    _timeSpans = {}  # collect timespans played by this player
    for player in players:
        _timeSpans[player] = []
     
        a_ = playbyplay['eventmsgtype'].isin([1,2,3,4,5,6,8])
        b_ = playbyplay['player1_name'] == player 
        c_ = playbyplay['player2_name'] == player
        ourPlayerEvents = playbyplay[a_ & (b_ | c_)]

        if player == 'Aaron Wiggins':
            t = ['period','pctimestring','eventmsgtype','player1_name','player2_name','homedescription','visitordescription']
            tmp = ourPlayerEvents[t]
            for i in t:
                print(f'{i[:10]:>10}  ',end= '')
            print()    
            for i, d in tmp.iterrows():
                for i in t:
                    print(f'{str(d[i])[:10]:>10}  ', end='')
                print()   

        inTheGame = False
        lastInGameEvent = -1

        initialEvent = ourPlayerEvents.iloc[0]
        if initialEvent.eventmsgtype != 8:
            if initialEvent.player1_name == player or initialEvent.player2_name == player:
                _timeSpans[player].append(['IN',int(initialEvent.period),'12:00']) 
                inTheGame = True

        for i, d in ourPlayerEvents.iterrows():
            period = int(d.period)
            pctimestring = str(d.pctimestring)
            match d.eventmsgtype:
                case 8 : # event is SUB IN or OUT
                    Entering = d.player2_name == player

                    if inTheGame: 
                        if Entering:
                            if lastInGameEvent != -1:
                                # we have an IN and we are already in and have events since last IN
                                # close off the last IN
                                _period = ourPlayerEvents.period.loc[[lastInGameEvent]].iloc[0]
                                _clock = ourPlayerEvents.pctimestring.loc[[lastInGameEvent]].iloc[0]
                                _timeSpans[player].append(['OUT', _period, _clock])
                            else:
                                # we have no events since our last IN
                                # close off last in at prior quarter end
                                lastIN = _timeSpans[player][-1]
                                if lastIN[0] == 'IN':
                                    _timeSpans[player].append(['OUT', lastIN[1], '0:00'])
                                else:
                                    print('OUCH',player,lastIN,period,pctimestring)

                            # start new span with an IN    
                            lastInGameEvent = -1
                            _timeSpans[player].append(['IN',period, pctimestring])
                        else:
                            # end span as we are leaving
                            inTheGame = False 
                            lastInGameEvent = -1
                            _timeSpans[player].append(['OUT',period,pctimestring])
                    else: # we are out
                        if Entering:
                            inTheGame = True
                            lastInGameEvent = -1
                            _timeSpans[player].append(['IN',period,pctimestring]) 
                        else:
                            print('WHAT  ',player,period,pctimestring)
                     
                case 1 | 2 | 3 | 4 |5 | 6:
                    
                    lastInGameEvent = i
                    if not inTheGame:
                        inTheGame = True
                        _timeSpans[player].append(['IN', period, '12:00']) 
                        # this happens when a player enters the game between periods
                        # set start of span to the beginning of this period
    

                case _ : print('-')

        lastEvent = ourPlayerEvents.iloc[-1]
        
        if lastEvent.eventmsgtype != 8:
            # not SUB message at end, end span at end of last period used
            _timeSpans[player].append(['OUT',int(lastEvent.period),'0:00']) 
        elif lastEvent.player2_name == player:
            # last message is IN end span at end of period used
            _timeSpans[player].append(['OUT',int(lastEvent.period),'0:00'])
               
    return _timeSpans

def checkScoreErrors(pbpEvents):
    sc1 = pbpEvents.query('eventmsgtype == 1 or eventmsgtype == 3')
    scores = list(filter(lambda x:x != None,sc1.score))
    score_errors = 0
    for x,y in zip(scores,scores[1:]):
        a = x.split(' - ')
        b = y.split(' - ')
        if a[0] == b[0]  :
            if a[1] == b[1]: 
                score_errors += 1
                print('ERROR A',x,y)
        else: 
            if a[1] != b[1]:
                score_errors += 1
                print('ERROR B',x,y) 
    return score_errors
    
def generatePBP(games_data):
   
    test_data, _start, _stop, _team, _season = games_data
 
    test_days = list(test_data.keys())

    starttime_duration_bydate = {}
    for date in test_days:

        starttime_duration_byPlayer = {}

        pbp_forDate = test_data[date].play_by_play[0]
        if pbp_forDate.shape[0] != 0:

            score_errors = checkScoreErrors(pbp_forDate)

            # player1 IN, player2 OUT 
            p1s = pbp_forDate.query('player1_team_abbreviation == "OKC"')['player1_name'] 
            p2s = pbp_forDate.query('player2_team_abbreviation == "OKC"')['player2_name']

            playersInGame = list(set(p1s) | set(p2s))       
            #######################################  [0:2]  ######## 
            # 8 substitution event, get our players thata are subbed IN/OUT
            pbp_subs = pbp_forDate #.query('eventmsgtype == 8') 
            timeSpans = getTimeSpansByPlayerX(pbp_subs, playersInGame)  # collect timespans played by this player

            for player in list(timeSpans.keys()):
                _tss = timeSpans[player]
                starttime_duration_byPlayer[player] = []

                if len(_tss) > 0:

                    lenTss = len(_tss)
                    for x,y in zip(range(0,lenTss,2),range(1,lenTss,2)):
                        start_ts  = _tss[x]
                        stop_ts   = _tss[y]
                        if start_ts[0] == 'IN' and stop_ts[0] == 'OUT':
                            ts = secDiff(start_ts,stop_ts)
                            starttime_duration_byPlayer[player].append([start_ts,ts,stop_ts])
                        else:
                            print('Error forming spans ',player,start_ts,stop_ts)   
            
            starttime_duration_bydate[date] = [starttime_duration_byPlayer,score_errors]

    return starttime_duration_bydate

"""
  if player == 'Ousmane Dieng':
    t = ['period','pctimestring','eventmsgtype','player1_name','player2_name','homedescription','visitordescription']
    tmp = ourPlayerEvents[t]
    for i in t:
        print(f'{i[:10]:>10}  ',end= '')
    print()    
    for i, d in tmp.iterrows():
        for i in t:
            #if type(d[i]) != type(None):
            print(f'{str(d[i])[:10]:>10}  ', end='')
        print()
"""                                                                                                                  