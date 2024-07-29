import pandas as pd
from loguru import logger

from settings import defaults

from utils import pms, sec_to_period_time, period_time_to_sec
from utils import save_file,save_files

from box_score import box_score
 
DBG                     = defaults.get('DBG')      



def getInsNOutsByPlayer(box):
    
    start_time =  box._start_time
    _sub_events_by_player = {}
    
    in_the_game = False
    last_event = None
    
    if defaults.get("SOURCE") == 'CSV':
        
        for player in box.get_players():
            _sub_events_by_player[player] = []        
            oinks = box._boxScore[player]['OINK']
            for i,oink in enumerate(oinks):
                if oink[0] in ['SUB.IN','SUB.OUT']:
                    _sub_events_by_player[player].append([oink[0][4:],oink[2],oink[0]] )
    else:

        for player in box.get_players():
        
            _sub_events_by_player[player] = []        
            
            in_the_game = False
            last_event = None
            
            oinks = box._boxScore[player]['OINK']

            for oi_,oink in enumerate(oinks):

                dsec = oink[2]
                
                try:
                    period = int(dsec/720) + 1
                except:
                    logger.error(f'period error {oink}')
                    
                if len(_sub_events_by_player[player]) > 0:
                    last_event = _sub_events_by_player[player][-1] 
                    in_the_game = last_event[0] == 'IN'
                else:
                    last_event = None
                    in_the_game = False
                
                match oink[0]:
                    
                    case  'SUB.IN':
                        if not in_the_game:
                            _sub_events_by_player[player].append(['IN',oink[2],'SUB in.'])
                            in_the_game = True
                                    
                    case  'SUB.OUT':
                        
                        if not in_the_game:
                            
                                # we get this when forced out at a period change
                                # and did not have another event until then

                            if last_event != None:
                                    # came in at period break for first time, did nothing 
                                    # and left before next period break

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
                            """        
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
                            """
                        else:
                            # we are in the game and subbed out during period, everthing OK
                            _sub_events_by_player[player].append(['OUT', dsec,'SUB out'])                         

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

                            # lastEvent = None if len(_sub_events_by_player[player]) == 0 else _sub_events_by_player[player][-1]
                            
                            if last_event == None:
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

                                if last_event[0] == 'OUT':

                                    # ouuted at last period break?
                                    if last_event[1] == dsec - dsec % 720: 
                                        # kicked out prior period break, .pop returns us to IN
                                        _sub_events_by_player[player].pop()
                                        in_the_game = True
                                    else:
                                        # out not from last period break
                                        if last_event[1] % 720 == 0:
                                            logger.warning(f'last event from 2 period ago {player} {oink}')
                                            
                                            # out not from any prior period break
                                            # say IN now
                                            # _sub_event_for_player.append(['IN', d.sec,'NON SUB while NOT in game']) 
                                        # else:            
                                            # out from more than one prior period ago
                                            # Non SUB event not in game,
                                            # set to in at start of cur
                                            
                                        # sub after rebound BOS 0403

                                        nosub = True
                                        anchor_oink = oinks[oi_][2]
                                        while anchor_oink == oinks[oi_ + 1][2]:
                                            if oinks[oi_ + 1][0] == 'SUB.IN':
                                                _sub_events_by_player[player].append(['IN', dsec,f'NON SUB. SUB follows at {pms(dsec)})']) 
                                                nosub = False
                                                break
                                            elif oinks[oi_ + 1][0] == 'SUB.OUT':
                                                logger.warning(f'{player} trailing out {oinks[oi_ + 1]}')
                                                pass
                                            oi_ += 1
                                            if oi_ > len(oinks): break
                                            

                                        if nosub:
                                            
                                            _sub_events_by_player[player].append(['IN', dsec - dsec % 720,f'NON SUB - NOT IN at {pms(dsec)})']) 
                                                
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
    
        score = [0,0] if row.score == '0' else row.score.split('-')
    
        home_score = int(score[0])
        away_score = int(score[1])
    
    return _secs, home_score, away_score
    
def stint_sort_key(stnt): return stnt[1] if stnt[4] == 'I' else stnt[2]

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
                    # print('cleaner killed',player,s1,s2)
                    kills.extend([i+1])
                else:
                    logger.error(f'{player} stop/start mis-match.  {i}  {s1}')
                    logger.error(f'{player}                        {i+1}  {s2}')
                
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
            'SUB'           :[  2,   1,   1,   1    ],
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

        return ((game_second, so, outs_first))
     
