import itertools
from loguru import logger

from settings import defaults
from utils import ms, sec_to_period_time, save_file,period_time_to_sec
# sec_to_period_time2,intersection,save_file

from box_score import PM

TEST_PLAYERS  = defaults.get('TEST_PLAYERS')  

def get_oinks(player,stint,box,home_scores, away_scores):

    start = stint[1]
    stop  = stint[2]

    oinks = box._boxScore[player]['OINK']
    # print(start,stop,oinks)
    def fo(start,stop,oink):
        if oink[2] != None:
            if oink[2] >= start:
                if oink[2] <= stop:
                    return oink
        return None

    our_oinks = list(map(lambda x:fo(start,stop,x),oinks))
    while None in our_oinks: our_oinks.remove(None)

    oinks_sum = {}
    for oink in our_oinks:
        if oink[0] not in oinks_sum.keys():
            oinks_sum[oink[0]] = 0
        oinks_sum[oink[0]] += int(oink[1])

    try:
        if stop >= len(home_scores) : stop = -1
        deltah = home_scores[stop] - home_scores[start]
        deltaa = away_scores[stop] - away_scores[start]

    except:
        logger.error(f'OFF/DEF issues {stop} {start} {len(home_scores)}')
        deltaa = 0
        deltah = 0

    tnk = [deltah,deltaa] 
    if box._team_name != box._home_team: tnk.reverse()

    oinks_sum['OFF'] = tnk[0]
    oinks_sum['DEF'] = tnk[1]

    # oinks_sum[PM] = tnk[0] - tnk[1]

    pm = tnk[0] - tnk[1]
    secs = stint[0]
    oinks_sum[PM] = int(pm * 12 * 60 / secs)

    return oinks_sum   

def overlap(stintA, stintB):
    
    A_start = stintA[1]
    A_end   = stintA[2]    
    B_start = stintB[1]
    B_end   = stintB[2]
    
    overlap_start = [
        A_start,
        A_start,
        A_start,
        B_start,
        B_start,
        B_start,
        A_start,
        A_start,
        A_start,]
    
    overlap_length = [
    A_end - A_start,
    A_end - A_start,
    B_end - A_start,
    A_end - B_start,
    A_end - B_start,
    B_end - B_start,
    A_end - A_start,
    A_end - A_start,
    B_end - A_start,]
    
    index = 0
    
    if   A_start < B_start:  index = 3
    elif A_start > B_start:  index = 6

    if   A_end < B_end:   index += 1
    elif A_end > B_end:   index += 2
    
    OVLP_start = overlap_start[index]
    OVLP_end   = overlap_length[index]
    
    return OVLP_start, OVLP_end

def overlap_combos(game_stints_by_player):
    
    players = list(game_stints_by_player[0].keys())
    game_stints_by_combo = {}
    
    for i in defaults.get('OVERLAP_GROUP'):
        
        for combo in itertools.combinations(players, i):
            # print(i,combo)
            # continue
            combo_name = '_'.join(combo)
            
            game_stints_by_combo[combo_name] = []
    
            stints = get_overlap_stints(combo[0],combo[1],game_stints_by_player[0])
            pt = sum(list(map(lambda x:x[0],stints)))
            
            if len(stints) != 0 and pt > 30:
                
                game_stints_by_combo[combo_name] = stints
                
                for c_name in combo[2:]:
                
                    stints = _overlap_stints(stints,game_stints_by_player[0][c_name])    
                    pt = sum(list(map(lambda x:x[0],stints)))
    
                    if len(stints) <= 0 or pt < 30: 
    
                        del game_stints_by_combo[combo_name]
                        stints = []
                        break 
                    
                    game_stints_by_combo[combo_name] = stints
                
    return game_stints_by_combo

def overlap_dump(game_stints_by_combo, game_data, box, home_scores, away_scores):
    
    team_name = box._team_name   
    L1, L2 = box.stint_columns()

    def fgg(stints):
        return sum(list(map(lambda x:x[0],stints)))
        
    ol_pt = list(map( lambda x:
                    [x,fgg(game_stints_by_combo[x]),game_stints_by_combo[x]],
                    game_stints_by_combo.keys()))
     
    ol_pts = sorted(ol_pt, key=lambda x: x[1])   
    ol_pts.reverse()
    
    ols = [L1.replace('PLAYER','PLAYER1,PLAYER2,PLAYER3,PLAYER4,PLAYER5') + '\n']   
   
    n = min(25,len(ol_pts))
    
    # sorted(ol_pts[0:n],)
    for x in ol_pts[0:n]:
            
        plrs = x[0].split('_')
        while len(plrs) < 5: plrs.extend(['']) 
        plrs = (',').join(plrs)
        
        for stint in x[2]:
            
            s = f'{plrs},{team_name},{stint_dump(stint)}'
            
            players = x[0].split('_') 
            oinkss = []
            for player in players:
                oinks = get_oinks(player,stint,box,home_scores,away_scores)
                oinkss.extend([oinks])
                
            oink_sum = {}
            for oink in oinkss:
                for onk in oink.keys():
                    if onk not in oink_sum.keys(): 
                         oink_sum[onk] = 0
                    if onk in [PM,'OFF','DEF']:
                        oink_sum[onk] = oink[onk]
                    else:
                        oink_sum[onk] += oink[onk]

            oinks_str = ''
            for o in L2:
                v = oink_sum[o] if o in oink_sum.keys() else 0
                oinks_str += ',' + str(v)
            s += oinks_str
            s += '\n'

            ols.extend([s])
            
    fn_pre = f'OVERLAPS_{team_name}_'
    
    kk = ols[0].split(',').index(PM)

    m = 1 if box.is_home_team() else -1
         
    def jj(s,kk,m): return int(s.split(',')[kk]) * m
    
    zz = sorted(ols[1:], key=lambda x: jj(x,kk,m))
    save_file(fn_pre, game_data, 'SAVE_GAME_DIR', [ols[0]] + zz)

