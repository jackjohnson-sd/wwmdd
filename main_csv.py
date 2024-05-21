import pandas as pd

from play_by_play import generatePBP
from plots import plot3, settings

def main(filename):

    df = pd.read_csv(filename, keep_default_na=False)
    df.iloc[::-1] # reverse dataframe

    event_map = {
        '2POINT'			: [1,1], 
        '2POINT_ASSIST'	    : [1,1,2], 
        '3POINT'            : [1,1],
        '3POINT_ASSIST'     : [1,2],
        'FTMAKE'            : [3,1], 
        'FTMISS'            : [3,1], 
        '2POINTMISS'        : [2,1],
        '3POINTMISS'        : [2,1],
        '2POINTMISS_BLOCK'  : [2,1,2],
        '3POINTMISS_BLOCK'  : [2,1,2],
        'REBOUND'			: [4,1],
        'STEAL'				: [5,1], 
        'TURNOVER'			: [5,2], 
        'STEAL_TURNOVER'    : [5,1,2],
        'FOUL'				: [6,1], 
        'SUB'		        : [8,1,2],  # id#, player[1,2,3] 
        'TIMEOUT'			: [None], 
        'END_GAME'			: [None], 
        'END_PERIOD'		: [None], 
        'TIP'				: [None], 
        }
    
    new_cols = [
        'eventmsgtype', 'period', 'pctimestring', 
        'homedescription','neutraldescription', 'visitordescription', 
        'score', 'scoremargin', 
        'player1_name', 'player1_team_abbreviation',
        'player2_name', 'player2_team_abbreviation',
        'player3_name', 'player3_team_abbreviation',
       ]

    def bethere(row):
        return event_map[row.eventmsgtype]
    
    oink = []
    for i, r in df.iterrows():
        if r.eventmsgtype in event_map.keys():
            id = event_map[r.eventmsgtype]
            
            if id[0] != None:
                a = [
                id[0],
                r.period, r.pctimestring,
                r.homedescription, 
                r.neutraldescription, 
                r.visitordescription,
                r.score, r.scoremargin,
                r.player1_name, r.player1_team_abbreviation,
                r.player2_name, r.player2_team_abbreviation,
                r.player3_name, r.player3_team_abbreviation]
                
                oink.extend([a])
        
    play_by_play = pd.DataFrame(
                data    = oink,           # values
                # index   = oink [1:,0],    # 1st column as index
                columns = new_cols)  
    
    home = list(play_by_play[play_by_play.homedescription != ''].player1_team_abbreviation)[0]
    away = list(play_by_play[play_by_play.homedescription == ''].player1_team_abbreviation)[0]
    

    game_data = {
    'season_id_home' :'',
    'team_id_home'	: '',
    'team_abbreviation_home': home,
    'team_name_home': '',
    'game_id'		: '',
    'game_date'		: '2024-10-10',
    'matchup_home'	: 'DAL @ OKC',
    'wl_home'		: 'W',
    'pts_home'      : '100',
    'pts_away'      : '101',
    'blk_home'		: '',
    'season_id_away': '',
    'team_id_away'	: '',
    'team_abbreviation_away': away,
    'team_name_away': '',
    'game_id_away'	: '',
    'game_date_away': '',
    'matchup_away'	: '',
    'wl_away'		: '',
    'blk_away'        : '',
    'tov_away'        : '',
    'pf_away'         : '',
    'plus_minus_away' :'',
    'play_by_play'    : play_by_play
    }

    pds_game_data = pd.Series(game_data)
    
    our_playerstints_and_boxscore      = generatePBP(pds_game_data, home)
    opponent_playerstints_and_boxscore = generatePBP(pds_game_data, home, OPPONENT=True)

    plot3(home, pds_game_data,
        our_playerstints_and_boxscore,
        opponent_playerstints_and_boxscore)
