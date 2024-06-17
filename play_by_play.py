from box_score import  box_score
import pandas as pd
from settings import defaults
from gemini import save_files
 
def getTimeSpansByPlayer(playbyplay, players):
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
                        _timeSpans[player].append(['OUT',(lastPeriod) * 720])

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
                            _timeSpans[player].append(['OUT', d.sec])
                            inTheGame = False 
                                
                    else: # we are not in the game last thing should be OUT
                        if Entering:
                            inTheGame = True
                            _timeSpans[player].append(['IN', d.sec])
                        else:
                            # we have a leaving message and we're out
                            # set to starting at beginning of period
                            _timeSpans[player].append(['IN',(period -1) * 720])
                            _timeSpans[player].append(['OUT', d.sec])
                     
                case 1 | 2 | 3 | 4 | 5 | 6:
                    
                    if not inTheGame:
                        # if not in game add an IN at beggining of period
                        inTheGame = True
                        _timeSpans[player].append(['IN', (period - 1) * 720]) 

                        # this happens when a player enters the game between periods
                        # set start of span to the beginning of this period

                case _ : print('-*-*-*-*-*-*-*-*')

        if len(ourPlayerEvents) > 0:
            lastEvent = ourPlayerEvents.iloc[-1]
            le_period = int(lastEvent.period)
            if lastEvent.eventmsgtype != 8:
                # not SUB message at end, end span at end of last period used
                _timeSpans[player].append(['OUT', le_period * 720]) 
            elif lastEvent.player2_name == player:
                # last message is IN end span at end of period used
                _timeSpans[player].append(['OUT',le_period * 720])

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
    
def period_clock_to_seconds(row):
    _period = int(row.period)
    _minsec = row.pctimestring.split(':')
    _secs =  (_period * 720) - (int(_minsec[0]) * 60) - int(_minsec[1])
    home_score = None
    away_score = None
    if row.score != '' and row.score != None:
        if row.score == '0': score = ['0','0']
        else: score = row.score.split('-')
        home_score = int(score[0])
        away_score = int(score[1])
    return _secs, home_score, away_score

def generatePBP(game_data, team_abbreviation, OPPONENT=False):

    pbp = game_data.play_by_play

    if  pbp.shape[0] != 0:
        
        # creates a computed column of seconds into game of event 
        pbp[['sec','score_home','score_away']] = pbp.apply(
            lambda row: period_clock_to_seconds(row), axis=1, result_type='expand'
        )

        #score_errors = checkScoreErrors(pbp)

        if OPPONENT:
            p1s = pbp.query(f'player1_team_abbreviation != "{team_abbreviation}"')['player1_name'] 
            p2s = pbp.query(f'player2_team_abbreviation != "{team_abbreviation}"')['player2_name']
        else:
            p1s = pbp.query(f'player1_team_abbreviation == "{team_abbreviation}"')['player1_name'] 
            p2s = pbp.query(f'player2_team_abbreviation == "{team_abbreviation}"')['player2_name']
        
        playersInGame = list(set(p1s.dropna()) | set(p2s.dropna()))

        # happens in csv read where we have a team rebound with no players
        if '' in playersInGame: playersInGame.remove('')
        
        boxSc = box_score({})
        boxSc.stuff_bs(game_data.play_by_play, playersInGame)

        timeSpans = getTimeSpansByPlayer(pbp, playersInGame)  # collect timespans played by this player
        
        stints_by_player = {}

        for player in timeSpans.keys():
            _tss = timeSpans[player]

            if len(_tss) > 0:

                stints_by_player[player] = []

                lenTss = len(_tss)
                _total_secs = 0
                for x,y in zip(range(0,lenTss,2),range(1,lenTss,2)):
                    start_ts  = _tss[x]
                    stop_ts   = _tss[y]
                    if start_ts[0] == 'IN' and stop_ts[0] == 'OUT':
                        _duration = stop_ts[1] - start_ts[1]
                        _total_secs += _duration
                        _start = start_ts[1]
                        _stop = stop_ts[1]
                        if OPPONENT :
                            if team_abbreviation != game_data.team_abbreviation_home:
                                team_abbreviation = game_data.team_abbreviation_home
                            
                                
                        stints_by_player[player].append([int(_duration) , int(_start), int(_stop),team_abbreviation])
                    else:
                        print('Error forming spans ',player,start_ts,stop_ts)  
                
                boxSc.update(player,'secs',_total_secs) 
                 
        return [stints_by_player, dict(boxSc.getBoxScore())]

    return [{},{}]

def _ms(_sec) : return pms(_sec).replace(' ',',')[1:]
        
def pms(_sec):  # p eriod m inute s econd
    
    q        = int(_sec / 720) + 1
    s_into_q = int(_sec % 720)
    m_into_q = s_into_q / 60
    s_into_m = int(s_into_q % 60)
    if s_into_m == 0:
        s_into_m = 60
    s = f'{q},{int(12-m_into_q):02d}:{int(60-s_into_m):02d}'
    return s

