from datetime import timedelta

boxScore = {}

_bsItemsA = ['MIN','FG','3PT','FT','REB','BLK','AST', 'STL','TO','PF','+/-','PTS']
_bsItemsB =['3miss','3make','make','miss','FTmiss','FTmake','secs']
_bsItems = _bsItemsA + _bsItemsB

def bs_getBoxScore():
    global boxScore
    return boxScore

def bs_setBoxScore(bs):
    global boxScore
    boxScore = bs

def bs_dump(_players = []):
    global boxScore
    print('                    ',end = '')
    for label in _bsItems:
        print(f'{label:<5} ',end='')
    print()    

    players = _players if _players != [] else list(boxScore.keys())
    for name in players:
        print(f'{name[:15]:<19} ', end = '')
        for item in _bsItems:
            print(f'{boxScore[name][item]:<6}',end='')
        print('')    
        
def bs_clean(): 

    global boxScore
    for key in boxScore:
        d = boxScore[key]
        tFGMakes =  d['make'] + d['3make']
        tFGMisses = d['miss'] + d['3miss']
        tFGShots = tFGMisses + tFGMakes

        t3Shots = d['3miss'] + d['3make']
        d['FG'] = f'{tFGShots}-{tFGMakes}'
        d['3PT'] = f'{t3Shots}-{d["3make"]}'
        d['FT']  = f'{d["FTmake"] + d["FTmiss"]}-{d["FTmake"]}'   
        d['MIN'] =  str(timedelta(seconds=d['secs']))[2:] 


    for key in boxScore:
        for item in _bsItemsB:
            del boxScore[key][item]

def bs_add_player( _player):
    global boxScore
    if _player not in boxScore.keys():
        boxScore[_player] = {}
        for key in _bsItems:
            boxScore[_player][key] = 0 

def bs_add_players(_players):
    for p in _players: bs_add_player(p)

def bs_get_players():
    global boxScore 
    return list(boxScore.keys())

def bs_get_items(item, players = []):
    global boxScore
    ourPlayers = boxScore.keys() if players == [] else players 
    return list(map(lambda x:boxScore[x][item], ourPlayers))
    
def bs_update(_player, _item, val):
    global boxScore
    if _player != None:
        if _player in bs_get_players():
            boxScore[_player][_item] += val

def bs_sum_item(item):
    return sum(bs_get_items(item))

def bs_stuff_bs (_evnts, players):
    """                          player1      player2    player3 
        events  1 = make         shooter      assist 
                2 = miss         shooter                 block
                3 = Free throw   shooter      score = NULL if miss else changed score
                4 = rebound
                5 = steal        turn over    stealer
                6 = foul         fouled       fouler
                8 = SUB          OUT          IN
                10  jump ball    jumper1      jumper2    who got the ball
    """
    global boxScore

    boxScore = {}

    bs_add_players(players)

    for i, _evnt in _evnts.iterrows():  
        p1 = _evnt.player1_name
        p2 = _evnt.player2_name
        p3 = _evnt.player3_name

        match _evnt.eventmsgtype:
            
            case 1: # make
                is3 = '3PT' in (str(_evnt.visitordescription) + str(_evnt.homedescription))
                pts = 3 if is3 else 2
                mk = '3make'if is3 else 'make'
                bs_update(p1,mk,1)
                bs_update(p1,'PTS',pts)
                bs_update(p2,'AST',1)

            case 2: # miss
                is3 = '3PT' in (str(_evnt.visitordescription) + str(_evnt.homedescription))
                mk = '3miss'if is3 else 'miss'
                bs_update(p1,mk,1)
                bs_update(p3,'BLK',1)

            case 3: # free throw
                its_good = _evnt.score != None
                bs_update(p1,'FTmake' if its_good else 'FTmiss',1)
                if its_good:
                    bs_update(p1,'PTS',1)

            case 4: #rebound
                bs_update(p1,'REB',1)

            case 5: # steal
                bs_update(p1,'TO',1)
                bs_update(p2,'STL',1)

            case 6: # foul
                bs_update(p1,'PF',1)
                #bs_update(p1,'PFd',1) # got fouled

            #case 8: # substitution    

def bs_add_plus_minus(player, start, end):
    bs_update(player,'+/-', end - start)

def  bs_get_bs_data(players = []):
    global boxScore

    rows = players if players != [] else list(boxScore.keys())
    columns = _bsItemsA
    data = []
    for key in rows:
        data2 = []
        for key2 in _bsItemsA:
            data2 +=  [boxScore[key][key2]]
        data += [data2]
    return rows, columns, data
