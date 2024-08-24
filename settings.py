import json 
from loguru import logger

defaults = None
colors = None
patches = None

class default :
    
    push_data = []
    stuff = {}

    def __init__(self, fn='.wwmdd/settings.json', cfd=False):
        
        try:    
            with open(fn, "r") as f:
                self.stuff = json.load(f)
        except:
                if cfd:
                    logger.error(f'failed to load {fn}')
                    self.stuff = \
                    {
                "GOOD_EVENT_COLOR"  : "mediumseagreen"
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
                }
                else:
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
                        
                        , "TEAM"            : ["OKC"]
                        , "START_DAY"       : "2024-04-29" 
                        , "STOP_DAY"        : "2024-04-29"
                        , "SOURCE"          : "WEB:"
                    
                        }

    def update_colors(self,fn):
        try:    
            with open(fn, "r") as f:
                newstuff = json.load(f)
                colors.stuff = {**colors.stuff,**newstuff}
        except:
            logger.error(f'Failed to load {fn} as colors json file.')
            if colors.stuff == {}:
                pass
            
    def push(self): 
        self.push_data.extend([self.stuff.copy()])

    def pop(self): 
        if len(self.push_data) > 0:
            self.stuff = self.push_data[-1]
            self.push_data.pop()
            
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
