import pandas as pd
from loguru import logger

from settings import defaults

from utils import pms,period_time_to_sec

from utils import period_from_sec,period_start_sec,time_into_period_from_sec,sec_at_start_of_period

from utils import save_file,save_files


from box_score import box_score
 
DBG                     = defaults.get('DBG')      


def get_sub_io_events_by_player(box):

    def r_(oink):
        oink[2] = f'P{pms(oink[1],delim1=' ')} {oink[2]}' 
        return oink

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
                    _sub_events_by_player[player].append(r_([oink[0][4:],oink[2],oink[0]]))
    else:

        for player in box.get_players():
        
            _sub_events_by_player[player] = []        
            
            oinks = box._boxScore[player]['OINK']

            for oi_,oink in enumerate(oinks):

                dsec = oink[2]

                if len(_sub_events_by_player[player]) > 0:
                
                    last_event = _sub_events_by_player[player][-1] 
                    in_the_game = last_event[0] == 'IN'
                
                else:
                
                    last_event = None
                    in_the_game = False
                
                match oink[0]:
                    
                    case  'SUB.IN':
                        
                        if not in_the_game:
                            _sub_events_by_player[player].append(r_(
                                ['IN',oink[2],'SUB in.']))
                            
                        # else:
                            # if last_event != None:
                                
                            #     if oinks[oi_ - 1][2] == oink[2]:
                            #         # prior oink same time as ours 
                            #         if last_event[1] - last_event[1] % _per_length:
                            #             # last sub event happend at period event
                            #             last_event[oi_][1] == oink[2]
                            #             # we exited a period break
                                        
                            # logger.error(f'SUB IN while in {pms(oink[1])}')
                                    
                    case  'SUB.OUT':
                        
                        if not in_the_game:
                            
                                # we get this when forced out at a period change
                                # and did not have another event until then

                            if last_event != None:
                                    # came in at period break for first time, did nothing 
                                    # and left before next period break

                                # at period break? 
                                if time_into_period_from_sec(int(last_event[1])) == 0:  
                                    # extend last in until now 
                                    last_event[1] = dsec 
                                else:

                                    _sub_events_by_player[player].append(r_(
                                        ['IN', period_start_sec(dsec), 
                                         'make in, OUT already out, last out not period change']))

                                    _sub_events_by_player[player].append(r_(
                                        ['OUT', dsec,
                                         'OUT with made up IN at period start']))
            
                            else:
                                # got an out, my first event ever! go in at closest period start
                                # and leave now

                                _sub_events_by_player[player].append(r_(
                                    ['IN',  period_start_sec(dsec), 
                                     'Out']))

                                _sub_events_by_player[player].append(r_(
                                    ['OUT', dsec,
                                     'OUT no IN']))
                                
                        else:
                            # we are in the game and subbed out during period, everthing OK
                            _sub_events_by_player[player].append(r_(
                                ['OUT', dsec,
                                 'normal in game SUB out']))                         

                    case   'EOQ' :
                                
                        if last_event != None:                                    
                            if last_event[0] == 'IN':

                                _sub_events_by_player[player].append(r_(
                                    ['OUT', period_start_sec(dsec), 
                                     'period change out']))
                                    
                    case _: 

                        if time_into_period_from_sec(dsec) == 0:
                                # this happens when an event occuus with < 1 sec on the clock
                                # don't do anything about in or out
                                # print(player,d.sec,d.period,d.pctimestring)
                                continue
                        
                        if oink[0] == 'TF':
                            if not in_the_game:
                                continue                     
                                                
                        if not in_the_game:
                            
                            if last_event == None:
                                
                                # first time this player shows up non sub in/out
                                # could happen if a period change force out and 
                                # player has a event, treat as enter at change
                                # we're lost if already 5 guys in
                        
                                _sub_events_by_player[player].append(r_(
                                    ['IN', period_start_sec(dsec),
                                     'First non SUB in' ]))

                            else:
                                
                                if last_event[0] == 'OUT':

                                    # outed at last period break?
                                    # out was at a period boundary
                                    if time_into_period_from_sec(last_event[1]) == 0: 
                                        # kicked out prior period break, .pop returns us to IN
                                        if period_from_sec(last_event[1]) == period_from_sec(dsec):
                                            
                                            # skip if next oink same time as this    
                                            if oinks[oi_ +  1][2] !=  oink[2]: 
                                                _sub_events_by_player[player].pop()
                                        else:
                                            # kicked out multiple period ago
                                            _sub_events_by_player[player].append(r_(
                                                ['IN', period_start_sec(dsec),
                                                'non SUB first IN' ]))
                                    else:
                                                                                        
                                        nosub = True
                                        anchor_oink = oinks[oi_][2]
                                        
                                        while anchor_oink == oinks[oi_ + 1][2]:
                                        
                                            if oinks[oi_ + 1][0] == 'SUB.IN':

                                                _sub_events_by_player[player].append(r_(
                                                    ['IN', dsec,
                                                     f'NON SUB. SUB follows at {pms(dsec)})']))

                                                nosub = False
                                                break
                                            
                                            elif oinks[oi_ + 1][0] == 'SUB.OUT':
                                                logger.debug(f'{player} trailing out {oinks[oi_ + 1]}')
                                                pass
                                           
                                            oi_ += 1
                                            if oi_ > len(oinks): break
                                            
                                        if nosub:
                                            
                                            # no sub.in following
                                            # prior was out same time as us
                                            if last_event[1] == oink[2]: pass
                                            else:

                                                 _sub_events_by_player[player].append(r_(
                                                    ['IN', 
                                                    period_start_sec(dsec),
                                                    'NON SUB - NOT IN']))
                                                                              
                                else:
                                    # last event was an 'IN' ?
                                    logger.error('ERROR X',player)
                                    pass    


            if len(_sub_events_by_player[player]) > 0:
                            
                last_event = _sub_events_by_player[player][-1]
                if last_event[0] == 'IN':
                    
                    logger.error('Ended without an out!')
                    
                    last_period = period_from_sec(last_event[1])
                    
                    _sub_events_by_player[player].append(r_(
                        ['OUT', 
                         sec_at_start_of_period(last_period + 1),
                         'EndOfGame All IN go out']))
                        
    return _sub_events_by_player
    
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

