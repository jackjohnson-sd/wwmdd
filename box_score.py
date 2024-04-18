from datetime import timedelta

class box_score:

    _bsItemsA = ['MIN','FG','3PT','FT','REB','BLK','AST', 'STL','TO','PF','+/-','PTS']
    _bsItemsB =['3miss','3make','make','miss','FTmiss','FTmake','secs']
    _bsItems = _bsItemsA + _bsItemsB
    
    _boxScore = None

    def __init__(self, existing_bs):
        self._boxScore = existing_bs
    
    def xx__init__(self):
        self._boxScore = {}

    def getBoxScore(self):
        return self._boxScore

    def setBoxScore(self, bs):
        self._boxScore = bs

    def add_player(self, player): 

        if player not in self._boxScore.keys():
            self._boxScore[player] = {}
        for key in self._bsItems:
            self._boxScore[player][key] = 0 
    
    def clean(self):
        for key in self._boxScore:
            d = self._boxScore[key]
            tFGMakes =  d['make'] + d['3make']
            tFGMisses = d['miss'] + d['3miss']
            tFGShots = tFGMisses + tFGMakes

            t3Shots = d['3miss'] + d['3make']
            d['FG'] = f'{tFGShots}-{tFGMakes}'
            d['3PT'] = f'{t3Shots}-{d["3make"]}'
            d['FT']  = f'{d["FTmake"] + d["FTmiss"]}-{d["FTmake"]}'   
            d['MIN'] =  str(timedelta(seconds=d['secs']))[2:] 

            #for key in self._boxScore:
            #    for item in self._bsItemsB:
            #        del self._boxScore[key][item]

    def dump(self,_players = []):
        print('                    ',end = '')
        for label in self._bsItems:
            print(f'{label:<5} ',end='')
        print()    

        players = _players if _players != [] else list(self._boxScore.keys())
        for name in players:
            print(f'{name[:15]:<19} ', end = '')
            for item in self._bsItems:
                print(f'{self._boxScore[name][item]:<6}',end='')
            print('')   

    def add_player(self, _player):
        if _player not in self._boxScore.keys():
            self._boxScore[_player] = {}
            for key in self._bsItems:
                self._boxScore[_player][key] = 0 
    
    def add_players(self, _players):
        for p in _players: 
            self.add_player(p)
                
    def get_players(self):
        return list(self._boxScore.keys())

    def get_items(self, item, players = []):
        ourPlayers = self._boxScore.keys() if players == [] else players 
        return list(map(lambda x:self._boxScore[x][item], ourPlayers))
        
    def update(self,_player, _item, val):
        if _player != None:
            if _player in self.get_players():
                self._boxScore[_player][_item] += val

    def sum_item(self, item):
        return sum(self.get_items(item))

    def stuff_bs (self, _evnts, players):
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

        self.add_players(players)

        for i, _evnt in _evnts.iterrows():  
            p1 = _evnt.player1_name
            p2 = _evnt.player2_name
            p3 = _evnt.player3_name

            match _evnt.eventmsgtype:
                
                case 1: # make
                    is3 = '3PT' in (str(_evnt.visitordescription) + str(_evnt.homedescription))
                    pts = 3 if is3 else 2
                    mk = '3make'if is3 else 'make'
                    self.update(p1,mk,1)
                    self.update(p1,'PTS',pts)
                    self.update(p2,'AST',1)

                case 2: # miss
                    is3 = '3PT' in (str(_evnt.visitordescription) + str(_evnt.homedescription))
                    mk = '3miss'if is3 else 'miss'
                    self.update(p1,mk,1)
                    self.update(p3,'BLK',1)

                case 3: # free throw
                    its_good = _evnt.score != None
                    self.update(p1,'FTmake' if its_good else 'FTmiss',1)
                    if its_good:
                        self.update(p1,'PTS',1)

                case 4: #rebound
                    self.update(p1,'REB',1)

                case 5: # steal
                    self.update(p1,'TO',1)
                    self.update(p2,'STL',1)

                case 6: # foul
                    self.update(p1,'PF',1)
                    #bs_update(p1,'PFd',1) # got fouled

                #case 8: # substitution    

    def add_plus_minus(self, player, start, end):
        self.update(player,'+/-', end - start)

    def get_bs_data(self, players = []):

        rows = players if players != [] else list(self, self._boxScore.keys())
        columns = self._bsItemsA
        data = []
        for key in rows:
            data2 = []
            for key2 in self._bsItemsA:
                data2 +=  [self._boxScore[key][key2]]
            data += [data2]
        return rows, columns, data
