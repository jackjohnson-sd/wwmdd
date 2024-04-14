
from utils import secDiff

def dump_play_by_play(players,pbp):

    if players == []:
       players =  list(set(pbp.player1_name) | set(pbp.player2_name))

    for player in players:
        subs = pbp.query(
            f'(player1_name == "{player}" or player2_name == "{player}")'
            )
        if subs.shape[0] > 0:
            print()
            print(player,' -----------------')
            for key,e in subs.iterrows():
                p1 = '' if type(e.player1_name) == type(None) else e.player1_name
                p2 = '' if type(e.player2_name) == type(None) else e.player2_name
                desc = '' if type(e.homedescription) == type(None) else e.homedescription    
                if desc == '':  desc = '' if type(e.visitordescription) == type(None) else e.visitordescription
                if desc == '':  desc = '' if type(e.neutraldescription) == type(None) else e.neutraldescription
                print(
                    f'{e.period} {e.pctimestring:<5} {e.eventmsgtype} {p1:<20} {p2:<20} {desc}'
                )

def getTimeSpansByPlayerY(playbyplay, players):

    _timeSpans = {}  # collect timespans played by this player

    for player in players:

        _timeSpans[player] = []
     
        a_ = playbyplay['eventmsgtype'].isin([1,2,3,4,5,6,8])
        b_ = playbyplay['player1_name'] == player 
        c_ = playbyplay['player2_name'] == player
        ourPlayerEvents = playbyplay[a_ & (b_ | c_)]

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
                            if lastInGameEvent == -1:
                                # we've had no events, go to the last event 
                                lastEvent = _timeSpans[player][-1]
                                lperiod = lastEvent[1]
                                period_delta = period - lperiod
                                if lastEvent[0] == 'IN':
                                    if period_delta == 2 or period_delta == 1:
                                        _timeSpans[player].append(['OUT', lperiod, '0:00'])
                                        _timeSpans[player].append(['IN', period, '12:00'])

                            _timeSpans[player].append(['OUT', period, pctimestring])
                            inTheGame = False 
                            lastInGameEvent = -1
                                
                    else: # we are out
                        if Entering:
                            inTheGame = True
                            lastInGameEvent = -1
                            _timeSpans[player].append(['IN',period,pctimestring]) 
                        else:
                            print(f'LEAVING {player} Entering:{Entering} InTheGame:{inTheGame}  ',player,period,pctimestring)
                     
                case 1 | 2 | 3 | 4 | 5 | 6:
                    
                    if not inTheGame:
                        #if player == 'Aaron Wiggins' : print('IN ---',period,pctimestring)
                        # if not in game add an IN
                        inTheGame = True
                        _timeSpans[player].append(['IN', period, '12:00']) 
                        # this happens when a player enters the game between periods
                        # set start of span to the beginning of this period
                    elif lastInGameEvent == -1:
                        # this is our first event since IN
                         #if player == 'Aaron Wiggins' : print('E1 ---',period,pctimestring)
                         inEvnt = _timeSpans[player][-1]
                         if inEvnt[1] != period:
                             # we started in a prior period and we've had nothing 
                             secs = secDiff(inEvnt,['',period, pctimestring])
                             if secs > 3 * 60:
                                #print('prior IN set to where we are now')
                                #print('before',_timeSpans[player][-1])
                                _timeSpans[player][-1][1] = period
                                _timeSpans[player][-1][2] = '12:00'
                                #print('after',_timeSpans[player][-1])
                    else:
                        # we've already had events in this span
                        lEvent = ourPlayerEvents.loc[lastInGameEvent]
                        l_period = lEvent.period
                        l_clock  = lEvent.pctimestring
                        if l_period != period:
                            # we could have left at the prior period
                            secs = secDiff(['',l_period, l_clock],['',period, pctimestring])
                            if secs > 3 * 60: 
                                _timeSpans[player].append(['OUT', l_period, '00:00'])
                                _timeSpans[player].append(['IN', period, '12:00'])
                                # its been 3 minutes, we're in a new period
                                # Out at end of prior event period
                                # IN start of this period

                                aaa = 6
                    lastInGameEvent = i
                case _ : print('-*-*-*-*-*-*-*-*')

        lastEvent = ourPlayerEvents.iloc[-1]
        
        if lastEvent.eventmsgtype != 8:
            # not SUB message at end, end span at end of last period used
            _timeSpans[player].append(['OUT',int(lastEvent.period),'0:00']) 
        elif lastEvent.player2_name == player:
            # last message is IN end span at end of period used
            _timeSpans[player].append(['OUT',int(lastEvent.period),'0:00'])
               
    return _timeSpans

def getTimeSpansByPlayerX(playbyplay, players):

    _timeSpans = {}  # collect timespans played by this player

    for player in players:

        _timeSpans[player] = []
     
        a_ = playbyplay['eventmsgtype'].isin([1,2,3,4,5,6,8])
        b_ = playbyplay['player1_name'] == player 
        c_ = playbyplay['player2_name'] == player
        ourPlayerEvents = playbyplay[a_ & (b_ | c_)]

        inTheGame = False
        lastInGameEvent = -1
        lastPeriod = -1

        for i, d in ourPlayerEvents.iterrows():
            period = int(d.period)
            pctimestring = str(d.pctimestring)

            # on period change every one is out
            if period != lastPeriod:
                if lastPeriod != -1:
                    if _timeSpans[player][-1][0] != 'OUT':
                        _timeSpans[player].append(['OUT', lastPeriod, '0:00'])
                inTheGame = False
                lastPeriod = period
                lastInGameEvent = -1

            match d.eventmsgtype:
                case 8 : # event is SUB IN or OUT
                    Entering = d.player2_name == player

                    if inTheGame: 
                        if Entering:
                            # we're in and have a message saying we're in
                            print('We missed an OUT  ----- ')
                        else:
                            _timeSpans[player].append(['OUT', period,  pctimestring])
                            inTheGame = False 
                                
                    else: # we are not in the game last thing should be OUT
                        if Entering:
                            inTheGame = True
                            _timeSpans[player].append(['IN',period, pctimestring]) 
                        else:
                            # we have a leaving message and we're out
                            # set to starting at beginning of period
                            _timeSpans[player].append(['IN',period,'12:00'])
                            _timeSpans[player].append(['OUT',period, pctimestring])
                     
                case 1 | 2 | 3 | 4 | 5 | 6:
                    
                    if not inTheGame:
                        # if not in game add an IN at beggining of period
                        inTheGame = True
                        _timeSpans[player].append(['IN', period, '12:00']) 
                        # this happens when a player enters the game between periods
                        # set start of span to the beginning of this period

                case _ : print('-*-*-*-*-*-*-*-*')

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
                                                                                                                