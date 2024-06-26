from box_score import box_score
import pandas as pd
from settings import defaults
from gemini import save_files
 
TEST_PLAYERS  = defaults.get('TEST_PLAYERS')   
SAVE_RAW_GAME_AS_CSV = defaults.get('SAVE_RAW_GAME_AS_CSV')

def period(sec) : return int(sec / 720) + 1

def period_time_to_sec(period,mmss): 
    # period 1:4, mmss 1:23 1 minute 23 seconds left in period
    _period = int(period)
    _minsec = mmss.split(':')
    _secs =  (_period * 720) - (int(_minsec[0]) * 60) - int(_minsec[1])
    return _secs

def sec_to_period_time(sec):

    p = int(sec / 720)
    
    remaining_secs = int(sec) - p * 720
    remaining_minutes = int(remaining_secs / 60)
    remaining_secs = int(sec - p * 720 - remaining_minutes * 60)  

    if remaining_secs == 0:# and remaining_minutes == 0:
        remaining_secs = 60
    else:
        remaining_minutes += 1
        
    remaining_secs = 60 - remaining_secs
    remaining_minutes = 12 - remaining_minutes
    
    return f'{p+1} {remaining_minutes}:{remaining_secs:02d}'

def _ms(_sec) : return pms(_sec).replace(' ',',')[1:]
        
def pms(_sec):  # p eriod m inute s econd
    
    q        = int(_sec / 720) + 1
    s_into_q = int(_sec % 720)
    m_into_q = s_into_q / 60
    s_into_m = int(s_into_q % 60)
    if s_into_m == 0: s_into_m = 60
    if m_into_q == 0 and s_into_m == 60:
        m_into_q = 12
        q -= 1
    s = f'{q},{int(12-m_into_q)}:{int(60-s_into_m):02d}'
    return s

