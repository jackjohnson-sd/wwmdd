import json 

class defaults :
    
    stuff = {}
    fn = 'settings.json'

    def __init__(self):
        try:    
            with open(self.fn, "r") as f:
                self.stuff = json.load(f)
        except:
                print(f'Failed to load {self.fn} as json settings file.')
                print('Using default values.')
                
                self.stuff = {
                    'GOOD_EVENT_COLOR': 'mediumseagreen', 
                    'BAD_EVENT_COLOR' : 'cornflowerblue', 
                    'GRID_COLOR'      : 'dimgrey', 
                    'STINT_COLOR'     : 'dimgrey', 
                    'PM_PLUS_COLOR'   : 'maroon', 
                    'PM_MINUS_COLOR'  : 'darkgreen', 
                    'TABLE_COLOR'     : 'darkgoldenrod', 
                    'PLOT_COLOR_STYLE': 'dark_background', 
                    'DB_NAME'         : 'nba.sqlite', 
                    'DATA_START'      : '2020-01-01', 
                    
                    'TESTDATA_START_DAY'    : '2023-01-01', 
                    'TESTDATA_STOP_DAY'     : '2023-04-20', 
                    'TESTDATA_TEAM'         : 'OKC', 
                    'TESTDATA_SEASON'       : '2022',
                    
                    "M2OFFSET"        : 4.0,
                    "M3OFFSET"        : 2.5,
                    "MRK_WIDTH"       : 28,

                    "MRK_FONTSCALE"      : 2.7,
                    "MRK_FONTWEIGHT"    : "demi"
                }

    def get(self, _name):
       return self.stuff[_name]

    def set(self,_name, _value):
       self.stuff[_name] = _value

    def save(self):
        with open(self.fn, "w") as f:
            json.dump(self.stuff, f, indent=4)   
