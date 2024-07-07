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
                print('----------- Using default values.       ------------ ')
                # copy/paste contents of wwmmd.json here to update defaults
                self.stuff =  {
                    
                      "LOG"         : "OFF"
                    , "TRIM"        : "OFF"      
                    , "CONSOLE"     : "ON"

                    , "dbga"        : "OFF"
                    , "dbgb"        : "OFF"
                    , "dbgc"        : "OFF"

                    , "SHOW_PLOTS"            : [       "STINTS", "EVENTS", "SCORE", "xMARGIN", "PERIOD_SCORES", "BOX_SCORE"]
                    , "example_SHOW_PLOTS"    : ["ALL", "STINTS", "EVENTS", "SCORE", "MARGIN", "PERIOD_SCORES", "BOX_SCORE"]

                    , "TEST_PLAYERS"          :  []
                    , "example_TEST_PLAYERS"  :  ["Josh Giddey"]

                    , "SAVE_GAME_AS_CSV"      : "OFF"
                    , "SAVE_RAW_GAME_AS_CSV"  : "OFF"

                    , "PLAY_TIME_CHECK_ONLY"  : "OFF"

                    , "EXAMPLE_SHOW_OVERLAP"  : "OKC"
                    , "SHOW_OVERLAP"          : ""
                    , "OVERLAP_GROUP"         : [4,5]

                    , "PLAY_TIME_CHECK_SHOW"  : "OFF"
                    , "example_PLAY_TIME_CHECK_SHOW"  : "ON,OFF,FAIL_ONLY"

                    , "SAVE_SUBS_FILE"   : "OFF"
                
                    , "SAVE_GAME_DIR"     : "llm_training_data"
                
                    , "SAVE_PLOT_AS_PDF"  : "OFF DOES NOT WORK"
                    , "SAVE_PLOT_DIR"     : "llm_training_plots"
                    , "SHOW_PLOT"         : "ON"

                    , "GOOD_EVENT_COLOR"  : "mediumseagreen"
                    , "BAD_EVENT_COLOR"   : "cornflowerblue"
                    , "GRID_COLOR"        : "dimgrey"

                    , "STINT_COLOR"       : "dimgrey"
                    , "STINT_COLOR_IN"    : "limegreen"
                    , "STINT_COLOR_OUT"   : "darkorange"

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

                    , "START_DAY"            : "2023-01-30" 
                    , "STOP_DAY"             : "2023-01-30"
                    , "TEAM"                 : "OKC"
                
                    , "SOURCE"      : "WEB:"
                    , "aSOURCE"     : "FILE:llm_training_data"
                    , "aaSOURCE"     : "FILE:llm_training_data/RAW_BOSvOKC20240403.csv"
                
                    , "dSOURCE"     : "CLAUDE:claude_test"
                    , "eSOURCE"     : "GEMINI:gemini_test"
                    , "fSOURCE"     : "TOKENS:gemini_test"
                    , "nSOURCE"     : "nba.sqlite"

                }
                

    def get(self, _name):
       return self.stuff[_name]

    def set(self,_name, _value):
       self.stuff[_name] = _value

    def save(self):
        with open(self.fn, "w") as f:
            json.dump(self.stuff, f, indent=4)   