def getTimeSpansByPlayer(playbyplay, player_group, needs_spans_fixed = True):
    # collects timespans played by these players

    start_time = 'UNNKNOWN'
    
    _sub_events_by_player = {}
    
    a_ = playbyplay['eventmsgtype'].isin([1,2,3,4,5,6,8])
    a1_ = playbyplay['eventmsgtype'].isin([12,13])
    
    b_ = playbyplay['player1_name'].isin(player_group)
    c_ = playbyplay['player2_name'].isin(player_group)
    d_ = playbyplay['player3_name'].isin(player_group)
    
    our_events = playbyplay[((a_ & (b_ | c_ | d_)) | a1_)]
    
    # we're looking at all events for this player
    # in the NBA data players who enter or exit 
    # between 1-2,2-3,3-4 period are not reported
    # We find then because they show up with playing events
    # while not in the game.
    
    in_the_game = False
    last_event = None
    players_in_period_count = 0
    
    for i, d in our_events.iterrows():
                    
        if d.eventmsgtype == 13: # ENDOFPERIOD
            
            # print(f'ENDOFPERIOD {players_in_period_count} players set OUT, {int(pms(d.sec)[0])}')
            
            players_in_period_count = 0
            
            for player in _sub_events_by_player:
                if needs_spans_fixed:
                    events = _sub_events_by_player[player]
                    if len(events) > 0:
                        
                        last_event = _sub_events_by_player[player][-1] 
                        
                        if last_event[0] == 'IN':
                            events.append(['OUT',int(pms(d.sec)[0]) * 720,'P change'])                        
        
        # 12: # STARTOFPERIOD
        elif  d.eventmsgtype == 12: 
            if d.eventmsgtype == 12:                    
                s = d.neutraldescription
                start_time = s[s.find('(')+1:s.find(')')]
        else:    
            
            period = int(d.period)
            pctimestring = str(d.pctimestring)

            p1_name = d.player1_name
            p2_name = d.player2_name

            pls = []
            if p1_name in player_group: pls.extend([p1_name])
            if p2_name in player_group: pls.extend([p2_name])
            
            for player in pls:
                
                if player not in _sub_events_by_player.keys(): _sub_events_by_player[player] = []
                
                _sub_event_for_player = _sub_events_by_player[player]
                
                in_the_game = False
                last_event = None
                
                if len(_sub_event_for_player) > 0: 
                    
                    last_event = _sub_event_for_player[-1]
                    
                    # our last event was IN from sub or other
                    in_the_game = last_event[0] == 'IN'
                    
                if player in TEST_PLAYERS:
                    print(period,pctimestring,d.eventmsgtype,'p1:',p1_name,'p2:',p2_name,d.visitordescription)  
            
                match d.eventmsgtype:

                    case 12: pass # STARTOFPERIOD
                    case 13: pass # ENDOFPERIOD  

                    case 8 : # event is SUB IN or OUT or BOTH
                        # p2 entering player, p1 leaving player, both optional
                        p2_entering = p2_name == player
                        
                        if p2_entering:
                            
                            if not in_the_game:
                                            
                                _sub_event_for_player.append(['IN', d.sec,'SUB in.'])
                                     
                            elif player in TEST_PLAYERS:
                                print(f'{player} {pms(d.sec)} Entered when IN the game.')
                        
                        p1_leaving = p1_name == player                
                        
                        if p1_leaving:
                                
                            # p1 is exiting the game, 'OUT'
                            if not in_the_game:

                                # we get this when forced out at a period change
                                # and did not have another event until then
                                if last_event == None:
                                    # came in at period break for first time, did nothing 
                                    # and left before next period break
                                    pmss = sec_to_period_time(d.sec)

                                    _sub_event_for_player.append(['IN', (int(pmss[0]) - 1) * 720, 'Enter in'])
                                    _sub_event_for_player.append(['OUT', d.sec,'Leave via SUB'])
                            
                                else:
                                    # if last message was out from period change
                                    is_out = last_event[0] == 'OUT'  
                                    is_period_change_time = last_event[1] == (period-1) * 720
                                    
                                    if is_out and is_period_change_time :
                                        # set last out to now, so it extends over the period break
                                        last_event[1] = d.sec
                                        last_event[2] = 'extending out over period change'
                                    else:    
                                        if is_out:
                                            pmss = sec_to_period_time(d.sec)

                                            _sub_event_for_player.append(['IN', (int(pmss[0]) - 1) * 720, 'Enter in'])
                                            _sub_event_for_player.append(['OUT', d.sec,'Leave via SUB'])
                                        
                                            # pass # for now
                                            # if player in TEST_PLAYERS:
                                            #     print(f'{player} {d.sec} Exit when NOT IN the game.')
                            else:
                                # we are in the game and subbed out during period, everthing OK
                                _sub_event_for_player.append(['OUT', d.sec,'SUB out'])                         
                            
                    case 1 | 2 | 3 | 4 | 5 | 6:
                        
                        if d.sec % 720 == 0:
                            # this happens when an event occuus with < 1 sec on the clock
                            # don't do anything about in or out
                            # print(player,d.sec,d.period,d.pctimestring)
                            continue
                        
                        if d.eventmsgtype == 6: #FOUL
                            ttm = ''
                            try: 
                                ttm += str(d.neutraldescription) 
                                ttm += str(d.homedescription) 
                                ttm += str(d.visitordescription) 
                            except : pass
                            
                            if 'T.FOUL' in ttm:
                                if not in_the_game: continue
                            
                        if not needs_spans_fixed: continue
                                            
                        if not in_the_game:

                            lastEvent = None if len(_sub_event_for_player) == 0 else _sub_event_for_player[-1]
                            
                            if lastEvent == None:
                                # first time this player shows up non sub in/out
                                # could happen if a period change force out and 
                                # player has a event, treat as enter at change
                                # we're lost if already 5 guys in
                                if players_in_period_count < 5:
                                    
                                    players_in_period_count += 1
                                    _sub_event_for_player.append(['IN', (period-1) * 720,'First non SUB in' ])
                                                                
                                else:
                                    print('Error',player,sec_to_period_time(d.sec),'non SUB ins > 5.')
                            else:
                                
                                """
                                case 1 prior event out from kicked out at period break
                                        (i.e. OCCURED at period break times)
                                        delete the prior event, an out and set us to inTheGame at start 
                                
                                case 2 prior event not from kick out 
                                        (i.e. did NOT OCCUR at period break times)
                                        this is an error
                                """
                                
                                if lastEvent[0] == 'OUT':
                                    
                                    # outed at last period break?
                                    if lastEvent[1] == (period-1) * 720: 
                                        # kicked out prior period break, .pop returns us to IN
                                        _sub_event_for_player.pop()
                                        # print(f'{player} POP {sec_to_period_time(last_event[1])}')
                                        players_in_period_count += 1
                                    else:
                                        # out more than one period ago
                                        # Non SUB event without an enter,
                                        # set to in at start of current period
                                        _sub_event_for_player.append(['IN', (period-1) * 720,'NON SUB while NOT in game']) 
                                                                        # last out NOT at the begining of this period?
                                        # print(f'ReEnter from period change, {d.eventmsgtype}',player,sec_to_period_time(d.sec))
            
                                else:
                                    # last event was an 'IN' ?
                                    print('ERROR X',player)
                                    pass    

                    # case _ : print('-*-*-*-*-*-*-*-*')
    
    # send players 'OUT' at end of game
    if needs_spans_fixed:
        
        for player in  _sub_events_by_player.keys():
            
            events = _sub_events_by_player[player]
            if len(events) > 0:
                last_event = events[-1] 
                if last_event[0] == 'IN':

                    pmss = sec_to_period_time(last_event[1])
                    _sub_events_by_player[player].append(['OUT', ((int(pmss[0])) * 720),'EndOfGame All IN go out']) 
                            
    return _sub_events_by_player, start_time

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
    
