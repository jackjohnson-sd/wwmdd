import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.path import Path
from matplotlib.textpath import TextToPath
from matplotlib.font_manager import FontProperties

from settings import defaults

# DBG_A       = defaults.get('dbga')
# DBG_B       = defaults.get('dbgb')
# DBG_C       = defaults.get('dbgc')

STINT_C     = defaults.get('STINT_COLOR')       
BAD_EVNT    = defaults.get('BAD_EVENT_COLOR')    
GOOD_EVNT   = defaults.get('GOOD_EVENT_COLOR') 

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
1: [ GOOD_EVNT, 30.0, mrk['2'],'FG',    GOOD_EVNT, 30.0, mrk['A'],'AST',  [1, 2], em_fg, 0.8,0.8],  # make, assist
2: [  BAD_EVNT, 30.0, mrk['2'],'MISS',  GOOD_EVNT, 30.0, mrk['B'],'BLK',  [1, 3], em_mi, 0.8,0.8],  # miss, block
3: [ GOOD_EVNT, 30.0, mrk['1'],'FT',    None, None, ',','',               [1],    em_ft, 0.8,0.8],  # free throw
4: [ GOOD_EVNT, 30.0, mrk['D'],'DREB',  None, None, ',','',               [1],    or_dr, 0.8,0.8],  # rebound
5: [ GOOD_EVNT, 30.0, mrk['S'],'STL',   BAD_EVNT,  30.0, mrk['T'],'TO',   [2, 1], None,  0.8,0.8],  # steal, turnover
6: [ BAD_EVNT,  30.0, mrk['F'],'PF',    None, None, 's','PF\'d',          [1, 2], None,  0.8,0.8],  # foul, fouled
8: [ STINT_C,   15.0, 'o','SUB',        STINT_C,  15.0, 'o','OUT',        [1, 2], None,  1.0,1.0],  # substitution
20:[ GOOD_EVNT, 30.0, mrk['O'],'OREB',  GOOD_EVNT, 30.0, mrk['3'],'3PT',  [1],    None,  0.8,0.8],  # for legend
}

def event_legend():

    event_legend_map = [        # the order in which we show up in legend
        [20,1,1.5], [ 1,0,1.5], [3,0,1.5],    # 3PT  FG  FT 
        [ 2,0,1.5], [ 5,1,1.5], [6,0,1.5],    # MISS, TO, PF
        [ 1,1,1.5], [ 2,1,1.5], [5,0,1.5],    # ast ,blk,STL
        [ 4,0,1.5], [20,0,1.5], [8,0,2.0]     # dreb,oreb
    ]

    legend_elements = []
    
    for x in event_legend_map:
        e      = event_map[x[0]]
        offset = x[1] * 4
        if type(e[2 + offset]) == type([]):
            marker_ = '$'+e[2 + offset][0] +'$'
        else: 
            marker_ = e[2 + offset]
        l = Line2D([0], [0], 
                lw                = 0, 
                marker            = marker_, 
                color             = e[    offset], 
                label             = e[3 + offset], 
                markerfacecolor   = e[    offset],  
                markersize        = e[1 + offset]/8 * x[2])
    
        legend_elements.extend([l])

    legend_elements.extend([Line2D([0], [0], lw=1, color=STINT_C, label=' STINT' )])
    return legend_elements
            
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
                    _si *= action[10]
                    if i == 0:
                        _color1 = _co
                        _size1  = _si * action[10]
                        _style1 = _st
                    else:   
                        _color2 = _co
                        _size2  = _si * action[11]
                        _style2 = _st

    # return c/si/st for both possible players
    return _color1, _size1, _style1, _color2, _size2, _style2,
