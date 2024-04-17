
from datetime import datetime,timedelta

from utils import totalTeamMinutes
from data_management import loadNBA_data
from play_by_play import generatePBP 
from box_score import bs_setBoxScore, bs_dump, bs_clean, bs_sum_item
from plots import plot3
from games_by_team import create_games_by_team,filterGamesByDateRange

START_SEASON = '2020-01-01'
DB_FILENAME = "nba.sqlite"
SECONDS_PER_PERIOD = 12*60
SECONDS_PER_GAME   = 4*SECONDS_PER_PERIOD

HOME_TEAM  = 'OKC'
AWAY_TEAM  = 'OKC'

dfs = {}            # has everthing that was in db as dict of DateFrame by column name from DB
gamesByTeam = {}    # gamesByTeam[NICK_NAME][SEASON][DATE]  ['OKC']['2022']['2022-12-01']
db_con = None       # keep this around to get play_by_play when needed

def loadNBA():

    global db_con

    _dfs, db_con = loadNBA_data(DB_FILENAME)

    _gamesByTeam = create_games_by_team(_dfs, db_con, START_SEASON, ['OKC'])    

    return _dfs, _gamesByTeam   
  
def getTestData(_games):

    _START_DAY = '2022-01-31'
    _STOP_DAY = '2022-04-31'
    _TEAM = HOME_TEAM
    _SEASON = '2021'

    results = filterGamesByDateRange( _START_DAY, _STOP_DAY, _games[_TEAM][_SEASON])
    return results, _START_DAY, _STOP_DAY, _TEAM, _SEASON

def main():

    global dfs 
    global gamesByTeam

    # gamesByTeam['OKC']['2022]['2023-01-03']  -- gets game via team,year,game_date

    dfs,gamesByTeam = loadNBA()

    test_data = getTestData(gamesByTeam)
    
    start_duration_by_date = generatePBP(test_data)

    dates = list(start_duration_by_date.keys())

    for date in dates:
        game = start_duration_by_date[date][0]
        players = list(game.keys())

        starters = []
        for player in players:
            if game[player][0][0] == ['IN',1,'12:00']:
                starters += [player]            
        bench = list(set(players) - set(starters))
        players = starters + bench

        bs_setBoxScore(start_duration_by_date[date][2])
        
        total_secs_playing_time = bs_sum_item('secs')

        g = gamesByTeam[HOME_TEAM]['2021'][date]
        if g.matchup_home.split(' vs. ')[0] == HOME_TEAM:
            score = f'{int(g.pts_home)}-{int(g.pts_away)}'
        else:
            score = f'{int(g.pts_away)}-{int(g.pts_home)}'

        t = str(timedelta(seconds=total_secs_playing_time)).split(':')
        title = f'{g.matchup_home} {score}  {date} '
        debug_title = f'DEBUG {t[0]}:{t[1]}  {g.game_id}'

        if total_secs_playing_time != SECONDS_PER_GAME*5 or True: 
            ps = list(start_duration_by_date[date][0].keys())
            #dump_play_by_play(['Kenrich Williams'], g.play_by_play[0])
    
            plot3(start_duration_by_date[date], title, g.play_by_play, debug_title)    


    """
    tests(test_data)
    t = pd.DataFrame(test_data[0]).T
    plot1(t)
    #input("Press Enter to continue...")
    plot2(t)
    #input("Press Enter to continue...")
    """

if __name__ == "__main__":
    main()

"""
play_by_play feilds

[
'game_id', 'eventnum', 

'eventmsgtype', 
'eventmsgactiontype', 

'period', 'wctimestring', 'pctimestring', 

'homedescription', 
'neutraldescription', 
'visitordescription', 

'score', 
'scoremargin', 

'person1type', 'player1_id', 'player1_name', 'player1_team_id', 'player1_team_city', 'player1_team_nickname', 'player1_team_abbreviation', 
'person2type', 'player2_id', 'player2_name', 'player2_team_id', 'player2_team_city', 'player2_team_nickname', 'player2_team_abbreviation', 
'person3type', 'player3_id', 'player3_name', 'player3_team_id', 'player3_team_city', 'player3_team_nickname', 'player3_team_abbreviation', 

'video_available_flag'
]

game feilds
[
    'season_id', 'team_id_home', 
    'team_abbreviation_home', 'team_name_home',
    'game_id', 'game_date', 'matchup_home', 'wl_home', 'min', 

    'fgm_home','fga_home', 'fg_pct_home', 'fg3m_home', 'fg3a_home', 'fg3_pct_home',
    'ftm_home', 'fta_home', 'ft_pct_home', 'oreb_home', 'dreb_home',
    'reb_home', 'ast_home', 'stl_home', 'blk_home', 'tov_home', 'pf_home',
    'pts_home', 'plus_minus_home', 
       
    'video_available_home', 
    
    'team_id_away', 'team_abbreviation_away', 'team_name_away', 'matchup_away', 'wl_away',
       
    'fgm_away', 'fga_away', 'fg_pct_away', 
    'fg3m_away', 'fg3a_away','fg3_pct_away', 
    'ftm_away', 'fta_away', 'ft_pct_away', 
    'oreb_away', dreb_away', 'reb_away', 
    'ast_away', 'stl_away', 'blk_away', 'tov_away', 'pf_away', 
       
    'pts_away', 'plus_minus_away', 
       
       'video_available_away',
       'season_type', 
       'play_by_play'

 keeps = ['Shai Gilgeous-Alexander','Jalen Williams', 'Josh Giddey', 
     'Tre Mann','Jaylin Williams', 'Dario Saric', 'Ousmane Dieng'
     'Isaiah Joe', 'Kenrich Williams',
     'Mike Muscala','Luguentz Dort','Aaron Wiggins','Jeremiah Robinson-Earl' ]

"""