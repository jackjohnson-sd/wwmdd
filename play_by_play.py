import pandas as pd
from loguru import logger

from settings import defaults

from utils import pms,period_time_to_sec

from utils import period_from_sec,period_start_sec,time_into_period_from_sec,sec_at_start_of_period
from utils import period_start_sec
from utils import save_file,save_files,fn_root


from box_score import box_score
 
DBG                     = defaults.get('DBG')      


def insert_row(new_row, old_df):

    from pandas import DataFrame, concat

    event_cols = [ 'eventmsgtype','period', 'pctimestring',
        'neutraldescription',
        'score', 'scoremargin',
        'player1_name', 'player1_team_abbreviation',
        'player2_name', 'player2_team_abbreviation',
        'player3_name', 'player3_team_abbreviation'
    ]
   
    new_row = new_row.split(',')
    
    period = new_row[1]
    pctime = new_row[2]
    s = f'period == {period} & pctimestring == "{pctime}"'
    us = old_df.query(s) 
    
    index = us.index.tolist()
    values = us.values.tolist()
    
    insert_point = index[-1]
    new_insert = values[-1]
    
    df_cols = us.columns.tolist()
    
    for j,c in enumerate(df_cols):
        if c in event_cols:
            i = event_cols.index(c)
            new_insert[j] = new_row[i]     
        else:
           if type(new_insert[j]) == type(2): new_insert[j] = 0
           if type(new_insert[j]) == type(2.0): new_insert[j] = 0.0
           if type(new_insert[j]) == type('a'): new_insert[j] = ''
           
                
    new_insert[2] = int(new_insert[2])    
    line = DataFrame([new_insert], columns=df_cols)
    df2 = concat([old_df.iloc[0:insert_point], line, old_df.iloc[insert_point:]]).reset_index(drop=True)
    return df2

def get_players_and_team(game_data, team_abbreviation, play_by_play, get_opponent_data = False):

    # get who's playing and the team they are playing for
    if get_opponent_data:

        p1s = play_by_play[play_by_play["player1_team_abbreviation"] != team_abbreviation]
        p2s = play_by_play[play_by_play["player2_team_abbreviation"] != team_abbreviation]

        # we might be home or away.  we're opponent so we're not team_abbreviation        
        if team_abbreviation != game_data.team_abbreviation_home:
            team_abbreviation = game_data.team_abbreviation_home
        else:
            team_abbreviation = game_data.team_abbreviation_away

    else:
        
        p1s = play_by_play[play_by_play["player1_team_abbreviation"] == team_abbreviation]
        p2s = play_by_play[play_by_play["player2_team_abbreviation"] == team_abbreviation]
    
    p1s = p1s['player1_name']
    p2s = p2s['player2_name']
    
    players_in_game = list(pd.concat([p1s,p2s]).dropna().unique())
    players_in_game = list(pd.concat([p1s,p2s]).dropna().unique())

    # happens in csv read where we have a team rebound with no players
    if '' in players_in_game: players_in_game.remove('')
    
    return team_abbreviation, players_in_game
        
