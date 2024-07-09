import re
import numpy as np

from matplotlib.path import Path
from matplotlib.textpath import TextToPath
from matplotlib.font_manager import FontProperties

import settings

color_defaults = settings.default(settings.defaults.get('COLOR_DEFAULTS'))

STINT_CO_IN     = color_defaults.get('STINT_COLOR_IN')   
STINT_CO_OUT    = color_defaults.get('STINT_COLOR_OUT')   
STINT_CO        = color_defaults.get('STINT_COLOR')   

BAD_EVNT        = color_defaults.get('BAD_EVENT_COLOR')    
GOOD_EVNT       = color_defaults.get('GOOD_EVENT_COLOR') 

MRK_FONTSCALE   = color_defaults.get('MARKER_FONTSCALE')
MRK_FONTWEIGHT  = color_defaults.get('MARKER_FONTWEIGHT')
BOX_COL_COLOR   = color_defaults.get('BOX_COL_COLOR')

TABLE_C         = color_defaults.get('TABLE_COLOR')

STINT_COLOR_PLUS  = color_defaults.get('STINT_COLOR_PLUS')
STINT_COLOR_MINUS = color_defaults.get('STINT_COLOR_MINUS')
 
fp = FontProperties(family='sans-serif',size='xx-small')
fp.set_weight('light')

def get_marker(symbol):
    v, codes = TextToPath().get_text_path(fp, symbol)
    v = np.array(v)
    mean = np.mean([np.max(v,axis=0), np.min(v, axis=0)], axis=0)
    return Path(v-mean, codes, closed=False)

mrk = {
    # 'A': get_marker('A'),
    'A': ['A'],
    'D': ['D'],
    'O': ['O'],
    '1': ['1'],
    '2': ['2'],
    '3': ['3'],
    'F': ['F'],
    'B': ['B'],
    'S': ['S'],
    'T': ['T'],
}

# print(matplotlib.get_data_path())

def is3(eventRecord):
    vis = eventRecord.homedescription
    hom = eventRecord.visitordescription
    return (str(vis) + str(hom)).find('3PT') != -1

def em_mi(_style, _color, _size, eventRecord, current_oreb_count, scoreMargins):
    # helper to make 3PT makes a bigger shape on plots
    if _style == mrk['2'] and is3(eventRecord):
        _style = mrk['3']
    return _style, _color, _size    

def em_fg(_style, _color, _size, eventRecord, current_oreb_count, scoreMargins):
    # helper to make 3PT makes a bigger shape on plots
    if _style == mrk['2'] and is3(eventRecord):
        _style = mrk['3']
    return _style, _color, _size    

def em_ft(_style, _color, _size, eventRecord, current_oreb_count, scoreMargins):
    # differentiate made vs missed free throw by color
    if type(eventRecord.score) != type('a'): 
        _color= BAD_EVNT
    return _style, _color, _size

def em_st(_style, _color, _size, eventRecord, current_oreb_count, scoreMargins):
    return _style, _color, _size
        
def or_dr(_style, _color, _size, eventRecord, current_oreb_count, scoreMargins):
    
    try:
        s = str(eventRecord.visitordescription) 
        s2 = str(eventRecord.homedescription)
        if s != s2: s += s2
        or_count = re.search('Off:(.*) Def:', s).group(1)
        is_or = False
        _player1 = eventRecord.player1_name
        if _player1 not in current_oreb_count.keys():
            current_oreb_count[_player1]  = 0 

        is_or = current_oreb_count[_player1] != or_count
        current_oreb_count[_player1] = or_count
        if is_or: _style = mrk['O']
    except Exception as err:
        print(err)

    return _style, _color, _size

event_map = {
1: [ GOOD_EVNT, 18.0, mrk['2'],'FG',    GOOD_EVNT, 18.0, mrk['A'],'AST',  [1, 2], em_fg,],  # make, assist
2: [  BAD_EVNT, 18.0, mrk['2'],'MISS',  GOOD_EVNT, 18.0, mrk['B'],'BLK',  [1, 3], em_mi,],  # miss, block
3: [ GOOD_EVNT, 18.0, mrk['1'],'FT',    None, None, ',','',               [1],    em_ft,],  # free throw
4: [ GOOD_EVNT, 18.0, mrk['D'],'DREB',  None, None, ',','',               [1],    or_dr,],  # rebound
5: [ GOOD_EVNT, 18.0, mrk['S'],'STL',   BAD_EVNT,  18.0, mrk['T'],'TO',   [2, 1], None, ],  # steal, turnover
6: [ BAD_EVNT,  18.0, mrk['F'],'PF',    None, None, 's','PF\'d',          [1, 2], None, ],  # foul, fouled
8: [ STINT_CO_IN,8.0,     'o','IN',     STINT_CO_OUT, 8.0,   'o','OUT',   [1, 2], None, ],  # substitution
20:[ GOOD_EVNT, 18.0, mrk['O'],'OREB',  GOOD_EVNT, 18.0, mrk['3'],'3PT',  [1],    None, ],  # for legend
}

def event_to_size_color_shape(player, eventRecord, current_oreb_count, scoreMargins):

    # call with player or list of players
    players = [player] if type(player) != type([]) else player
    player_names = [eventRecord.player1_name, eventRecord.player2_name, eventRecord.player3_name]

    # return None's when this is not us
    _size1 = 0
    _color1 = None
    _style1 = ','

    _size2 = 0
    _color2 = None
    _style2 = ','

    if eventRecord.eventmsgtype in event_map.keys():
        # this is an event we want to report on
        action = event_map[eventRecord.eventmsgtype]

        # 1 or 2 players can be attached to this event
        for i, xx in enumerate(action[8]):
            index = i * 4  # for the moment color and size per event, 
            if player_names[xx - 1] in players:
                # its for us color and size for event
                _co = action[index]
                _si = action[index + 1]
                _st = action[index + 2]
                if _co != None:
                    # if we need help figuring this out call helper
                    if action[9] != None: 
                        _st,_co, _si = action[9](_st, _co, _si, eventRecord, current_oreb_count,scoreMargins)
            
                    # first person return in xxx1 all others xxx2
                
                    if i == 0:
                        _color1 = _co
                        _size1  = _si
                        _style1 = _st
                    else:   
                        _color2 = _co
                        _size2  = _si
                        _style2 = _st

    # return c/si/st for both possible players
    return _color1, _size1, _style1, _color2, _size2, _style2,