def seconds_plus_home_away_scores(row):
    _secs = period_time_to_sec(row.period,row.pctimestring)

    home_score = None
    away_score = None
    if row.score != '' and row.score != None:
        if row.score == '0': score = ['0','0']
        else: score = row.score.split('-')
        home_score = int(score[0])
        away_score = int(score[1])
    return _secs, home_score, away_score

def generatePBP(game_data, team_abbreviation, OPPONENT=False, needs_subs_fixed = True):

    pbp = game_data.play_by_play

    if  pbp.shape[0] != 0:
        
        # creates a computed column of seconds into game of event 
        pbp[['sec','score_home','score_away']] = pbp.apply(
            lambda row: seconds_plus_home_away_scores(row), axis=1, result_type='expand'
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
        boxSc.stuff_bs(pbp, playersInGame)
        
        timeSpans, start_time = getTimeSpansByPlayer(pbp, playersInGame)  # collect timespans played by this player
        
        if OPPONENT :
            if team_abbreviation != game_data.team_abbreviation_home:
                team_abbreviation = game_data.team_abbreviation_home
            else:
                team_abbreviation = game_data.team_abbreviation_away
                
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
                        
                        stints_by_player[player].append([int(_duration) , int(_start), int(_stop),team_abbreviation])
                    else:
                        print('Error forming spans ',player,start_ts,stop_ts)  
                
                boxSc.update(player,'secs',_total_secs) 

        game_data.start_time = start_time       
        return [stints_by_player, dict(boxSc.getBoxScore())]

    return [{},{}], start_time

def stint_sort_key(stnt): return stnt[1] if stnt[4] == 'I' else stnt[2]

def save_starts(starts):
    
    def sfn(event):  
        when = pms(stint_sort_key(event))
        return (',').join([when] + list(map(lambda a : str(a), event)))  
    
    f = ('\n').join(list(map(lambda a : sfn(a), starts)))  
    save_files('InsAndOuts.csv','_save_and_ignore',[['InsAndOuts.csv',f]])

def clean_stints(game_stints):
        
    for player in game_stints:
        stints = game_stints[player]
        
        starts = sorted(stints, key=lambda stint: stint[1]) 
        starts = list(map(lambda x:x +['I'],starts))
        
        ends   = sorted(stints, key=lambda stint: stint[2]) 
        ends   = list(map(lambda x:x +['O'],ends))
        
        ins_and_outs = starts + ends
        
        ins_and_outs = sorted(ins_and_outs, key=lambda stint: stint_sort_key(stint)) 
        
        kills = []
        for i,(s1,s2) in enumerate(zip(ins_and_outs,ins_and_outs[1:])):
            if s1[4] == s2[4]:  # 2 I's or O's in a row
                if s1[2] == s2[1]: # our end is next guys start
                    # set end on the first to end of the seconds
                    # then kill the last
                    ins_and_outs[i][2] = ins_and_outs[i+1][2]
                    ins_and_outs[i][0] += ins_and_outs[i+1][0]
                    kills.extend([i+1])
                else:
                    print('NO MATCH ON STOP -> START', player)
                    print('x  ',ins_and_outs[i])
                    print('x+1',ins_and_outs[i+1])
                
        if len(kills) > 0:        
            starts_not_killed = [v for i,v in enumerate(ins_and_outs) if i not in frozenset(kills)] 
            game_stints[player] = starts_not_killed
        else:
            game_stints[player] = ins_and_outs

def make_sub_events(game_stints):
    
    sub_events = []

    for player in game_stints.keys():
        stints = game_stints[player]
        for this_in_out in stints:
            this_in_out += [player]
            player_name = this_in_out[5]
            team_name = this_in_out[3]
            # print(team_name,player_name,this_in_out)
            p1_ln = player_name.split(' ')[1]
            if this_in_out[4] == 'I':
                x1 = sec_to_period_time(this_in_out[1]).replace(' ',',')
                s1 = f'SUB,{x1},SUB: {p1_ln} Enters,,,,,{player_name},{team_name},,'
            else:
                # x2 = sec_to_period_time(this_in_out[2]).replace(' ',',')
                x2 = pms(this_in_out[2])
                # home of the 5,12:00 problem
                s1 = f'SUB,{x2},SUB: {p1_ln} Exits,,,{player_name},{team_name},,,,'
  
            sub_events.extend([s1])
            
    return  sub_events
    
def sub_events_from_stints(game_stints):
    
    # game_stints has in/outs for all players
    # go through each stints for player 
    # reduce consecutive ins or outs to one by setting
    # the end of the first to the end of the second
    # then removing the second
    # return sorted list of SUB events 
    
    clean_stints(game_stints)
    
    sub_events = make_sub_events(game_stints)
            
    def sub_event_to_sec(sub):
        s = sub.split(',')
        return period_time_to_sec(s[1],s[2])
        
    sub_events = sorted(sub_events, key = lambda stint: sub_event_to_sec(stint))

    if False:
        f = ',eventmsgtype,period,pctimestring,neutraldescription,score,scoremargin,player1_name,player1_team_abbreviation,player2_name,player2_team_abbreviation,player3_name,player3_team_abbreviation\n,' + \
            ('\n,').join(sub_events)  
        
        save_files('subs.csv','_save_and_ignore',[['subs.csv',f]])

    return list(map(lambda x:x.split(','),sub_events))

def dump_pbp(game, game_stints):
    
    period_end_score = {}    
    
    save_as_raw = SAVE_RAW_GAME_AS_CSV == 'ON'
    
    sub_events = [] if save_as_raw else sub_events_from_stints(game_stints)
    
    pbp_event_map = {
        1: [['POINT', 'ASSIST'],  [1, 2],],  # make, assist
        2: [['MISS', 'BLOCK'],    [1, 3],],
        3: [['FREETHROW', ''],    [1]   ,],  # free throw
        4: [['REBOUND', ''],      [1]   ,],  # rebound
        5: [['STEAL', 'TURNOVER'],[2, 1],],
        6: [['FOUL',''],          [1]   ,],
        7: [['VIOLATION',''],     [1,2] ,],
        8: [['SUB', ''],          [1]   ,],  # substitution
        9: [['TIMEOUT', ''],      [1]   ,],  # time out
        
        10: [['JUMPBALL', ''],    [1,2,3],], # jump ball
        11: [['EJECTION', ''],    [1]   ,],  # 
        12: [['STARTOFPERIOD', ''],[1]  ,],  # START of period
        13: [['ENDOFPERIOD', ''], [1]   ,],  # END of period
    }
    
    keys = list(pbp_event_map.keys())
    
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
            event_name = emap[0][0]
            
            if event == 8: match = save_as_raw
            
            # point.assist
            if event == 1:
                match = True   
                if p.player2_name != None: event_name = '.'.join(emap[0])
                s = '3' if '3PT' in desc else '2'
                event_name = s + event_name
            
            # miss.block        
            elif event == 2:
                match = True
                if p.player3_name != None: event_name = '.'.join(emap[0])
                e = '3POINT' if '3PT' in desc else '2POINT'
                event_name = e + event_name

            # free throw        
            elif event == 3:
                match = True
                event_name = 'FTMISS' if 'MISS' in desc else 'FTMAKE'

            # steal.turnover    
            elif event == 5:
                match = True
                if p.player2_name != None: event_name = '.'.join(emap[0])
                
            elif event == 13:
                tk = f'{p.period+1}:12:00'
                period_end_score[tk] = [p.score, p.scoremargin]
                # print(tk,period_end_score[tk])
                match = True

            # foul, rebound plus others, NO 8 i.e. subs
            elif event in [4,6,7,9,10,11,12,13]: match = True

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
                sub_events.extend([a])
            
    if not save_as_raw:
        sub_events = sorted(sub_events,key = lambda x:event_sort_keys(x))
    
    # find our sub events that do not have score, margin set
    for i in range(0,len(sub_events)):
                
        # if we find an event in need
        if sub_events[i][4] == '':
            j = i
            # go up stream until we have a score
            while sub_events[j][4] == '': 
                if j == 0: break
                j -= 1

            # if we're at the begining it must be 0    
            sub_events[i][4] = 0 if j == 0 else sub_events[j][4]
            sub_events[i][5] = 0 if j == 0 else sub_events[j][5]
    
    new_cols = [
        'eventmsgtype',
        'period', 'pctimestring',
        'neutraldescription',
        'score', 'scoremargin',
        'player1_name', 'player1_team_abbreviation',
        'player2_name', 'player2_team_abbreviation',
        'player3_name', 'player3_team_abbreviation'
    ]
    
    play_by_play = pd.DataFrame(data = sub_events, columns = new_cols)  
            
    t = game.matchup_home.split(' ')

    import os
    cwd = os.getcwd() + '/' + defaults.get('SAVE_GAME_DIR')
    
    fn = f'{t[0]}v{t[2]}{game.game_date.replace('-','')}.csv'
    if save_as_raw : fn = f'RAW-{fn}'
    
    fn = os.path.join(cwd, fn) 
    
    if not(os.path.exists(cwd)): os.mkdir(cwd)   
    
    fl = open(fn,"w")
    f = play_by_play.to_csv()
    fl.write(f)
    fl.close()
                                                                                                            

def event_sort_keys(x):
        
        """            
            0            PRE     STARTOF, SUB, NONSUB
            1 ... 719    Q1      NONSUB, SUB
            720          Q1-Q2   NONSUB, ENDOF, SUB, STARTOF 
            721 .. 1439  Q2      NONSUB, SUB
            1440         Q2-Q3   NONSUB, ENDOF, SUB, STARTOF 
            1441 .. 2159 Q3      NONSUB, SUB
            2160         Q3-Q4   NONSUB, ENDOF, SUB, STARTOF 
            2161 .. 2879 Q4      NONSUB, SUB
            2880         POST    NONSUB, SUB, ENDOF, STARTOF 
        """
        # smaller means first
        sort_order = {
            #                   PRE  1234 POST INPERIOD 
            'STARTOFPERIOD' :[  0,   4,   0,   0    ],
            'SUB'           :[  2,   1,   1,   0    ],
            'NONSUB'        :[  5,   0,   0,   1    ],
            'EJECTION'      :[  1,   2,   2,   5    ],
            'ENDOFPERIOD'   :[  3,   2,   2,   0    ],

        }
        
        event_type = x[0]
        period = int(x[1])
        
        game_second = period_time_to_sec(period,x[2])
        
        period_1 = int(game_second / 720)
        mod_period_sec = game_second % 720
        
        period_x = 3
        
        if mod_period_sec == 0:
            if period_1 == 0       : period_x = 0
            elif period_1 in [1,2,3] : period_x = 1 
            else                   : period_x = 2
                   
        if event_type not in sort_order.keys(): event_type = 'NONSUB'
                    
        so2 = sort_order[event_type][period_x] 
        
        # if exit SUB it goes first                 
        outs_first = event_type == 'SUB' and x[6] == ''
        # print(period_x,x[0:3],(game_second, so2, outs_first))
        return ((game_second, so2, outs_first))