def stint_dump(stint):
    start_time = f'{sec_to_period_time(stint[1]).replace(' ',',')}'
    end_time = f'{sec_to_period_time(stint[2]).replace(' ',',')}'
    duration = f'{ms(int(stint[0]))}'
    s = f'{start_time},{end_time},{duration}'
    s.strip()
    return s

def overlap_stints_show(header, stintsA, trailer):
    
    def ms(sec):
        m = int(sec / 60)
        s = int(sec % 60)
        return f'{m:02d}:{s:02d}'

    secs = sum(list(map(lambda x:x[0],stintsA)))
    print(header)
    print('\n'.join(list(map(lambda x:f'{stint_dump(x)}',stintsA))), ms(secs))

def get_overlap_stints(pa_name,pb_name, game_stints_by_player):

    pa_stints = game_stints_by_player[pa_name]
    pb_stints = game_stints_by_player[pb_name]
    return _overlap_stints(pa_stints, pb_stints)

def _overlap_stints(pa_stints, pb_stints):

    ovelap_stints_by_player = []
    for stintsa in pa_stints:
        for stintsb in pb_stints:
            if stintsa[3] == stintsb[3]:
                os,ol = overlap(stintsa,stintsb) 
                if ol > 0:
                    ovelap_stints_by_player.extend([[ol, os, os+ol,stintsa[3]]])
    return ovelap_stints_by_player


def stints_as_csv(bx1, bx2, stints1, stints2, game_data, home_scores, away_scores):
    
    def xxx(stints,bx,labels):
    
        def ms(sec):
            m = int(sec / 60)
            s = int(sec % 60)
            return f'{m:02d}:{s:02d}'
        
        def get_oinks(player,stint,box):
            
            start = stint[1]
            stop  = stint[2]
            
            oinks = box._boxScore[player]['OINK']
        
            def fo(start,stop,oink):
                if oink[2] != None:
                    if oink[2] >= start:
                        if oink[2] <= stop:
                            return oink
                return None
        
            our_oinks = list(map(lambda x:fo(start,stop,x),oinks))
        
            while None in our_oinks: our_oinks.remove(None)
            
            oinks_sum = {}
            for oink in our_oinks:
                if oink[0] not in oinks_sum.keys():
                    oinks_sum[oink[0]] = 0
                oinks_sum[oink[0]] += int(oink[1])
                    
            try:
                if stop >= len(home_scores) : 
                    stop = -1
                
                #if box._home_team  == box._team_name:
                deltah = home_scores[stop] - home_scores[start]
                deltaa = away_scores[stop] - away_scores[start]

            except:
                logger.error(f'OFF/DEF issues {stop} {start} {len(home_scores)}')

            tnk = [deltah,deltaa] 
            if box._team_name != box._home_team:
                tnk.reverse()
                
            oinks_sum['OFF'] = tnk[0]
            oinks_sum['DEF'] = tnk[1]
            oinks_sum[PM] = tnk[0] - tnk[1]
            
            secs = stint[0]
            oinks_sum[PM] = int(oinks_sum[PM] * 12 * 60 /secs)
  
            return oinks_sum   
        
        def stint_dump(stints,player,box):
            s = ''
            if player in stints[0]:
                    
                stintw = stints[0][player]
                s = ''
                for stint in stintw:
                    
                    oinks = get_oinks(player,stint,box)
                    oinks_str = ''
                    for o in labels:
                        v = oinks[o] if o in oinks.keys() else 0
                        oinks_str += ',' + str(v)
                        
                    tmp = f'{player},{bx._team_name},{sec_to_period_time(stint[1]).replace(' ',',')},{sec_to_period_time(stint[2]).replace(' ',',')},{ms(int(stint[0]))}'
                    
                    s += tmp + oinks_str + '\n'
            else:
                logger.error(f'stints to csv error. {player} has no stints.')
            
            return s.strip()

        tmp = list(map(lambda x:f'{stint_dump(stints,x[0],bx)}',bx.get_names_items('secs')))
        
        return '\n'.join(tmp)
        # list(map(lambda x:f'{stint_dump(stints,x[0],bx)}',bx.get_names_items('secs'))))

    L1, L2 = bx1.stint_columns()
    
    # plus/minus is positive for home negative for away team
    m = 1 if bx1.is_home_team() else -1
    pm_index = L1.split(',').index(PM)
    
    def jj(s,pm_index,m):    
        try: return int(s.split(',')[pm_index]) * m
        except: return 0 
    
    a = xxx(stints1,bx1,L2)
    aa = sorted(a.split('\n'), key=lambda x: jj(x,pm_index,m))
 
    b = xxx(stints2,bx2,L2)
    bb = sorted(b.split('\n'), key=lambda x: jj(x,pm_index,m))

    data = L1 + '\n' + '\n'.join(aa) + '\n\n\n' + '\n'.join(bb)
    
    save_file('STINTS_', game_data, 'SAVE_GAME_DIR', data)
    
    return True
