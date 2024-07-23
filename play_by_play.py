import pandas as pd
from loguru import logger

from settings import defaults

from utils import pms,sec_to_period_time,period_time_to_sec,save_file
from utils import save_files

from box_score import box_score
 
TEST_PLAYERS            = defaults.get('TEST_PLAYERS')

DBG = defaults.get('DBG')      

def getInsNOutsByPlayer(box):
    
    start_time =  box._start_time
    _sub_events_by_player = {}
    
    in_the_game = False
    last_event = None
    
    for player in box.get_players():
        
        _sub_events_by_player[player] = []        
        in_the_game = False
        last_event = None
        oinks = box._boxScore[player]['OINK']

        for i,oink in enumerate(oinks):

            dsec = oink[2]
            
            try:
                period = int(dsec/720) + 1
            except:
                logger.error(f'period error {oink}')

                
            if len(_sub_events_by_player[player]) > 0:
                last_event = _sub_events_by_player[player][-1] 
                in_the_game = last_event[0] == 'IN'
            
            match oink[0]:
                
                case  'SUB.IN':
                    if not in_the_game:
                        _sub_events_by_player[player].append(['IN',oink[2],'SUB in.'])
                        in_the_game = True
                                
                case  'SUB.OUT':
                    
                    if not in_the_game:
                        if last_event != None:
                            if last_event[1] % 720 == 0:  
                                # at period break, extend our till now 
                                last_event[1] = dsec 
                            else:
                                _sub_events_by_player[player].append(['IN',  dsec - dsec % 720, 'Out'])
                                _sub_events_by_player[player].append(['OUT', dsec,'OUT no IN'])
                                in_the_game = False

                        else:
                            _sub_events_by_player[player].append(['IN',  dsec - dsec % 720, 'Out'])
                            _sub_events_by_player[player].append(['OUT', dsec,'OUT no IN'])
                            in_the_game = False
                            
                      
                    else:
                        if last_event == None:
                               pmss = sec_to_period_time(oink[2])
                               _sub_events_by_player[player].append(['IN', (int(pmss[0]) - 1) * 720, 'Enter in'])
                               _sub_events_by_player[player].append(['OUT', dsec,'Leave via SUB'])
                               in_the_game = False
                        else:
                            is_out = last_event[0] == 'OUT'  
                            is_period_change_time = last_event[1] == (period-1) * 720
                            
                            if is_out and is_period_change_time :
                                # set last out to now, so it extends over the period break
                                last_event[1] = dsec
                                last_event[2] = f'extend after period change, {sec_to_period_time(dsec)}'
                            else:    
                                if is_out:
                                    pmss = sec_to_period_time(dsec)
                                    _sub_events_by_player[player].append(['IN', (int(pmss[0]) - 1) * 720, 'Enter in'])
                                    
                                _sub_events_by_player[player].append(['OUT', dsec,'Leave via SUB'])
                                in_the_game = False
                                        
                                    # pass # for now
                                    # if player in TEST_PLAYERS:
                                    #     print(f'{player} {d.sec} Exit when NOT IN the game.')

                case   'EOQ' :
                             
                    for plyer in _sub_events_by_player:
                        
                        events = _sub_events_by_player[plyer]
                        if len(events) > 0:
                            
                            last_event = _sub_events_by_player[plyer][-1] 
                            
                            if last_event[0] == 'IN':
                                events.append(['OUT',dsec - (dsec % 720), 'P change'])
                                
                case _: 

                    if dsec % 720 == 0:
                            # this happens when an event occuus with < 1 sec on the clock
                            # don't do anything about in or out
                            # print(player,d.sec,d.period,d.pctimestring)
                            continue
                    
                    if oink[0] == 'TF':
                        if not in_the_game:
                            continue                     
                                            
                    if not in_the_game:

                        lastEvent = None if len(_sub_events_by_player[player]) == 0 else _sub_events_by_player[player][-1]
                        
                        if lastEvent == None:
                            # first time this player shows up non sub in/out
                            # could happen if a period change force out and 
                            # player has a event, treat as enter at change
                            # we're lost if already 5 guys in
                    
                            _sub_events_by_player[player].append(['IN', (period-1) * 720,'First non SUB in' ])
                            in_the_game = True
                                                            
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
                                    _sub_events_by_player[player].pop()
                                    in_the_game = True
                                else:
                                    # out not from last period break
                                    # if last_event[1] % 720 != 0:
                                        # out not from any prior period break
                                        # say IN now
                                        # _sub_event_for_player.append(['IN', d.sec,'NON SUB while NOT in game']) 
                                    # else:            
                                        # out from more than one prior period ago
                                        # Non SUB event not in game,
                                        # set to in at start of cur
                                        _sub_events_by_player[player].append(['IN', (period-1) * 720,f'NON SUB - NOT IN at {dsec}']) 
                                        in_the_game = True                                    
                            else:
                                # last event was an 'IN' ?
                                logger.error('ERROR X',player)
                                pass    

    
    for player in  _sub_events_by_player.keys():
        
        events = _sub_events_by_player[player]
        if len(events) > 0:
            last_event = events[-1] 
            if last_event[0] == 'IN':

                pmss = sec_to_period_time(last_event[1])
                _sub_events_by_player[player].append(['OUT', ((int(pmss[0])) * 720),'EndOfGame All IN go out']) 
                        
    return _sub_events_by_player, start_time
    