def dump_pbp(game, game_stints, save_as_raw = False):
    
    period_end_score = {}    
    event_keys = list(pbp_event_map.keys())
 
    sub_events = [] if save_as_raw else sub_events_from_stints(game, game_stints)
    
    lastScore = '0 - 0'
    lastScoreMargin = 0
    
    for i,p in game.play_by_play.iterrows():
        
        event = p.eventmsgtype 
        if event in event_keys:
            
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
    save_file(fpre, game, 'SAVE_DIR', f)
                                                                                                                
def generatePBP(game_data, team_abbreviation, get_opponent_data=False ):

    TEST_PLAYERS            = defaults.get('TEST_PLAYERS')

    pbp = game_data.play_by_play

    if  pbp.shape[0] != 0:
        
        # creates a computed column of seconds into game of event 
        pbp[['sec','score_home','score_away']] = pbp.apply(
            lambda row: make_seconds_home_away_scores(row), axis=1, result_type='expand'
        )

        # get who's playing and the team they are playing for
        if get_opponent_data:

            p1s = pbp.query(f'player1_team_abbreviation != "{team_abbreviation}"')['player1_name'] 
            p2s = pbp.query(f'player2_team_abbreviation != "{team_abbreviation}"')['player2_name']
            
            if team_abbreviation != game_data.team_abbreviation_home:
                team_abbreviation = game_data.team_abbreviation_home
            else:
                team_abbreviation = game_data.team_abbreviation_away

        else:
            p1s = pbp.query(f'player1_team_abbreviation == "{team_abbreviation}"')['player1_name'] 
            p2s = pbp.query(f'player2_team_abbreviation == "{team_abbreviation}"')['player2_name']
        
        playersInGame = list(set(p1s.dropna()) | set(p2s.dropna()))

        # happens in csv read where we have a team rebound with no players
        if '' in playersInGame: playersInGame.remove('')
        
        # if get_opponent_data :
        #     if team_abbreviation != game_data.team_abbreviation_home:
        #         team_abbreviation = game_data.team_abbreviation_home
        #     else:
        #         team_abbreviation = game_data.team_abbreviation_away
                        
        # stuff box score with events from play by play
        boxSc = box_score({})
        boxSc.stuff_bs(pbp, playersInGame)
        
        # get player enter and exit times from box score
        InsNOuts, start_time = getInsNOutsByPlayer(boxSc)  
        
        game_data.start_time = start_time 
         
        """
        InsNOutsOLD, start_timeOLD = getInsNOutsByPlayer22(pbp,playersInGame)  # collect timespans played by this player

        for i,pname in enumerate(InsNOuts.keys()):

            try:
                new = InsNOuts[pname]
                old = InsNOutsOLD[pname]
            except:
                continue
            
            if len(old) != len(new):
                print(pname,f'old {len(old)}, new {len(new)} xxxxxxxx=====')
                    
                for k,new_in in enumerate(new):
                    try :
                        if old[k][0:2] != new_in[0:2]:
                            print(pname,k)
                            print(f'new              old')
                            for kk,nnew_in in enumerate(new):
                                print(f'{nnew_in[0]:5} {pms(nnew_in[1]):5}     {old[kk][0]:5} {pms(old[kk][1]):5} ')
                        
                            break
                    except: pass
        if DBG:
            logger.warning('using old/DBG InsNOuts') 
            InsNOuts = InsNOutsOLD

        # if player == 'Jaylin Williams':
        #     for oink in oinks:
        #         print(f'{oink[0]:<7} {oink[2]:<10} {pms(oink[2])}')

        """
        
    # updates boxscore 'secs' for game for player
        # by summing duration of all stints for player
        
        # also turning In/Out to start,stop,duration (a stint)  
        # for each player
             
        stints_by_player = {}
        
        for player,_sub_events in InsNOuts.items():
            
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
                        
                        stints_by_player[player].append([int(_duration), int(_start), int(_stop), team_abbreviation])
                    else:
                        logger.error(f'stint mis-match {player}{start_ts}{stop_ts}')  
                
                boxSc.update(player,'secs',int(_total_secs)) 
            
        return [stints_by_player, dict(boxSc.getBoxScore())]

    return [{},{}], start_time

