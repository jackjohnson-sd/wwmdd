import itertools
from utils import ms, sec_to_period_time,sec_to_period_time2,intersection

from settings import defaults
TEST_PLAYERS  = defaults.get('TEST_PLAYERS')  
OVELAP_GROUP  = defaults.get('OVERLAP_GROUP')  


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
    
    players = list(game_stints_by_player.keys())
    game_stints_by_combo = {}
    
    for i in OVELAP_GROUP:
        
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
            stints = get_overlap_stints(combo[0],combo[1],game_stints_by_player)
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

def overlap_dump(game_stints_by_combo, team_abbreviation):
        
        def fgg(stints):
            return sum(list(map(lambda x:x[0],stints)))
            
        ol_pt = list(map(lambda x:[x,fgg(game_stints_by_combo[x]),game_stints_by_combo[x]],game_stints_by_combo.keys())) 
        ol_pts = sorted(ol_pt, key=lambda x: x[1])   


        print(f'{team_abbreviation} OVERLAP')
        ol_pts.reverse()
        for x in ol_pts[0:25]:
            
                
            st = (', ').join(list(map(lambda x:stint_dump(x),x[2])))
            nP = f'({1 + x[0].count('_')})' 
            dur = f'{ms(x[1])}' 
            combo = f'{x[0]}'
            
            # print(f'{nP} {dur} {combo} {st} ')
            print(f'{nP} {dur} {combo}\n          {st}')
    

def stint_dump(stint):
    start_time = f'{sec_to_period_time2(stint[1]).replace(' ',':')}'
    end_time = f'{sec_to_period_time2(stint[2]).replace(' ',':')}'
    duration = f'{ms(int(stint[0]))}'
    s = f'[{duration} {start_time},{end_time}]'
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