def save_starts(starts):
    
    def sfn(event):  
        when = _ms(event[1] if event[5] == 'I' else event[2])
        return (' ').join([when] + list(map(lambda a : str(a), event)))  
    
    f = ('\n').join(list(map(lambda a : sfn(a), starts)))  
    save_files('tmp.txt','_save_and_ignore',[['tmp.txt',f]])
   
def sub_fix(game_stints):

    results = []

    def leaving_game(event,idx,starts):
        found_out = False
        in_game = False
        for key in currents.keys():
            _current_player = currents[key]
            # match everything but I/O
            # if idx >= 37:
            #     print('current',_current_player[3:5])
            #     print('event',event)

            if _current_player[3:5] == event[3:5]:
                # currently playing enter matches our exit
                in_game = True
                # delete from currently playing
                del currents[key]
                
                # look in event list that came before
                priors = reversed(starts[0:idx])
                for j,prior in enumerate(priors):
                    
                    # for an I for our team
                    if prior[3] == event[3] and prior[5] == 'I':
                        # if idx >= 37:
                        #     print('prior',prior)
                        #     print('event',event)
                        # that enters the same as our exit
                        if prior[1] == event[2]:
                            
                            # tell the world we have an I/O pair
                            # str_in = f'{_current_player[4]:>20} {_ms(_current_player[1])} {_ms(_current_player[2])}'
                            # str_r =  f'{prior[4]:>20} {_ms(prior[1])} {_ms(prior[2])}'
                            # print(idx,pms(event[2]),f'IN {str_r}       OUT,{str_in}',)
                            
                            str_in = f'{_current_player[4]:>20} {_ms(_current_player[1])} {_ms(_current_player[2])}'
                            str_r =  f'{prior[4]:>20} {_ms(prior[1])} {_ms(prior[2])}'

                            p1_ln = prior[4].split(' ')[1]
                            p2_ln = _current_player[4].split(' ')[1]
                            s = f'SUB: {p1_ln} FOR {p2_ln}'
        
                            s1 = f'SUB,{pms(event[2])},{s},,,{prior[4]},{prior[3]},{_current_player[4]},{_current_player[3]},,'
                            results.extend([s1])
                         
                            # print(idx,f'SUB,{pms(event[2])},{s},,,{prior[4]},{prior[3]},{_current_player[4]},{_current_player[3]},,',)

                            # mark it as used
                            starts[idx - (j + 1)][3] = '***'
                            found_out = True
                            break
                break
            
        if not found_out: 
            if not in_game:
                print(idx,'        WARNING -- NOT IN GAME',event[4],event[3])
            else:
                # we have an out for some one who is not playing
                print(idx,'        WARNING -- NO HISTORY MATCH - LEFT WITHOUT ENTER',event[4],event[3])
           
    flattened_stints  = []
    for key in game_stints.keys():
        stints = game_stints[key]
        for stint in stints:
            stint += [key]
            flattened_stints.extend([stint])
            
    starts = sorted(flattened_stints, key=lambda stint: stint[1]) 
    starts = list(map(lambda x:x +['I'],starts))
    ends   = sorted(flattened_stints, key=lambda stint: stint[2]) 
    ends   = list(map(lambda x:x +['O'],ends))
    
    starts = starts + ends
    def fn(stint): return stint[1] if stint[5] == 'I' else stint[2]
    starts = sorted(starts, key=lambda stint: fn(stint)) 
    
    save_starts(starts)
    
    currents = {}
    now = pms(starts[0][1])
    
    then_start = 0
    then = starts[0][1] if starts[0][5] == 'I' else starts[0][2]
    
    for i,d in enumerate(starts):
    
        #[376, 0, 376, 'OKC', 'Chet Holmgren', 'I'] duration,start,end,player,direction

        now = d[1] if d[5] == 'I' else d[2]
        if now != then:
            # print(list(range(then_start,i)))
                    
            for m in range(then_start,i):
                d = starts[m]
                if d[5] == 'I': 
                    # print('Enter',d[4])
                    if d[4] in currents.keys():
                        currents[d[4]][2] = d[2]
                        currents[d[4]][0] += d[0]
                    else: 
                        if len(list(currents.keys())) < 10:
                            p1_ln = d[4].split(' ')[1]
                            s = f'SUB: {p1_ln} Enters'
                            s1 = f'SUB,{pms(d[1])},{s},,,{d[4]},{d[3]},,,,'
                            results.extend([s1])
                            # print(i,s1)

                            # print(i,_ms(d[1]),f'IN {d[4]},{d[3]}')

                        currents[d[4]] = d.copy()

            for m in range(then_start,i):
                d = starts[m]
                if d[5] == 'O': 
                    # is an Input for this Output
                    # in our group of simultaneous events
                    # if so ignore the exit
                    fi = False
                    for x in range(then_start,i):
                        # check is I for our
                        if starts[x][5] == 'I':
                            # check its our name
                            if starts[x][4] == d[4]: 
                                # print('in for out in our group')
                                # print(x,'|',starts[x],d)
                                fi = True
                                break
                    if not fi:     
                        # not an in/out pair        
                        leaving_game(d,i,starts)

            then_start = i
            then = now

    for key in currents.keys():
        d = currents[key]
        q = int(d[2] / 720) 
        s = f'{q},00:00'
        
        ln = d[4].split(' ')[1]
        f = f'SUB: {ln} Exits.'
        s1 = f'SUB,{s},{f},,,,,{d[4]},{d[3]},,'
        print(i,s1)
        results.extend([s1])

    f = ',eventmsgtype,period,pctimestring,neutraldescription,score,scoremargin,player1_name,player1_team_abbreviation,player2_name,player2_team_abbreviation,player3_name,player3_team_abbreviation' + \
        ('\n,').join(results)  
    
    save_files('subs.csv','_save_and_ignore',[['subs.csv',f]])

    return results

