import pandas as pd

from play_by_play import generatePBP
from plots import plot3, settings

def main(file_dir_name):

    import os

    if os.path.isdir(file_dir_name):
        cwd = os.getcwd() + '/' + file_dir_name
        files = [os.path.join(cwd, f) for f in os.listdir(cwd) if os.path.isfile(os.path.join(cwd, f))]
    else:
        files = [file_dir_name]
        
    for filename in files:
        if '.csv' not in filename: continue
        df = pd.read_csv(filename, keep_default_na=False)
        df.iloc[::-1] # reverse dataframe

        event_map = {
            '2POINT'			: [1,1], 
            '2POINT.ASSIST'	    : [1,1,2], 
            '3POINT'            : [1,1],
            '3POINT.ASSIST'     : [1,2],
            'FTMAKE'            : [3,1], 
            'FTMISS'            : [3,1], 
            '2POINTMISS'        : [2,1],
            '3POINTMISS'        : [2,1],
            '2POINTMISS.BLOCK'  : [2,1,2],
            '3POINTMISS.BLOCK'  : [2,1,2],
            'REBOUND'			: [4,1],
            'STEAL'				: [5,1], 
            'TURNOVER'			: [5,2], 
            'STEAL.TURNOVER'    : [5,1,2],
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
                    r.neutraldescription, 
                    r.neutraldescription, 
                    r.neutraldescription,
                    r.score, r.scoremargin,
                    r.player1_name, r.player1_team_abbreviation,
                    r.player2_name, r.player2_team_abbreviation,
                    r.player3_name, r.player3_team_abbreviation]
                    
                    oink.extend([a])
            
        play_by_play = pd.DataFrame(
                    data    = oink,           # values
                    # index   = oink [1:,0],    # 1st column as index
                    columns = new_cols)  

        # who's home and away based on score
        # score is always home_score - away_score
        # find first score for home and away and get
        # team from player1's team abbreviation i.e. 'OKC' 'DAL' etc.
        
        home = None
        away = None
        for i,r in play_by_play.iterrows():
            if r.score == '0':
                scr = ['0','0']
            else:
                scr = r.score.split('-')
            home_scr = int(scr[0])
            if home_scr != 0 and home == None:  
                home = r.player1_team_abbreviation 
                
            away_scr = int(scr[1])

            if away_scr !=0 and away == None:
                away = r.player1_team_abbreviation
                
            if (home != None) and (away != None): 
                break    

        ha_scores = play_by_play.tail(1).score.tolist()[0].split('-')
        
        game_data = {
        'season_id_home' :'',
        'team_id_home'	: '',
        'team_abbreviation_home': home,
        'team_name_home': '',
        'game_id'		: os.path.splitext(os.path.basename(filename))[0],
        'game_date'		: '2024-04-27',
        'matchup_home'	: f'{away} @ {home}',
        'wl_home'		: 'W' if int(ha_scores[0]) > int(ha_scores[1]) else 'L',
        'pts_home'      : ha_scores[0],
        'pts_away'      : ha_scores[1],
        'blk_home'		: '',
        'season_id_away': '',
        'team_id_away'	: '',
        'team_abbreviation_away': away,
        'team_name_away': '',
        'game_id_away'	: '',
        'game_date_away': '',
        'matchup_away'	: f'{home} vs. {away}',
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
