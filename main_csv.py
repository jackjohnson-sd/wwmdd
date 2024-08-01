import os
import pandas as pd
from loguru import logger

from plots import plot3
from play_by_play import generatePBP
from utils import time_sorted

def main(file_dir_name):

    if os.path.isdir(file_dir_name):
        try:
            cwd = os.path.join(os.getcwd(), file_dir_name)
            files = time_sorted(cwd,file_dir_name)
            # files = [os.path.join(cwd, f) for f in os.listdir(cwd) if os.path.isfile(os.path.join(cwd, f))]
        except:
            logger.error('sorted file error')
    else:
        files = [file_dir_name]
        
    if len(files) == 0:
        logger.debug(f'NO files found ... {file_dir_name}')
        
    else:     
      for filename in files:
        # print(filename)
        name = os.path.basename(filename)
        
        if '##' in filename:
            logger.debug('COMMENT:',filename) 
            continue
        
        if '.csv' not in filename: 
            logger.warning(f'Non csv file {name}. Skipped')
            continue
        
        if 'STINTS_' in filename: continue
        if 'OVERLAP' in filename: continue       
        if 'BOX_' in filename: continue       
        if 'RAW_' in filename: continue       
        
        if len(name) not in [19,22]:
            logger.error(f'file name {len(name)} {name} wrong length. Skipped.')
            continue
        
        if not (os.path.isfile(filename)):
            logger.error(f'file {filename} fails isfile . Skipped.')
            continue
        
        df = pd.read_csv(filename, keep_default_na=False)
        if df.shape[1] != 13:
            continue
            
        try:
            n = os.path.basename(filename)[-12:-4]
            if len(n) == 8:
                game_date = n[0:4] + '-' + n[4:6] + '-' + n[6:8]
            else:
                game_date = '-- NO DATE '
        except:
            game_date = '-- NO DATE '
        
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
            'VIOLATION'         : [7,1,2], 
            'SUB'		        : [8,1,2],  # id#, player[1,2,3] 
            'JUMPBALL'          : [10,1,2,3],
            'EJECTION'          : [11,1,2,3],
            'STARTOFPERIOD'		: [12,1,1], 
            'ENDOFPERIOD'       : [13,1,1],
            'TIMEOUT'			: [None], 
            'END_GAME'			: [None], 
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
        
        oink = []
        prev = None
        rprev = None
        for i, r in df.iterrows():
            
            if type(rprev) != type(None):
                if r.equals(rprev):
                    logger.error(f'{os.path.basename(filename)} DUP {r.period} {r.pctimestring} {r.neutraldescription}')
                    continue
                
            rprev = r
            
            if r.eventmsgtype not in event_map.keys():
                logger.warning(f' unused event {r.eventmsgtype} {r.player1_name} {r.player3_name} {r.player3_name}')
            else:
                        
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
                    r.player3_name, r.player3_team_abbreviation,]
                    
                    if type(prev) != type(None):
                        
                        if prev == a:
                            logger.error(f'{os.path.basename(filename)} 2DUP {r.period} {r.pctimestring} {r.neutraldescription}')
                            continue
            
                    prev = a
                    oink.extend([a])
                    # if r.player1_name == 'Mike Muscala':
                    #     if id[0] in [1,3]:
                    #         print(r.player1_name,id,r.eventmsgtype,r.score)
            
        play_by_play = pd.DataFrame(
                    data    = oink,           # values
                    # index   = oink [1:,0],    # 1st column as index
                    columns = new_cols)  

        # who's home and away based on score
        # score is always away_score - home_score
        # find first score for home and away and get
        # team from player1's team abbreviation i.e. 'OKC' 'DAL' etc.
        
        home = None
        away = None
        home_scr = None
        away_scr= None

        for i,r in play_by_play.iterrows():
            
            if r.score == '0' or r.score == '':
                scr = ['0','0']
            else:
                scr = r.score.split('-')
                
            home_scr = int(scr[1])
            
            if home_scr != 0 and home == None:  
                home = r.player1_team_abbreviation 
                
            away_scr = int(scr[0])

            if away_scr !=0 and away == None:
                away = r.player1_team_abbreviation
                
            if (home != None) and (away != None): 
                break    

        if home == None: home = 'OKC'
        if away == None: away = 'GSW'
        if home_scr == None: home_scr = '0'
        if away_scr == None: away_scr = '0'
         
        ha_scores = play_by_play.tail(1).score.tolist()[0].split('-')
        
        if len(ha_scores) != 2:
            ha_scores = ['0','0']
            
        game_data = {
        'season_id_home' :'',
        'team_id_home'	: '',
        'team_abbreviation_home': home,
        'team_name_home': '',
        'game_id'		: os.path.splitext(os.path.basename(filename))[0],
        'game_date'		: game_date,
        'matchup_home'	: f'{home} vs. {away}',
        'wl_home'		: 'W' if int(ha_scores[1]) > int(ha_scores[0]) else 'L',
        'pts_home'      : ha_scores[1],
        'pts_away'      : ha_scores[0],
        'blk_home'		: '',
        'season_id_away': '',
        'team_id_away'	: '',
        'team_abbreviation_away': away,
        'team_name_away': '',
        'game_id_away'	: '',
        'game_date_away': '',
        'matchup_away'	: f'{away} @ {home}',
        'wl_away'		: '',
        'blk_away'        : '',
        'tov_away'        : '',
        'pf_away'         : '',
        'plus_minus_away' :'',
        'play_by_play'    : play_by_play
        }

        pds_game_data = pd.Series(game_data)
        
        our_playerstints_and_boxscore      = generatePBP(pds_game_data, home)
        opponent_playerstints_and_boxscore = generatePBP(pds_game_data, home, get_opponent_data=True)

        plot3(home, pds_game_data,
            our_playerstints_and_boxscore,
            opponent_playerstints_and_boxscore)
        