def dump_pbp(game, game_stints):
    
    # ds = sub_fix(game_stints)
    # return

    pbp_event_map = {
        1: [['POINT', 'ASSIST'],  [1, 2]],  # make, assist
        2: [['MISS', 'BLOCK'],    [1, 3]],
        3: [['FREETHROW', ''],    [1]   ],  # free throw
        4: [['REBOUND', ''],      [1]   ],  # rebound
        5: [['STEAL', 'TURNOVER'],[2, 1]],
        6: [['FOUL',''],          [1]   ],
        7: [['VIOLATION',''],     [1,2]   ],
        8: [['SUB', ''],          [1]   ],  # substitution
        9: [['TIMEOUT', ''],      [1]   ],  # time out
        
        10: [['JUMPBALL', ''],   [1,2,3] ],  # jump ball
        11: [['EJECTION', ''],    [1]   ],  # 
        12: [['STARTOFPERIOD', ''], [1]   ],  # START of period
        13: [['ENDOFPERIOD', ''], [1]   ],  # END of period
    }
    keys = list(pbp_event_map.keys())
    stuff = []
    lastScore = 0
    lastScoreMargin = 0
    for i,p in game.play_by_play.iterrows():
        event = p.eventmsgtype 
        if event in keys:
            emap = pbp_event_map[event]
            desc = str(p.homedescription) + str(p.neutraldescription) + str(p.visitordescription)
            desc = desc.replace('None','')
            if p.score == None:
                p.score = lastScore
                p.scoremargin = lastScoreMargin
            else:
                lastScore = p.score
                lastScoreMargin = p.scoremargin
            match = False   
            if event == 1:
                match = True   
                if p.player2_name != None:
                    event_name = '.'.join(emap[0])
                else:    
                    event_name = emap[0][0]
                if '3PT' in desc:
                    event_name = '3' + event_name
                else:
                    event_name = '2' + event_name
           
            elif event == 4:
                event_name = emap[0][0]
                match = True
                    
            elif event == 2:
                match = True
                if p.player3_name != None:
                    event_name = '.'.join(emap[0])
                else:    
                    event_name = emap[0][0]

                e = '3POINT' if '3PT' in desc else '2POINT'
                event_name = e + event_name
                    
            elif event == 3:
                event_name = emap[0][0]  
                match = True
                event_name = 'FTMISS' if 'MISS' in desc else 'FTMAKE'
                
            elif event == 6:
                event_name = emap[0][0]  
                match = True
                
            elif event == 5:
                match = True
                if p.player2_name != None:
                    event_name = '.'.join(emap[0])
                else:    
                    event_name = emap[0][1]

            elif event == 8: 
                event_name = emap[0][0]
                match = True

            elif event in [7,9,10,11,12,13]:
                event_name = emap[0][0]
                match = True

            if match:
                a = [
                    event_name,
                    p.period, 
                    p.pctimestring,
                    desc,
                    p.score,
                    p.scoremargin,
                    p.player1_name, p.player1_team_abbreviation,
                    p.player2_name, p.player2_team_abbreviation,
                    p.player3_name, p.player3_team_abbreviation
                    ]
                stuff.extend([a])
                    
    new_cols = [
        'eventmsgtype',
        'period', 
        'pctimestring',
        'neutraldescription',
        'score',
        'scoremargin',
        'player1_name', 'player1_team_abbreviation',
        'player2_name', 'player2_team_abbreviation',
        'player3_name', 'player3_team_abbreviation'
    
    ]
    play_by_play = pd.DataFrame(
            data    = stuff,           # values
            # index   = oink [1:,0],    # 1st column as index
            columns = new_cols)  
            
    f = play_by_play.to_csv()

    t = game.matchup_home.split(' ')

    import os
    cwd = os.getcwd() + '/' + defaults.get('SAVE_GAME_DIR')
    
    fn = f'{t[0]}v{t[2]}{game.game_date.replace('-','')}.csv'
    fn = os.path.join(cwd, fn) 
    
    # test/make dir for csv (BES)
    if not(os.path.exists(cwd)):
        os.mkdir(cwd)   
    
    fl=open(fn,"w")
    fl.write(f)
    fl.close()

    a = 1
                                                                                                               