def make_seconds_home_away_scores(row):
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

    dbg = defaults
    pbp = game_data.play_by_play

    if  pbp.shape[0] != 0:
        
        # creates a computed column of seconds into game of event 
        pbp[['sec','score_home','score_away']] = pbp.apply(
            lambda row: make_seconds_home_away_scores(row), axis=1, result_type='expand'
        )

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
        
        InsNOuts, start_time = getInsNOutsByPlayer(boxSc)  # collect timespans played by this player
                
        if OPPONENT :
            if team_abbreviation != game_data.team_abbreviation_home:
                team_abbreviation = game_data.team_abbreviation_home
            else:
                team_abbreviation = game_data.team_abbreviation_away
                
        stints_by_player = {}

        for player in InsNOuts.keys():
            
            _sub_events = InsNOuts[player]

            if len(_sub_events) > 0:

                stints_by_player[player] = []

                lenTss = len(_sub_events)
                _total_secs = 0
                
                for x,y in zip(range(0,lenTss,2),range(1,lenTss,2)):
                    start_ts  = _sub_events[x]
                    stop_ts   = _sub_events[y]
                    
                    if start_ts[0] == 'IN' and stop_ts[0] == 'OUT':
                        _duration = stop_ts[1] - start_ts[1]
                        _total_secs += _duration
                        _start = start_ts[1]
                        _stop = stop_ts[1]
                        
                        stints_by_player[player].append([int(_duration) , int(_start), int(_stop), team_abbreviation])
                    else:
                        logger.error('Error forming spans ',player,start_ts,stop_ts)  
                
                boxSc.update(player,'secs',_total_secs) 

        game_data.start_time = start_time  
            
        return [stints_by_player, dict(boxSc.getBoxScore())]

    return [{},{}], start_time

def save_box_score(box,box2,game_data):
    
    rows, columns, data = box.get_bs_data()

    s = f'date,player,team,{','.join(columns)}\n'  
    lines = [s]         
    
    for i,d in enumerate(data):
        a = f'{game_data.game_date},{rows[i]},{box._team_name},{','.join(d)}\n'
        lines.extend(a)

    rows, columns, data = box2.get_bs_data()
    for i,d in enumerate(data):
        a = f'{str(game_data.game_date)},{rows[i]},{box2._team_name},{','.join(d)}\n'
        lines.extend(a)
        
    save_file('BOX_',game_data,'SAVE_GAME_DIR',lines)
    
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
        
            p1_ln = player_name.split(' ')[1]
            if this_in_out[4] == 'I':
                x1 = sec_to_period_time(this_in_out[1]).replace(' ',',')
                s1 = f'SUB,{x1},SUB: {p1_ln} Starts playing.,,,,,{player_name},{team_name},,'
            else:
                # x2 = sec_to_period_time(this_in_out[2]).replace(' ',',')
                x2 = pms(this_in_out[2])
                # home of the 5,12:00 problem
                s1 = f'SUB,{x2},SUB: {p1_ln} Stops playing.,,,{player_name},{team_name},,,,'
  
            sub_events.extend([s1])
            
    return  sub_events
    
