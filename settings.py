import json 

defaults = None

class default :
    
    stuff = {}

    def __init__(self,fn='wwmdd.json'):
        
        if fn == None: fn = 'wwmdd.json'
        try:    
            with open(fn, "r") as f:
                self.stuff = json.load(f)
        except:
                print(f'Failed to load {fn} as json settings file.')
                print('Using default values.')
                
                self.stuff =  {
                  "dbga"         : "OFF"
                , "dbgb"         : "OFF"
                , "dbgc"         : "OFF"

                , "SAVE_GAME_AS_CSV"  : "OFF"
                , "SAVE_GAME_DIR"     : "llm_training_data"

                , "SAVE_PLOT_AS_PDF"  : "OFF"
                , "SAVE_PLOT_DIR"     : "llm_training_plots"
                , "SHOW_PLOT"         : "ON"

                , "GOOD_EVENT_COLOR"  : "mediumseagreen"
                , "BAD_EVENT_COLOR"   : "cornflowerblue"
                , "GRID_COLOR"        : "dimgrey"
                , "STINT_COLOR"       : "dimgrey"
                , "PM_PLUS_COLOR"     : "maroon"
                , "PM_MINUS_COLOR"    : "darkgreen"
                , "TABLE_COLOR"       : "goldenrod"
                , "PLOT_COLOR_STYLE"  : "dark_background"
            
                , "STINT_COLOR_PLUS"       : "forestgreen"
                , "STINT_COLOR_MINUS"      : "firebrick"

                , "MARKER_2_STACK_OFFSET"  : 2.7 
                , "MARKER_3_STACK_OFFSET"  : 4.7
                , "MARKER_WIDTH"           : 28
                , "MARKER_FONTSCALE"       : 2.7
                , "MARKER_FONTWEIGHT"      : "demi"
                , "GRID_linewidth"         : 1.2

                , "BOX_COL_COLOR"         : "sienna"
                , "BOX_COL_COLOR_ALT"     : "chocolate"

                , "START_DAY"            : "2024-05-01" 
                , "STOP_DAY"             : "2024-05-31"
                , "TEAM"                 : "OKC"
            
                , "dSOURCE"    : "nba.sqlite"
                , "SOURCE"     : "WEB:"
                , "zSOURCE"    : "FILE:llm_results/claude_sonnet.csv"
                , "tSOURCE"    : "FILE:llm_training_data"
                , "cSOURCE"    : "CLAUDE:claude_test"
     
                }                

    def get(self, _name):
       return self.stuff[_name]

    def set(self,_name, _value):
       self.stuff[_name] = _value

    def save(self):
        with open(self.fn, "w") as f:
            json.dump(self.stuff, f, indent=4)   
