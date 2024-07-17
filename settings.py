import json 
from loguru import logger

defaults = None
colors = None

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
                self.stuff = \
                {
                 "LOG"             : False
                , "LOG_ROTATION"    : "1 hour"
                , "LOG_RETENTION"   : "1 week"
                , "LOG_LEVEL"       : "DEBUG"

                , "TRIM"        : False       
                , "CONSOLE"     : True

                , "DBG"         : False

                , "COLOR_DEFAULTS"        : ".wwmdd/colors.json"

                , "SUB_PLOTS"            : [       "stints", "events", "score", "margin", "periodscores", "boxscore","legend"]
                , "example_SUB_PLOTS"    : ["all", "tools", "stints", "events", "score", "margin", "periodscores", "boxscore","legend"]
                
                , "SHOW" : ["plot","csv","img"]
                , "example_SHOW" : ["plot","csv","raw","img","stints", "overlaps","logs"]

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
            
                , "SAVE_GAME_DIR"     : "llm/llm_training_data/csv"
            
                , "SAVE_PLOT_IMAGE"  : False
                , "SAVE_PLOT_DIR"     : "llm/llm_training_data/img"
                , "SAVE_PLOT_TYPE"    : "png"
                , "SAVE_PLOT_DPI"     : 300

                , "SHOW_PLOT"         : True
                , "SHOW_PAUSE"        : -1

                , "START_DAY"            : "2024-04-29" 
                , "STOP_DAY"             : "2024-04-29"
                , "TEAM"                 : "OKC"
            
                , "FILE"        : "llm/llm_training_data/csv"

                , "SOURCE"      : "WEB:"
                , "bSOURCE"     : "FILE:llm/llm_training_data/csv"
                , "cSOURCE"     : "FILE:llm/llm_training_data/csv/OKCvGSW20230130.csv"
            
                , "dSOURCE"     : "CLAUDE:claude_test"
                , "eSOURCE"     : "GEMINI:gemini_test"
                , "fSOURCE"     : "TOKENS:gemini_test"
                , "nSOURCE"     : "nba.sqlite"
        }   

    def update_colors(self,fn):
        try:    
            with open(fn, "r") as f:
                newstuff = json.load(f)
                colors.stuff = {**colors.stuff,**newstuff}
        except:
            logger.error(f'Failed to load {fn} as colors json file.')
            
    def update(self,fn):
        try:    
            with open(fn, "r") as f:
                newstuff = json.load(f)
                self.stuff = {**self.stuff,**newstuff}
        except:
            logger.error(f'Failed to load {fn} as json settings file.')
   
    def get(self, _name):
        try:
            return self.stuff[_name]
        except:
            logger.error('INVALID settings key')
            return None
        
    def set(self,_name, _value):
       self.stuff[_name] = _value

    def save(self):
        with open(self.fn, "w") as f:
            json.dump(self.stuff, f, indent=4)   
