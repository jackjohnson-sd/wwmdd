from utils import secDiff
from box_score import  box_score

def getTimeSpansByPlayer(playbyplay, players, boxscore):

    # collect timespans played by this player
    # also calculate +/- for each player stint
    _timeSpans = {}  
        
    for player in players:

        _timeSpans[player] = []
     
        a_ = playbyplay['eventmsgtype'].isin([1,2,3,4,5,6,8])
        b_ = playbyplay['player1_name'] == player 
        c_ = playbyplay['player2_name'] == player
        ourPlayerEvents = playbyplay[a_ & (b_ | c_)]
  
        inTheGame = False
        lastPeriod = 1

        for i, d in ourPlayerEvents.iterrows():

            period = int(d.period)
            pctimestring = str(d.pctimestring)

            # on period change every one is out
            if period != lastPeriod:
                if len(_timeSpans[player]) == 0:
                    # we had no action in the first period
                    a = 1
                else:
                    if _timeSpans[player][-1][0] != 'OUT':
                        _timeSpans[player].append(['OUT', lastPeriod, '0:00'])

                inTheGame = False
                lastPeriod = period

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
        le_period = int(lastEvent.period)
        if lastEvent.eventmsgtype != 8:
            # not SUB message at end, end span at end of last period used
            _timeSpans[player].append(['OUT',le_period,'0:00']) 
        elif lastEvent.player2_name == player:
            # last message is IN end span at end of period used
            _timeSpans[player].append(['OUT',le_period,'0:00'])

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
    
def generatePBP(games_data,team_abbreviation):
   
    test_days = list(games_data.keys())

    starttime_duration_bydate = {}

    for date in test_days:

        starttime_duration_byPlayer = {}

        pbp_forDate = games_data[date].play_by_play[0]

        if pbp_forDate.shape[0] != 0:

            #score_errors = checkScoreErrors(pbp_forDate)

            p1s = pbp_forDate.query(f'player1_team_abbreviation == "{team_abbreviation}"')['player1_name'] 
            p2s = pbp_forDate.query(f'player2_team_abbreviation == "{team_abbreviation}"')['player2_name']
            playersInGame = list(set(p1s) | set(p2s))

            boxSc = box_score({})
            boxSc.stuff_bs(games_data[date].play_by_play[0], playersInGame)

            timeSpans = getTimeSpansByPlayer(pbp_forDate, playersInGame, boxSc)  # collect timespans played by this player

            for player in timeSpans.keys():

                starttime_duration_byPlayer[player] = []
                _tss = timeSpans[player]

                if len(_tss) > 0:

                    lenTss = len(_tss)
                    for x,y in zip(range(0,lenTss,2),range(1,lenTss,2)):
                        start_ts  = _tss[x]
                        stop_ts   = _tss[y]
                        if start_ts[0] == 'IN' and stop_ts[0] == 'OUT':
                            ts,start,stop = secDiff(start_ts,stop_ts)
                            starttime_duration_byPlayer[player].append([start_ts,ts,stop_ts,start,stop])
                        else:
                            print('Error forming spans ',player,start_ts,stop_ts)  
                 
                secs = sum(list(map(lambda x:x[1],starttime_duration_byPlayer[player])))
                boxSc.update(player,'secs',secs) 

            starttime_duration_bydate[date] = [starttime_duration_byPlayer, dict(boxSc.getBoxScore())]

    return starttime_duration_bydate
                                                                                                                