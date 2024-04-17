from utils import secDiff
from box_score import bs_add_plus_minus, bs_stuff_bs, bs_clean, bs_dump, bs_update, bs_getBoxScore

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

def getTimeSpansByPlayer(playbyplay, players):

    _timeSpans = {}  # collect timespans played by this player
        
    for player in players:

        _timeSpans[player] = []
     
        a_ = playbyplay['eventmsgtype'].isin([1,2,3,4,5,6,8])
        b_ = playbyplay['player1_name'] == player 
        c_ = playbyplay['player2_name'] == player
        ourPlayerEvents = playbyplay[a_ & (b_ | c_)]
  
        inTheGame = False
        lastPeriod = 1
        q_start_scoremargins = [0,0,0,0,0,0,0]
        last_scoremargin   = 0

        for i, d in ourPlayerEvents.iterrows():

            period = int(d.period)
            pctimestring = str(d.pctimestring)

            scoremargin = d.scoremargin
            if scoremargin == None:  scoremargin = last_scoremargin
            if scoremargin == 'TIE': scoremargin = 0
            scoremargin = int(scoremargin)

            # on period change every one is out
            if period != lastPeriod:
                q_start_scoremargins[period] = scoremargin
                if len(_timeSpans[player]) == 0:
                    # we had no action in the first period
                    a = 1
                else:
                    if _timeSpans[player][-1][0] != 'OUT':
                        _timeSpans[player].append(['OUT', lastPeriod, '0:00'])
                        bs_add_plus_minus(player, start_margin, scoremargin)

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
                            bs_add_plus_minus(player, start_margin, scoremargin)

                            inTheGame = False 
                                
                    else: # we are not in the game last thing should be OUT
                        if Entering:
                            inTheGame = True
                            _timeSpans[player].append(['IN',period, pctimestring])
                            start_margin = last_scoremargin 
                        else:
                            # we have a leaving message and we're out
                            # set to starting at beginning of period
                            start_margin = q_start_scoremargins[period-1]
                            bs_add_plus_minus(player, start_margin, scoremargin)
                            _timeSpans[player].append(['IN',period,'12:00'])
                            _timeSpans[player].append(['OUT',period, pctimestring])
                     
                case 1 | 2 | 3 | 4 | 5 | 6:
                    
                    if not inTheGame:
                        # if not in game add an IN at beggining of period
                        inTheGame = True
                        _timeSpans[player].append(['IN', period, '12:00']) 
                        start_margin = q_start_scoremargins[period - 1]

                        # this happens when a player enters the game between periods
                        # set start of span to the beginning of this period

                case _ : print('-*-*-*-*-*-*-*-*')

            last_scoremargin = scoremargin

        lastEvent = ourPlayerEvents.iloc[-1]
        le_period = int(lastEvent.period)
        if lastEvent.eventmsgtype != 8:
            # not SUB message at end, end span at end of last period used
            _timeSpans[player].append(['OUT',le_period,'0:00']) 
            bs_add_plus_minus(player, q_start_scoremargins[le_period], scoremargin)
        elif lastEvent.player2_name == player:
            # last message is IN end span at end of period used
            bs_add_plus_minus(player, q_start_scoremargins[le_period], scoremargin)
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

            bs_stuff_bs(test_data[date].play_by_play[0], playersInGame)

            timeSpans = getTimeSpansByPlayer(pbp_forDate, playersInGame)  # collect timespans played by this player

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
                 
                secs = sum(list(map(lambda x:x[1],starttime_duration_byPlayer[player])))
                bs_update(player,'secs',secs) 

            starttime_duration_bydate[date] = [starttime_duration_byPlayer, score_errors, dict(bs_getBoxScore())]

    return starttime_duration_bydate
                                                                                                                