def get_sub_io_events_by_player(box):

    TEST_PLAYERS = defaults.get('TEST_PLAYERS')
    
    def r_(oink):
        oink[2] = f'P{pms(oink[1],delim1=' ')} {oink[2]}' 
        return oink

    _sub_events_by_player = {}
    
    in_the_game = False
    last_event = None
    
    if defaults.get("SOURCE") in ['CSV','GEMINI']:
        
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
 
            length_of_game = 2880 if oinks == [] else oinks[-1][2]

            for oi_,oink in enumerate(oinks):

                dsec = oink[2]

                if len(_sub_events_by_player[player]) > 0:
                
                    last_event = _sub_events_by_player[player][-1] 
                    in_the_game = last_event[0] == 'IN'
                
                else:
                
                    last_event = None
                    in_the_game = False
                
                match oink[0]:
                    
                    case 'SUB.IN':
                        
                        if not in_the_game:
                            
                            _sub_events_by_player[player].append(r_(
                                ['IN',dsec,
                                 'out of game SUB in']))
                            
                        elif dsec > 2880:
                            # we have an in an we are already in
                            # terminate prior at the start of this period
                            # put us in no
                            # logger.error(f'SUB in while in {player} {pms(dsec)}')

                            _sub_events_by_player[player].append(r_(
                                ['OUT',period_start_sec(dsec),
                                'IN while in']))

                            _sub_events_by_player[player].append(r_(
                                ['IN',dsec,
                                'IN while in']))
                                                                    
                    case 'SUB.OUT':
                        
                        if not in_the_game:
                            
                                # we get this when forced out at a period change
                                # and did not have another event until then

                            if last_event == None:
                                                                # got an out, my first event ever! go in at closest period start
                                # and leave now

                                _sub_events_by_player[player].append(r_(
                                    ['IN',  period_start_sec(dsec), 
                                     'Out']))

                                _sub_events_by_player[player].append(r_(
                                    ['OUT', dsec,
                                     'OUT no IN']))
                                

                            else:
                                # came in at period break for first time, did nothing 
                                # and left before next period break

                                # last event was a PCO  
                                if time_into_period_from_sec(int(last_event[1])) == 0:  
                                     
                                    #if PCO from this period 
                                    if period_start_sec(dsec) == period_start_sec(last_event[1]):
                                        # extend PCO until now
                                        last_event[1] = dsec 
                                    else:
                                        # PCO not this SOP, IN at SOP, OUT NOW
                                        _sub_events_by_player[player].append(r_(
                                            ['IN', period_start_sec(dsec), 
                                            'make in, OUT already out, last out not period change']))

                                        _sub_events_by_player[player].append(r_(
                                            ['OUT', dsec,
                                            'OUT with made up IN at period start']))
                                else:
                                    # last out was not PCO, IN at SOP, OUT NOW
                                    _sub_events_by_player[player].append(r_(
                                        ['IN', period_start_sec(dsec), 
                                         'make in, OUT already out, last out not period change']))

                                    _sub_events_by_player[player].append(r_(
                                        ['OUT', dsec,
                                         'OUT with made up IN at period start']))
            
    
                        else:
                            # we are in the game and subbed out during period, everthing OK
                            _sub_events_by_player[player].append(r_(
                                ['OUT', dsec,
                                 'normal in game SUB out']))                         

                    case 'EOQ':
                        
                        # if over time game do not do PCOs
                        # for 4th period outs and beyond
                        # we do the clean up at end of game
                                
                        if last_event != None:    
                                                            
                            if in_the_game:
                                
                                # if dsec == 2880:
                                #     if oinks[oi_ - 1][0] != 'SUB.IN':
                                #         continue
                                
                                _sub_events_by_player[player].append(r_(
                                    ['OUT', period_start_sec(dsec), 
                                    'PCO, period change out']))
                                
                    case _: 

                        if time_into_period_from_sec(dsec) == 0:
                            if oink[0] != 'JB':
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
                        
                                # skip if next oink same time as this    
                                if oinks[oi_ +  1][2] ==  oink[2]: continue  

                                _sub_events_by_player[player].append(r_(
                                    ['IN', period_start_sec(dsec),
                                     'first event non SUB' ]))

                            else:
                                
                                # PCO?  period change out
                                if time_into_period_from_sec(last_event[1]) == 0: 
                                    
                                    # PCO'd this period?
                                    if period_from_sec(last_event[1]) == period_from_sec(dsec):
                                        
                                        # if next oink same time as this, absorb this oink    
                                        if oinks[oi_ +  1][2] !=  oink[2]: 
                                            _sub_events_by_player[player].pop()
                                    else:
                                        
                                        # PCO'd more than one period ago
                                        # if regulation starf at start of current period
                                        # if overtime start at start of overtime
                                        
                                        if period_from_sec(dsec) <= 4:
                                            # logger.critical(f'{pms(dsec)} NOT OT, 2+ PCO') 

                                            _sub_events_by_player[player].append(r_(
                                                ['IN', period_start_sec(dsec),
                                                'not OT, not SUB, not IN']))
                                        else:
                                            
                                            logger.critical(f'{pms(dsec)} 2OT, 2+ PCO') 

                                            enter_at = 2880     
                                            _sub_events_by_player[player].append(r_(
                                                ['IN', enter_at, 
                                                 'OT 2+ PCO not IN' ]))
                                        
                                else:

                                    if period_from_sec(dsec) == period_from_sec(last_event[1]):
                                        # if exited for this period and not PCO'd
                                        continue

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
                                        
                                        # no SUB.IN following
                                        # prior was out same time as us wait till then
                                        if last_event[1] == oink[2]: pass
                                        else:

                                                _sub_events_by_player[player].append(r_(
                                                ['IN', 
                                                period_start_sec(dsec),
                                                'NON SUB - NOT IN']))

            
            if len(_sub_events_by_player[player]) > 0:
                            
                last_event = _sub_events_by_player[player][-1]
                if last_event[0] == 'IN':
                    
                    maybe = sec_at_start_of_period(1 + period_from_sec(last_event[1]))                                
                    _sub_events_by_player[player].append(r_(
                        ['OUT', dsec,
                         'EndOfGame All IN go out']))
                
                    logger.critical(f'dangaling IN at end of game, {player} {pms(last_event[1])}')
                        
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
                        logger.trace(f'{player} consolidating adjacent stints {i+1} ')
            except:
                logger.error(f'{player} stints bad news') 
                           
    for player in game_stints.keys():
        
        stints = game_stints[player]
        p1_ln = player.split(' ')[1]
        
        for stint in stints:    
               
            start_time = pms(stint[1])
            stop_time = pms(stint[2],as_end=True)
            
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
    88: [['PATCH', ''],       [1]   ,],  # 
    18: [['REPLAY', ''],      [1]   ,],  # 
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


        etype_order = 0 
        if event_type == 'STARTOFPERIOD':
            etype_order = 0
            
        elif event_type == 'ENDOFPERIOD': 
            etype_order = 8
    
        elif event_type == 'SUB':
            etype_order = 3
        else:
            etype_order = 5
                      
        so = 2
        if event_type == 'SUB': 
            so = 1 if x[8] == '' else 3
                
     
        return ((period,game_second,etype_order))
     
