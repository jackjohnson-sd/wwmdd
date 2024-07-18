from datetime import timedelta
import re

PM = '\xB1'

class box_score:

    _bsItemsA = [
        'PTS','MIN','FG','3PT','FT',
        'REB','BLK','AST','STL',
        'TO','PF', PM,
    ]
    _bsItemsB = ['3miss', '3make', 'make', 'miss', 'FTmiss', 'FTmake', 'secs', 'ORS']
    _bsItems = _bsItemsA + _bsItemsB
    _boxScore = None
    _team_name = None
    _home_team = None
    _start_time = 'UNKNOWN'
    _max_by_items = {}
    
    
    def __init__(self, existing_bs):
        self._boxScore = existing_bs

    def set_team_name(self, team):
        self._team_name = team

    def get_team_secs_played(self): 
        return self.get_item(self._team_name, "secs")
        
    def get_team_minutes_desc(self):
        return f'{self._team_name} {int(self.get_team_secs_played())}'

    def set_home_team_name(self, team):
        self._home_team = team

    def is_flipper(self): return self._team_name != self._home_team
    
    def getBoxScore(self):
        return self._boxScore

    def setBoxScore(self, bs):
        self._boxScore = bs

    def add_player(self, player):

        if player not in self._boxScore.keys():
            self._boxScore[player] = {'OINK':0}
            
        for key in self._bsItems:
            self._boxScore[player][key] = 0
    
    def shooting_percentages(self, player):
        d = self._boxScore[player]
        tFGMakes = d['make'] + d['3make']
        tFGMisses = d['miss'] + d['3miss']
        tFGShots = tFGMisses + tFGMakes
        t3Shots = d['3miss'] + d['3make']
        fgp = (
            '--' if tFGShots == 0
            else str(int(float(tFGMakes) / float(tFGShots) * 100))
        )

        f3p = (
            '--' if t3Shots == 0
            else str(int(float(d['3make']) / float(t3Shots) * 100))
        )

        FTma = d['FTmake']
        FTmi = d['FTmiss']
        if FTma + FTmi == 0: ftp = '--'
        else: ftp  = (
                str(int(
                float(d['FTmake']) / float(d['FTmake'] + d['FTmiss'])* 100))
            )
        return [f3p,fgp, ftp]

    def ts_percentage(self, player):
        # TS% =  PTS/(2 * (FGA /(.044 X FTA)))
        src = ['PTS','make','miss','FTmake','FTmiss']
        b = list(map(lambda x:self._boxScore[player][x] ,src))
        ftA = int(b[3]) + int(b[4])
        fgA = int(b[1]) + int(b[2])
        pts = int(b[0])
        try : ts = int((pts * 100) / (2*(fgA/(0.044 * ftA))))
        except: ts = 'ERR'
        # print(pts,b[1],b[2],b[3],b[4],ftA,fgA,pts,ts)
        return str(ts)
    
    def clean(self):
        for key in self._boxScore:
            d = self._boxScore[key]
            tFGMakes = d['make'] + d['3make']
            tFGMisses = d['miss'] + d['3miss']
            tFGShots = tFGMisses + tFGMakes
            t3Shots = d['3miss'] + d['3make']
            
            d['REB'] = f'{d['ORS']}-{d['REB']}'
            d['FG'] = f'{tFGMakes}-{tFGShots}'
            d['3PT'] = f'{d['3make']}-{t3Shots}'
            d['FT'] = f'{d['FTmake']}-{d['FTmake'] + d['FTmiss']}'

            if key != self._team_name:
                d['MIN'] = str(timedelta(seconds=int(d['secs'])))[2:4]
            else:
                d['MIN'] = str(timedelta(seconds=d['secs'] / 5))[2:4]
                d[PM] = int(d[PM] / 5)

            # d['MIN'] = '99'
            # d[PM] = '30'
            # d['FG'] = '99-99'
            # d['3PT'] = '99-99'
            # d['FT'] = '99-99'
            # d['REB'] = '99-99'

    def dump(self, _players=[]):
        print('                    ', end='')
        for label in self._bsItems:
            print(f'{label:<5} ', end='')
        print()

        players = _players if _players != [] else list(self._boxScore.keys())
        for name in players:
            print(f'{name[:15]:<19} ', end='')
            for item in self._bsItems:
                print(f'{self._boxScore[name][item]:<6}', end='')
            print('')

    def add_player(self, _player):
        if _player not in self._boxScore.keys():
            self._boxScore[_player] = {'OINK' : []}
            for key in self._bsItems:
                self._boxScore[_player][key] = 0

    def add_players(self, _players):
        for p in _players:
            self.add_player(p)

    def get_players(self):
        return list(self._boxScore.keys())

    def get_item(self, _player, _item):
        if _player != None:
            if _player in self.get_players():
                return self._boxScore[_player][_item]
        return None

    def get_items(self, item, players=[]):
        ourPlayers = list(self._boxScore.keys() if players == [] else players)
        ourPlayers.remove(self._team_name)
        return list(map(lambda x: self._boxScore[x][item], ourPlayers))

    def get_names_items(self, item, players=[]):
        ourPlayers = list(self._boxScore.keys() if players == [] else players)
        ourPlayers.remove(self._team_name)
        return list(map(lambda x: [x,self._boxScore[x][item]], ourPlayers))

    def get_item_colwidth(self, item):
        return [item]+ list(map(lambda x: str(self._boxScore[x][item]), list(self._boxScore.keys())))
        
    def get_colwidths(self):
        return list(map(lambda x: self.get_item_colwidth(x),self._bsItemsA))    
        
    def XXupdate(self, _player, _item, val):
        if _player != None:
            if _player in self.get_players():
                self._boxScore[_player][_item] += val

    def update(self,_player,_item,val, when=None):
        if _player != None:
            if _player in self.get_players():
                self._boxScore[_player][_item] += val
                self._boxScore[_player]['OINK'].extend([[_item,val,when]])

    def set_item(self, _player, _item, val):
        if _player != None:
            if _player in self.get_players():
                # if _item in self._bsItems : 
                #     val = 33
                #     self._boxScore[_player][_item] = 0
                    
                self._boxScore[_player][_item] = val

    def sum_item(self, item):
        return sum(self.get_items(item))

    def stuff_bs(self, _evnts, players):
        """player1      player2    player3
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

        prev = None
        for i, _evnt in _evnts.iterrows():

            if type(prev) != type(None):
                if prev.visitordescription == _evnt.visitordescription:
                    if prev.homedescription == _evnt.homedescription:
                        if prev.neutraldescription == _evnt.neutraldescription:
                            # print('duplicat event at ', _evnt.period,_evnt.pctimestring)
                            continue

            p1 = _evnt.player1_name
            p2 = _evnt.player2_name
            p3 = _evnt.player3_name

            p1 = p1 if p1 != '' else None
            p2 = p2 if p2 != '' else None
            p3 = p3 if p3 != '' else None

            prev = _evnt
            event_description = str(_evnt.visitordescription) + str(_evnt.homedescription)
            is3 = '3PT' in event_description
            
            match _evnt.eventmsgtype:

                case 12:
                    if _evnt.period == 1:
                        s = _evnt.neutraldescription
                        self._start_time = s[s.find("(")+1:s.find(")")]
                                    
                case 1:  # make
                    pts = 3 if is3 else 2
                    mk = '3make' if is3 else 'make'
                    self.update(p1, mk, 1,      when=_evnt.sec)
                    self.update(p1, 'PTS', pts, when=_evnt.sec)
                    self.update(p2, 'AST', 1,   when=_evnt.sec)

                case 2:  # miss
                    mk = '3miss' if is3 else 'miss'
                    self.update(p1, mk, 1, when=_evnt.sec)
                    self.update(p3, 'BLK', 1, when=_evnt.sec)

                case 3:  # free throw
                    its_good = 'MISS' not in event_description
                    self.update(p1, 'FTmake' if its_good else 'FTmiss', 1, when=_evnt.sec)
                    if its_good: self.update(p1, 'PTS', 1, when=_evnt.sec)

                case 4:  self.update(p1, 'REB', 1, when=_evnt.sec)

                case 5:  # steal
                    self.update(p1, 'TO', 1, when=_evnt.sec)
                    self.update(p2, 'STL', 1, when=_evnt.sec)

                case 6:  self.update(p1, 'PF', 1, when=_evnt.sec)
  
                # case 8: # substitution

    def add_plus_minus(self, player, start, end):
        self.update(player, PM, end - start)

    def get_bs_data(self, players=[], all=False):

        itemlist = self._bsItemsA if not all else self._bsItems
        rows = players if players != [] else list(self._boxScore.keys())
        columns = itemlist
        data = []
        for key in rows:
            data2 = []
            for key2 in itemlist:
                if key2 == PM:
                    fp = -1 if self._team_name != self._home_team else 1
                    data2 += [str(fp * self._boxScore[key][key2])]
                else:
                    data2 += [str(self._boxScore[key][key2])]
            data += [data2]
        return rows, columns, data

    def summary(self):
        self.add_player(self._team_name)

        for n in self._bsItems:
            v = self.sum_item(n)
            self.set_item(self._team_name, n, v)

        self.clean()
        tmp = self.get_item(self._team_name, 'MIN')
        self.set_item(self._team_name, 'MIN', tmp[0:5])

        ourPlayers = list(self._boxScore.keys())
        ourPlayers.remove(self._team_name)
        
        # get max column values to show our Golden ticket

        def get_golden_ticket(bs_item):
                
            def ech(plr, item):
                value = self._boxScore[plr][item]
                if type(value) == type('aa'):
                    if '-' in value:
                        i = 1 if item == 'REB' else 0
                        value = int(value.split('-')[i])
                return value
            if len(ourPlayers) != 0:
                __tmp = list(map(lambda plr: ech(plr, bs_item), ourPlayers))
                flip_it = (self._home_team != self._team_name) and bs_item == PM
                self._max_by_items[bs_item] = min(__tmp) if flip_it else max(__tmp)
            else : 
                self._max_by_items[bs_item] = 0
                
        self._max_by_items = {}
        list(map(lambda x:get_golden_ticket(x),self._bsItems))     
   
    def is_max(self, item, value,who):
        if item == PM:
            if self._home_team != self._team_name:
                try: value = -int(value)
                except: pass

        if type(value) == type('aa'):
            i = 1 if item == 'REB' else 0
            if '-' in value:
                value = value.split('-')[i]
                
        # if item == 'PTS':print(str(self._max_by_items[item]) == str(value),who,item,value,self._max_by_items[item])
        return str(self._max_by_items[item]) == str(value)
