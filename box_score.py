from datetime import timedelta
import re

from loguru import logger
from utils import pms
from utils import save_file

PM = '\xB1'

class box_score:

    _shown_items = [
        'PTS','MIN','FG','3PT','FT',
        'REB','BLK','AST','STL',
        'TO','PF', PM,
    ]
    
    _not_shown_items = [
        '3P.MI', '3P.MA', 
        'FG.MI', 'FG.MA', 
        'FT.MI', 'FT.MA',
        'SUB.IN', 'SUB.OUT', 'EOQ',
        'secs', 'ORS','TF', 'JB', 'VO','EJ','FD'
    ]
    
    _bsItems = _shown_items + _not_shown_items
    
    _boxScore = None
    _team_name = None

    _home_team = None
    _start_time = 'UNKNOWN'

    _max_by_items = {}
        
    _Off_reb_cnt = {}
    
    def __init__(self, existing_bs):
        self._boxScore = existing_bs

    def set_team_name(self, team):
        self._team_name = team

    def is_home_team(self): self._team_name == self._home_team
    
    def stint_columns(self):
        
        L2a = self._shown_items 
        if PM in L2a: L2a.remove(PM)
        L2b = self._not_shown_items
        
        L1 = 'PLAYER,TEAM,PERIOD.START,CLOCK.START,PERIOD.STOP,CLOCK.STOP,PLAY.TIME,'
        L2 = ['OFF','DEF',PM] + L2a + L2b 
        
        for n in ['MIN','3PT','FG','FT','SUB.IN','SUB.OUT','ORS']:  L2.remove(n)
        
        return L1 + (',').join(L2), L2

    def get_team_secs_played(self): 
        return self.get_item(self._team_name, 'secs')
        
    def get_team_minutes_desc(self):
        return f'{self._team_name} {int(self.get_team_secs_played())}'

    def set_home_team_name(self, team): self._home_team = team

    def is_flipper(self): return self._team_name != self._home_team
    
    def getBoxScore(self): return self._boxScore

    def setBoxScore(self, bs): self._boxScore = bs

    def add_player(self, player):

        if player not in self._boxScore.keys():
            self._boxScore[player] = {'OINK':0}
            
        for key in self._bsItems:
            self._boxScore[player][key] = 0
    
    def shooting_percentages(self, player):
        d = self._boxScore[player]
        tFGMakes = d['FG.MA'] + d['3P.MA']
        tFGMisses = d['FG.MI'] + d['3P.MI']
        tFGShots = tFGMisses + tFGMakes
        t3Shots = d['3P.MI'] + d['3P.MA']
        fgp = (
            '--' if tFGShots == 0
            else str(int(float(tFGMakes) / float(tFGShots) * 100))
        )

        f3p = (
            '--' if t3Shots == 0
            else str(int(float(d['3P.MA']) / float(t3Shots) * 100))
        )

        FTma = d['FT.MA']
        FTmi = d['FT.MI']
        if FTma + FTmi == 0: ftp = '--'
        else: ftp  = (
                str(int(
                float(d['FT.MA']) / float(d['FT.MA'] + d['FT.MI'])* 100))
            )
        return [f3p,fgp, ftp]

    def ts_percentage(self, player):
        # TS% =  PTS/(2 * (FGA /(.044 X FTA)))
        src = ['PTS','FG.MA','FG.MI','FT.MA','FT.MI']
        b = list(map(lambda x:self._boxScore[player][x] ,src))
        ftA = int(b[3]) + int(b[4])
        fgA = int(b[1]) + int(b[2])
        pts = int(b[0])
        try : ts = int((pts * 100) / (2*(fgA/(0.044 * ftA))))
        except: ts = 'ERR'
        return str(ts)
    
    def clean(self):
        for key in self._boxScore:
            
            d = self._boxScore[key]

            tFGMakes = d['FG.MA'] + d['3P.MA']
            tFGMisses = d['FG.MI'] + d['3P.MI']
            tFGShots = tFGMisses + tFGMakes
            
            t3Shots = d['3P.MI'] + d['3P.MA']
            
            d['REB'] = f'{d['ORS']}-{d['REB']}'
            d['FG'] = f'{tFGMakes}-{tFGShots}'
            d['3PT'] = f'{d['3P.MA']}-{t3Shots}'
            d['FT'] = f'{d['FT.MA']}-{d['FT.MA'] + d['FT.MI']}'

            if key != self._team_name:
                d['MIN'] = str(timedelta(seconds=int(d['secs'])))[2:]
            else:
                d['MIN'] = str(timedelta(seconds=d['secs'] / 5))[2:]
                d[PM] = int(d[PM] / 5)

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

    def get_players(self): return list(self._boxScore.keys())

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
        return list(map(lambda x: self.get_item_colwidth(x),self._shown_items))    
        
    def update(self,_player,_item,val, when=None):
        if _player != None:
            if _player in self.get_players():
                try : 
                    when = int(when)
                except:
                    when = 0
                    
                self._boxScore[_player][_item] += val
                self._boxScore[_player]['OINK'].extend([[_item,val,int(when)]])

    def set_item(self, _player, _item, val):
        if _player != None:
            if _player in self.get_players():
                self._boxScore[_player][_item] = val

    def sum_item(self, item): return sum(self.get_items(item))

    def EOP_update(self,when):
        for p in self.get_players():
            self.update(p,'EOQ',1,when)
 
    def stuff_bs(self, _evnts, players):
        
        self.add_players(players)

        prev_event = None
                
        for i, _evnt in _evnts.iterrows():

            if type(_evnt) != type(None):
                if _evnt.equals(prev_event):
                    logger.warning(f'boxscore event loading found a duplicate line {i}, {_evnt.period} {_evnt.pctimestring}')
                        
            prev_event = _evnt
             
            p1 = _evnt.player1_name
            p2 = _evnt.player2_name
            p3 = _evnt.player3_name

            p1 = p1 if p1 != '' else None
            p2 = p2 if p2 != '' else None
            p3 = p3 if p3 != '' else None
            
            event_description = str(_evnt.visitordescription) + str(_evnt.homedescription)
            
            is3 = '3PT' in event_description
            
            match _evnt.eventmsgtype:

                case '88':
                    self.update(p2, 'JB', 1, when=_evnt.sec)
                    
                case 13: # END of period 
                    self.EOP_update(_evnt.sec)
                
                case 12: # START of period
                    if _evnt.period == 1:
                        s = _evnt.neutraldescription
                        self._start_time = s[s.find("(")+1:s.find(")")]
                
                case 10: # JUMP BALL
                    self.update(p1, 'JB', i, when=_evnt.sec)
                    self.update(p2, 'JB', 1, when=_evnt.sec)
                    self.update(p3, 'JB', 1, when=_evnt.sec)
    
                case 1:  # FG.MA
                    pts = 3 if is3 else 2
                    mk = '3P.MA' if is3 else 'FG.MA'
                    self.update(p1, mk, 1,      when=_evnt.sec)
                    self.update(p1, 'PTS', pts, when=_evnt.sec)
                    self.update(p2, 'AST', 1,   when=_evnt.sec)

                case 2:  # FG.MI
                    mk = '3P.MI' if is3 else 'FG.MI'
                    self.update(p1, mk, 1, when=_evnt.sec)
                    self.update(p3, 'BLK', 1, when=_evnt.sec)

                case 3:  # free throw
                    its_good = 'MISS' not in event_description
                    self.update(p1, 'FT.MA' if its_good else 'FT.MI', 1, when=_evnt.sec)
                    if its_good: self.update(p1, 'PTS', 1, when=_evnt.sec)

                case 8:  # SUB
                    self.update(p1, 'SUB.OUT', 1, when=_evnt.sec)
                    self.update(p2, 'SUB.IN', 1, when=_evnt.sec)
                    
                case 4: # REB
                    self.update(p1, 'REB', 1, when=_evnt.sec)
                    
                    if 'Off' in event_description:
                        
                        try: 
                            # search description for offensive rebound count change
                            # copy past from stackoverflow, i know nothing
                            or_count = re.search('Off:(.*) Def:', event_description).group(1)
                            
                            if int(or_count) != 0:
                                
                                if p1 not in self._Off_reb_cnt.keys():
                                    self._Off_reb_cnt[p1] = 0

                                # if there been a change
                                if or_count != self._Off_reb_cnt[p1]:
                                    self.update(p1, 'ORS', 1, when=_evnt.sec)

                                self._Off_reb_cnt[p1] = or_count
                                    
                        except:
                            # team rebounds have no player 
                            or_count = 0
                            # logger.error(f'Off Rebound description {event_description}')
                             
                case 5:  # steal/turnover
                    self.update(p1, 'TO', 1, when=_evnt.sec)
                    self.update(p2, 'STL', 1, when=_evnt.sec)

                case 6:  # foul
                
                    if p1 == None or p2 == None: 
                        # logger.debug(f'Only one player specifed foul {event_description}')
                        continue
                    
                    ttm = ''
                    try: 
                        ttm += str(_evnt.neutraldescription) 
                        ttm += str(_evnt.homedescription) 
                        ttm += str(_evnt.visitordescription) 
                    except : pass
                    
                    tech_foul = False
                    for a in ["TECHNICAL","T.FOUL","Technical","TECHNICAL"]:
                        if a in ttm:
                            tech_foul = True
                            break
                        
                    if tech_foul:
                               
                        self.update(p1, 'TF', 1, when=_evnt.sec)
                        self.update(p2, 'TF', 1, when=_evnt.sec)

                    else:    
                        self.update(p1, 'PF', 1, when=_evnt.sec)
                        self.update(p2, 'FD', 1, when=_evnt.sec)

                    # if foul_type == 'TF': print('T.FOUL',pms(_evnt.sec))
                
    def add_plus_minus(self, player, start, end):
        self.update(player, PM, end - start)

    def get_bs_data(self, players=[], all=False):

        itemlist = self._shown_items if not all else self._bsItems
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

def save_box_score(box1,box2,game_data):
    
    rows, columns, data = box1.get_bs_data(all=True)

    s = f'date,player,team,{','.join(columns)}\n'  
    lines = [s]         
    
    # don't include team name in sort
    sorted_rows = sorted(rows[0:-1]) + [rows[-1]]
    for player in sorted_rows:
        i = rows.index(player)
        d = data[i]
        a = f'{game_data.game_date},{rows[i]},{box1._team_name},{','.join(d)}\n'
        lines.extend(a)

    rows, columns, data = box2.get_bs_data(all=True)
    sorted_rows = sorted(rows[0:-1]) + [rows[-1]]
    for player in sorted_rows:
        i = rows.index(player)
        d = data[i]
        a = f'{game_data.game_date},{rows[i]},{box2._team_name},{','.join(d)}\n'
        lines.extend(a)
        
    save_file('BOX_',game_data,'SAVE_DIR',lines)