def sub_events_from_stints(game, game_stints):
    
    # game_stints has duratio,start,stop for all players
    # return sorted list of SUB events 
        
    sub_events = []
    
    for player,stints in game_stints.items():
        stints_count = len(stints)
        if stints_count > 1:
    
            try :    
            
                for i in range(stints_count - 1,0,-1):
                    s1 = stints[i-1]
                    s2 = stints[i]
                    s1_stop = s1[2]
                    s2_start = s2[1]
                    if s1_stop == s2_start:
                        # extend s1 
                        s1[2] = s2[2]  
                        s1[0] += s2[0]        
                        del stints[i]
                        logger.warning(f'{player} consolidating adjacent stints {i+1} ')
            except:
                logger.error(f'{player} stints bad news') 
                           
    for player in game_stints.keys():
        
        stints = game_stints[player]
        p1_ln = player.split(' ')[1]
        
        for stint in stints:    
               
            start_time = pms(stint[1])
            stop_time = pms(stint[2])
            
            s1 = f'SUB,{start_time},SUB: {p1_ln} Starts playing.,,,,,{player},{stint[3]},,'
            s2 = f'SUB,{stop_time},SUB: {p1_ln} Stops playing.,,,{player},{stint[3]},,,,'
  
            sub_events.extend([s1])
            sub_events.extend([s2])
                    
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

def get_stints_from_io_events(sub_io_events, box_):
            
    stints_by_player = {}
    
    for player, io_pairs in sub_io_events.items():
        
        # io_pair =  [IN, when as seconds, comments of whe this happened]
        n_io_items = len(io_pairs)
        
        # this check might/should be done elsewhere. Delete?
        if n_io_items % 2 == 1: 
            logger.error(f'{player} "io_pairs" not paired!')
            break
        
        if n_io_items > 0:

            stints_by_player[player] = []

            _total_secs = 0
            
            for x in range(0,n_io_items,2):
                
                stint_1   = io_pairs[x]
                stint_2   = io_pairs[x + 1]
                
                # type check
                if (stint_1[0], stint_2[0]) != ('IN','OUT'):
                    
                    logger.error(f'stint mis-match {player} {stint_1} {stint_2}')  
                    break
                
                _start = stint_1[1]
                _stop = stint_2[1]
                _duration = _stop - _start
                
                stints_by_player[player].append([int(_duration), int(_start), int(_stop), box_._team_name])                       
                _total_secs += _duration
                    
            box_.update(player,'secs',int(_total_secs)) 

    return stints_by_player

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
        
        so = 2
        if event_type == 'SUB': 
            so = 1 if x[8] == '' else 3
                
     
        return ((game_second))
     
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
                pl = '12:00' if p.period < 5 else '5:00'
                tk = f'{p.period+1}:{pl}'
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
    
    new_cols = [ 'eventmsgtype','period', 'pctimestring',
        'neutraldescription',
        'score', 'scoremargin',
        'player1_name', 'player1_team_abbreviation',
        'player2_name', 'player2_team_abbreviation',
        'player3_name', 'player3_team_abbreviation'
    ]
    
    play_by_play = pd.DataFrame(data = sub_events, columns = new_cols)  
                
    fpre = 'RAW_' if save_as_raw else ''
    save_file(fpre, game, 'SAVE_DIR', play_by_play.to_csv())
                                                                                                                
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
                                
        # fill box score with events from play by play
        box_ = box_score({})
        
        box_._team_name = team_abbreviation
        box_.stuff_bs(pbp, playersInGame)
        
        game_data.start_time = box_._start_time 
              
        # get player enter and exit times from box score events
        sub_io_events = get_sub_io_events_by_player(box_)  
        
        stints_by_player = get_stints_from_io_events(sub_io_events,box_)
            
        return [stints_by_player, dict(box_.getBoxScore())]

    return [{},{}],  box_.start_time

