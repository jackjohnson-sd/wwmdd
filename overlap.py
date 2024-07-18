import itertools
from utils import ms, sec_to_period_time,sec_to_period_time2,intersection

from settings import defaults
from loguru import logger

TEST_PLAYERS  = defaults.get('TEST_PLAYERS')  

def get_oinks(player,stint,box):
    
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
    
            """
                sresult = ov(n1,n2)
                for n3 on
                  sresult = overlap(sresult,n3)
            """
            stints = get_overlap_stints(combo[0],combo[1],game_stints_by_player[0])
            pt = sum(list(map(lambda x:x[0],stints)))
            if len(stints) != 0 and pt > 30:
                game_stints_by_combo[combo_name] = stints
                
                for c_name in combo[2:]:
                
                    stints = _overlap_stints(stints,game_stints_by_player[c_name])    
                    pt = sum(list(map(lambda x:x[0],stints)))
                    if len(stints) <= 0 or pt < 30: 
    
                        del game_stints_by_combo[combo_name]
                        stints = []
                        break 
                    game_stints_by_combo[combo_name] = stints
                
    return game_stints_by_combo

def overlap_dump(game_stints_by_combo, game_data, box):

    team = box._team_name   

    L2a = box._bsItemsA 
    L2b = box._bsItemsB
    L2 = L2a + L2b
    for n in ['MIN','3PT','FG','FT','secs']: 
        L2.remove(n)
       
    def fgg(stints):
        return sum(list(map(lambda x:x[0],stints)))
        
    ol_pt = list(map(lambda x:[x,fgg(game_stints_by_combo[x]),game_stints_by_combo[x]],game_stints_by_combo.keys())) 
    ol_pts = sorted(ol_pt, key=lambda x: x[1])   

    ol_pts.reverse()
    ols = ['player_group,player_group_team,start,end,duration,' + (',').join(L2) + '\n'] 
    for x in ol_pts[0:25]:
        for stint in x[2]:
            s = f'{x[0]},{team},{stint_dump(stint)}'
            
            players = x[0].split('_') 
            oinkss = []
            oink_sum = {}
            for player in players:
                oinks = get_oinks(player,stint,box)
                oinkss.extend([oinks])
                
            for oink in oinkss:
                for onk in oink.keys():
                    if onk not in oink_sum.keys(): 
                         oink_sum[onk] = 0
                    oink_sum[onk] += oink[onk]

            oinks_str = ''
            for o in L2:
                v = oink_sum[o] if o in oink_sum.keys() else 0
                oinks_str += ',' + str(v)
            s += oinks_str
            s += '\n'

            ols.extend([s])
    
    t = game_data.matchup_home.split(' ')

    import os
    cwd = os.getcwd() + '/' + defaults.get('SAVE_GAME_DIR')
    fn = f'OVERLAPS_{team}_{t[0]}v{t[2]}{game_data.game_date.replace('-','')}.csv'
    fn = os.path.join(cwd, fn) 
    if not(os.path.exists(cwd)): os.mkdir(cwd)   
    
    logger.info(f'Saving {os.path.basename(fn)}')
    
    fl_s = open(fn,"w")
    fl_s.writelines(ols)
    fl_s.close()
    
def stint_dump(stint):
    start_time = f'{sec_to_period_time2(stint[1]).replace(' ',':')}'
    end_time = f'{sec_to_period_time2(stint[2]).replace(' ',':')}'
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
