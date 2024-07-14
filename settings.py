import json 

defaults = None

class default :
    
    stuff = {}

    def __init__(self,fn='.wwmdd/settings.json'):
        
        if fn == None: fn = '.wwmdd/settings.json'
        try:    
            with open(fn, "r") as f:
                self.stuff = json.load(f)
        except:
                print(f'Failed to load {fn} as json settings file.')
                print('----------- Using default values.       ------------ ')
                # copy/paste contents of wwmmd.json here to update defaults
                self.stuff = {
        "LOG"         : "ON"
        , "TRIM"        : "OFF"      
        , "CONSOLE"     : "ON"

        , "dbga"        : "OFF"
        , "dbgb"        : "OFF"
        , "dbgc"        : "OFF"

        , "COLOR_DEFAULTS"        : "wwmdd_colors.json"

        , "SUB_PLOTS"            : [       "stints", "events", "score", "margin", "periodscores", "boxscore"]
        , "example_SUB_PLOTS"    : ["all", "stints", "events", "score", "margin", "periodscores", "boxscore"]
        
        , "SHOW" : ["plot","csv"]
        , "example_SHOW" : ["plot","csv","raw","pdf","stints", "overlaps","logs"]

        , "SOURCES" : ["web","file","db"]
        , "AI"      : ["GEMINI", "CLAUDE"]


        , "TEST_PLAYERS"          :  []
        , "example_TEST_PLAYERS"  :  ["Josh Giddey"]

        , "SAVE_GAME_AS_CSV"      : False
        , "SAVE_RAW_GAME_AS_CSV"  : False

        , "SAVE_SUBS_FILE"        : False

        , "PLAY_TIME_CHECK_ONLY"  : False
        , "PLAY_TIME_CHECK_SHOW"  : "OFF"

        , "example_PLAY_TIME_CHECK_SHOW"  : "ON,OFF,FAIL_ONLY"

        , "EXAMPLE_SHOW_OVERLAP"  : "OKC"
        , "SHOW_OVERLAP"          : "NONE"
        , "OVERLAP_GROUP"         : [2]
    
        , "SAVE_GAME_DIR"     : "llm_training_data"
    
        , "SAVE_PLOT_IMAGE"  : False

        , "SAVE_PLOT_DIR"     : "llm_training_plots"

        , "SHOW_PLOT"         : True

        , "START_DAY"            : "2024-01-01" 
        , "STOP_DAY"             : "2024-01-30"
        , "TEAM"                 : "OKC"
    
        , "FILE"         : "llm_training_data"

        , "SOURCE"      : "WEB:"
        , "aSOURCE"       : "FILE:llm_training_data"
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
