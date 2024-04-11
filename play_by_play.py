
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

def generatePBP(games_data):
   
    test_data, _start, _stop, _team, _season = games_data
 
    test_days = list(test_data.keys())

    starttime_duration_bydate = {}
    for date in test_days:

        starttime_duration_byPlayer = {}

        pbp_forDate = test_data[date].play_by_play[0]
        if pbp_forDate.shape[0] != 0:   

            sc1 = pbp_forDate.query('eventmsgtype == 1 or eventmsgtype == 3')
            scores = list(filter(lambda x:x != None,sc1.score))
            score_errors = 0
            for x,y in zip(scores,scores[1:]):
                a = x.split(' - ')
                b = y.split(' - ')
                if a[0] == b[0]  :
                    if a[1] == b[1]: 
                        score_errors += 1
                        #print('ERROR A',x,y)
                else: 
                    if a[1] != b[1]:
                        score_errors += 1
                        #print('ERROR B',x,y) 
            # 8 substitution event, get our players thata are subbed IN/OUT
            pbp_subs = pbp_forDate.query('eventmsgtype == 8') 

            # player1 IN, player2 OUT 
            p1s = pbp_subs.query('player1_team_abbreviation == "OKC"')['player1_name'] 
            p2s = pbp_subs.query('player2_team_abbreviation == "OKC"')['player2_name']

            playersInGame = list(set(p1s) | set(p2s))          
             
            timeSpans = getTimeSpansByPlayer(pbp_subs,playersInGame)  # collect timespans played by this player

            for player in list(timeSpans.keys()):
                _tss = timeSpans[player]
                starttime_duration_byPlayer[player] = []

                if len(_tss) > 0:

                    # our problem of the minute is lineup
                    # changes are not reported if they occur
                    # during stopage at end of period. so fix it by ...

                    # if first entry is OUT add IN at start of period
                    if _tss[0][0] == 'OUT':
                        _tss = [['IN',_tss[0][1],'12:00']] + _tss
                    # if last entry is IN add OUT at end of period     
                    if _tss[-1][0] == 'IN':
                        _tss.append(['OUT',_tss[-1][1],'0:00'])

                    # if we find two INs or OUTs together
                    # insert IN or OUT bettween them at the begining of period
                    insertsAdded = True    
                    while insertsAdded:
                        insertsAdded = False
                        lenTss = len(_tss)
                        for x in zip(range(0,lenTss),range(1,lenTss)):
                            ts1 = _tss[x[0]]
                            ts2 = _tss[x[1]]
                            if ts2[0] == ts1[0]:  # both INs or OUTs
                                if ts1[0] == 'IN':
                                    newTimeStamp = ['OUT', ts1[1], '00:00']
                                else: 
                                    newTimeStamp = ['IN',ts2[1],'12:00']
                                _tss.insert(x[1],newTimeStamp) 
                                #print(player,x)
                                insertsAdded = True
                                break
                    
                    lenTss = len(_tss)
                    for x,y in zip(range(0,lenTss,2),range(1,lenTss,2)):
                        start_ts  = _tss[x]
                        stop_ts   = _tss[y]
                        if start_ts[0] == 'IN' and stop_ts[0] == 'OUT':
                            ts = secDiff(start_ts,stop_ts)
                            #ts_str = str(timedelta(seconds=ts))
                            #print(f'{date} [{start_ts[0]:>2}, {start_ts[1]:>1}, {start_ts[2]:>5}], [{stop_ts[0]:>2}, {stop_ts[1]:>1}, {stop_ts[2]:>5}], {ts_str}')

                            starttime_duration_byPlayer[player].append([start_ts,ts,stop_ts])
                        else:
                            print('Error',player,x)   
            
            starttime_duration_bydate[date] = [starttime_duration_byPlayer,score_errors]

    return starttime_duration_bydate