def pbp_as_csv_file(game, game_stints, save_as_raw = False):
    
    event_keys = list(pbp_event_map.keys())
        
    sub_events = []
    
    for i,p in game.play_by_play.iterrows():
        
        event = p.eventmsgtype 
            
        desc = f'{p.homedescription} {p.neutraldescription} {p.visitordescription}'
        desc = desc.replace('None','').strip()
                        
        try:
            emap  = pbp_event_map[event]
            event_name = emap[0][0]
        except:
            
            if event == 18: emap = [['18']]
            elif event == 88: emap = [['88']]
                
            else:    
                logger.error(f'invalid event type {event}, file save aborted')   
                return     
            
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
        sub_events.extend(sub_events_from_stints(game, game_stints))
        sub_events = sorted(sub_events, key = lambda x:event_sort_keys(x))
    
    # find our sub events that do not have score, margin set
    valid_score_index = 0
    sub_events[0][4:6] = ['0 - 0',0]
    
    for i,sub_event in enumerate(sub_events):

        if sub_event[4] == None or sub_event[4] == '':
            sub_events[i][4:6] = sub_events[valid_score_index][4:6] 
        else:
            valid_score_index = i
                    
   
    new_cols = [ 'eventmsgtype','period', 'pctimestring',
        'neutraldescription',
        'score', 'scoremargin',
        'player1_name', 'player1_team_abbreviation',
        'player2_name', 'player2_team_abbreviation',
        'player3_name', 'player3_team_abbreviation'
    ]
    
    play_by_play = pd.DataFrame(data = sub_events, columns = new_cols)  

    events_by_player = (',').join(new_cols) +'\n'
    
    if save_as_raw:
        
        for player in sorted(list(game_stints.keys())):
            
            s = play_by_play\
            .query(f'eventmsgtype == "STARTOFPERIOD" | eventmsgtype == "ENDOFPERIOD" | player1_name == "{player}" | player2_name == "{player}" | player3_name == "{player}"')\
            .to_csv(header=False) 
            
            events_by_player += '\nPLAYER: ' + player + '\n\n' + s + '\n\n' 

        save_file('PLR_', game, 'SAVE_DIR', events_by_player)
                    
    fpre = 'RAW_' if save_as_raw else ''
    save_file(fpre, game, 'SAVE_DIR', play_by_play.to_csv())

def generatePBP(game_data, team_abbreviation, get_opponent_data=False ):

    TEST_PLAYERS            = defaults.get('TEST_PLAYERS')

    pbp = game_data.play_by_play

    if pbp.shape[0] != 0:
        
        # creates a computed column of seconds into game of event 
        pbp[['sec','score_home','score_away']] = pbp.apply(
            lambda row: make_seconds_home_away_scores(row), axis=1, result_type='expand'
        )
        
        # def get_players_and_team(game_data, team_abbreviation, play_by_play, get_opponent_data = False)
        
        team_abbreviation, players_in_game = get_players_and_team(game_data, team_abbreviation, pbp, get_opponent_data)   
                                         
        # fill box score with events from play by play
        box_ = box_score({})

        box_._team_name = team_abbreviation
        box_.stuff_bs(pbp, players_in_game)
        
        game_data.start_time = box_._start_time 
              
        # get player enter and exit times from box score events
        sub_io_events = get_sub_io_events_by_player(box_)  
        
        stints_by_player = get_stints_from_io_events(sub_io_events,box_)
            
        return [stints_by_player, dict(box_.getBoxScore())]

    return [{},{}],  box_.start_time
