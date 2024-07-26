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
                    "COLOR_DEFAULTS"  : ".wwmdd/colors.json"

                    , "LOG"             : True
                    , "LOG_LEVEL"       : "DEBUG"
                    , "LOG_FILE"        : ".wwmdd/logs/wwmdd.log"
                    , "LOG_ROTATION"    : "1 hour"
                    , "LOG_RETENTION"   : "1 week"
                    , "LOG_COLORIZE"    : ["sys.stdout"]
                
                    , "SAVE_PREFIX"     : ""
                    , "SAVE_GAME"       : False
                    , "SAVE_RAW"        : False
                    , "SAVE_STINTS"     : False
                    , "SAVE_OVERLAP"    : False
                    , "SAVE_BOX_SCORE"  : False
                    , "SAVE_IMAGE"      : False
                    , "SAVE_SUBS_FILE"  : False

                    , "SAVE_DIR"        : "llm/llm_training_data"

                    , "SAVE_IMAGE_TYPE" : "png"
                    , "SAVE_IMAGE_DPI"  : 300

                    , "OVERLAP_GROUP"   : [2]

                    , "SHOW_PLOT"       : True
                    , "PLOT_WAIT"       : -1
                
                    , "PARTS"           : [ "stints", "score", "margin", "periodscores", "boxscore"]

                    , "DBG"             : False
                    , "TEST_PLAYERS"    : []
                    
                    , "TEAM"            : "OKC"
                    , "START_DAY"       : "2024-04-29" 
                    , "STOP_DAY"        : "2024-04-29"
                    , "SOURCE"          : "WEB:"
                

                    , "tSOURCE"     : "TESTPARTSCALE:"  
                    , "bSOURCE"     : "FILE:llm/llm_training_data/csv"
                    , "cSOURCE"     : "FILE:llm/llm_training_data/csv/OKCvGSW20230130.csv"
                    , "dSOURCE"     : "CLAUDE:claude_test"
                    , "eSOURCE"     : "GEMINI:gemini_test"
                    , "fSOURCE"     : "TOKENS:gemini_test"
                    , "nSOURCE"     : "nba.sqlite"

                    , "example_PARTS"   : ["all", "tools", "stints", "events", "score", "margin", "periodscores", "boxscore","legend"]
                    , "example_SHOW"    : ["plot","csv","raw","img","stints", "overlaps","logs"]
                    , "AI"              : ["GEMINI", "CLAUDE"]
                    , "TRIM"            : False       
                    , "CONSOLE"         : True
                    , "example_TEST_PLAYERS"  :  ["Josh Giddey"]
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
            logger.error(f'INVALID settings key {_name}')
            return None
        
    def set(self,_name, _value):
       self.stuff[_name] = _value

    def save(self):
        with open(self.fn, "w") as f:
            json.dump(self.stuff, f, indent=4)   
