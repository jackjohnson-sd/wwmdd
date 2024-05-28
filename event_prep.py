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

MRK_FONTSCALE  = defaults.get('MARKER_FONTSCALE')
MRK_FONTWEIGHT = defaults.get('MARKER_FONTWEIGHT')
BOX_COL_COLOR  = defaults.get('BOX_COL_COLOR')

TABLE_C     = defaults.get('TABLE_COLOR')

STINT_COLOR_PLUS  = defaults.get('STINT_COLOR_PLUS')
STINT_COLOR_MINUS = defaults.get('STINT_COLOR_MINUS')
 
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
8: [ STINT_C,   8.0, 'o','SUB',         STINT_C,  8.0, 'o','OUT',        [1, 2], None,  ],  # substitution
20:[ GOOD_EVNT, 18.0, mrk['O'],'OREB',  GOOD_EVNT, 18.0, mrk['3'],'3PT',  [1],    None, ],  # for legend
}

def event_legend(ax,xstart,ystart):
    
    ax.set_xlim(0, 100)
    ax.set_ylim(100, 0)
     
    ax.tick_params(axis='both', which='major', labelsize=0, pad=0,   length = 0)
 
    ax.yaxis.set_visible(False)
    ax.xaxis.set_visible(False)
    
    for s in ['top', 'right', 'bottom', 'left']:
        ax.spines[s].set_visible(False)
    
    xoff = 9
    x1 = xstart
    x2 = x1 + xoff 
    x3 = x2 + xoff
    x4 = x3 + xoff
    x5 = x4 + xoff
    x6 = x5 + xoff
    x7 = x6 + xoff
    x8 = x7 + xoff
    x9 = x8 + xoff
    x10 = x9 + xoff

    
    yoff = 20
    y1 = ystart
    y2 = y1 + yoff 
    y3 = y2 + yoff 

    
    event_legend_map = [    
        [20, 1, x1, y1],  # 3PT 
        [ 1, 0, x1, y2],  # FG
        [ 3, 0, x1, y3],  # FT
    
        [ 2, 0, x2, y1],  # MISS 
        [ 5, 1, x2, y2],  # TO
        [ 6, 0, x2, y3],  # PF
        
        [ 1, 1, x3, y1], # AST
        [ 5, 0, x3, y2],  # STL
        [ 2, 1, x3, y3],  # BLK
    
        [ 4, 0, x4, y1],  # OREB
        [20, 0, x4, y2], # DREB
        [ 8, 0, x4, y3]    # SUB
    ]
    
    for k in event_legend_map:
        e = event_map[k[0]]
        offset = k[1] * 4
        label = e[3 + offset]
        x = k[2]
        y = k[3]
        if type(e[2 + offset]) == type([]):
            marker_ = e[2 + offset][0]
            ax.text(x-2,y, s = marker_, color=e[offset], 
                size= 20 / MRK_FONTSCALE, 
                va = 'center', 
                ha = 'left',
                # fontweight = MRK_FONTWEIGHT
                )
            
        else: 
            marker_ = e[2 + offset]
            ax.scatter(x-1.5,y-2, marker = marker_, color=e[0], s= 26 / MRK_FONTSCALE)

        ax.text(x,y, s = label, 
            color=BOX_COL_COLOR, 
            size= 22 / MRK_FONTSCALE, 
            va = 'center', 
            ha = 'left',
            # fontweight = MRK_FONTWEIGHT
            )
        
    l1x = x5 - 3
    l2x = l1x + 1
    l3x = l2x + 1
    l4x = l3x + 1
    
    l1 = Line2D([l1x,l2x], [y3,y3], lw=1, color=STINT_COLOR_MINUS , label='' )
    l2 = Line2D([l2x,l3x], [y3,y3], lw=1, color=STINT_C, label='' )
    l3 = Line2D([l3x,l4x], [y3,y3], lw=1, color=STINT_COLOR_PLUS , label='' )
    ax.add_line(l1)
    ax.add_line(l2)
    ax.add_line(l3)

    ax.text(l4x + 1,y3, s = 'STINT', 
        color=BOX_COL_COLOR, 
        size= 22 / MRK_FONTSCALE, 
        va = 'center', 
        ha = 'left',
        # fontweight = MRK_FONTWEIGHT
        )

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
