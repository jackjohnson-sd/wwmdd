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
                    , "dbgc"          : "OFF"

                    , "SAVE_GAME_AS_CSV"  : "ON"
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


                    , "MARKER_2_STACK_OFFSET"  : 1.8 
                    , "MARKER_3_STACK_OFFSET"  : 3.4
                    , "MARKER_WIDTH"           : 28
                    , "MARKER_FONTSCALE"       : 2.85
                    , "MARKER_FONTWEIGHT"      : "demi"
                    , "GRID_linewidth"         : 0.5

                    , "BOX_COL_COLOR"         : "sienna"
                    , "BOX_COL_COLOR_ALT"     : "chocolate"
                    , "BOX_COL_MAX_COLOR"     : "goldenrod"

                    , "START_DAY"            : "2024-04-27" 
                    , "STOP_DAY"             : "2024-05-15"
                    , "TEAM"                 : "OKC"
                
                    , "SOURCE"     : "WEB:"
                    , "dSOURCE"    : "nba.sqlite"
                    , "fSOURCE"    : "FILE:gemini_test"
                    , "zSOURCE"    : "FILE:claude_test"

                    , "cSOURCE"    : "CLAUDE:claude_test"
                    , "gSOURCE"    : "GEMINI:gemini_test"
                    , "tSOURCE"    : "TOKENS:gemini_test"
                }
     

    def get(self, _name):
       return self.stuff[_name]

    def set(self,_name, _value):
       self.stuff[_name] = _value

    def save(self):
        with open(self.fn, "w") as f:
            json.dump(self.stuff, f, indent=4)   