def sub_events_from_stints(game, game_stints):
    
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

    if defaults.get('SAVE_SUBS_FILE'):
        f = ',eventmsgtype,period,pctimestring,neutraldescription,score,scoremargin,player1_name,player1_team_abbreviation,player2_name,player2_team_abbreviation,player3_name,player3_team_abbreviation\n,' + \
            ('\n,').join(sub_events)  

        ma = game.matchup_away.split(' @ ')
        gd = game.game_date.split('-')
        fn = f'SUBS_{ma[0]}a{ma[1]}{gd[0]}{gd[1]}{gd[2]}.csv'

        save_files(fn,'_save_and_ignore',[[fn,f]])

    return list(map(lambda x:x.split(','),sub_events))

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
     
def dump_pbp(game, game_stints, do_raw = False):
    
    period_end_score = {}    
    
    save_as_raw = do_raw
    
    sub_events = [] if save_as_raw else sub_events_from_stints(game, game_stints)
    
    keys = list(pbp_event_map.keys())
    
    lastScore = '0 - 0'
    lastScoreMargin = 0
    
    for i,p in game.play_by_play.iterrows():
        
        event = p.eventmsgtype 
        if event in keys:
            
            desc = f'{p.homedescription} {p.neutraldescription} {p.visitordescription}'
            desc = desc.replace('None','').strip()
            
            if p.score == None:
                p.score = lastScore
                p.scoremargin = lastScoreMargin
            else:
                lastScore = p.score
                lastScoreMargin = p.scoremargin
                
            emap  = pbp_event_map[event]
            event_name = emap[0][0]
                        
            # point.assist
            if event == 1:              
                if p.player2_name != None: event_name = '.'.join(emap[0])
                s = '3' if '3PT' in desc else '2'
                event_name = s + event_name
            
            # miss.block        
            elif event == 2:
                if p.player3_name != None: event_name = '.'.join(emap[0])
                e = '3POINT' if '3PT' in desc else '2POINT'
                event_name = e + event_name

            # free throw        
            elif event == 3: event_name = 'FTMISS' if 'MISS' in desc else 'FTMAKE'

            # steal.turnover    
            elif event == 5: 
                if p.player2_name != None: event_name = '.'.join(emap[0])
                
            elif event == 13:
                tk = f'{p.period+1}:12:00'
                period_end_score[tk] = [p.score, p.scoremargin]

            match = event != 8 or save_as_raw
            
            if match:
                a = [
                    event_name,
                    p.period, p.pctimestring,
                    desc,
                    p.score, p.scoremargin,
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
            sub_events[i][4] = '0 - 0' if j == 0 else sub_events[j][4]
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
            
    f = play_by_play.to_csv()
    
    fpre = 'RAW_' if save_as_raw else ''
    save_file(fpre, game, 'SAVE_GAME_DIR', f)
                                                                                                                
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
            'SUB'           :[  2,   1,   1,   2    ],
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
                    
        so = sort_order[event_type][period_x] 
        
        if event_type == 'SUB':
            sub_enter = x[8] != ''
            if period_x == 3:
                if sub_enter: 
                    so = 0
                else:
                    # exit during game play
                    pass
                
        outs_first = event_type == 'SUB' and x[6] != ''
        # print(period_x,x[0:3],(game_second, so2, outs_first))
        return ((game_second, so, outs_first))

        for oink in boxSc._boxScore['Josh Giddey']['OINK']: print(oink)
"""

['IN', 0, 'First non SUB in']
['OUT', 449.0, 'SUB out']
['IN', 720, 'NON SUB - NOT IN at 800.0']
['OUT', 997.0, 'SUB out']
['IN', 1391.0, 'SUB in.']
['OUT', 1823.0, 'SUB out']
['IN', 2276.0, 'SUB in.']
['OUT', 2880, 'P change']


NEW
['IN', 0, 'First non SUB in']
['OUT', 2160, 'P change']
['IN', 2276.0, 'SUB in.']
['OUT', 2880, 'P change']


Oinks


['FG.MA', 1, 84.0]
['PTS', 2, 84.0]

['PTS', 2, 438.0]
['SUB.OUT', 1, 449.0]

['EOQ', 1, 720.0]

['REB', 1, 800.0]
['FG.MI', 1, 997.0]
['SUB.OUT', 1, 997.0]

['SUB.IN', 1, 1391.0]
['EOQ', 1, 1440.0]
['ORS', 1, 1504.0]
['REB', 1, 1819.0]
['SUB.OUT', 1, 1823.0]

['EOQ', 1, 2160.0]

['SUB.IN', 1, 2276.0]
['FG.MA', 1, 2323.0]
['PTS', 2, 2867.0]
['EOQ', 1, 2880.0]

"""
