import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
from datetime import datetime,timedelta

from utils import period_clock_seconds, secDiff,totalTeamMinutes
from tests import testPBPforErrors
from data_management import loadNBA_data

START_SEASON = '2020-01-01'
DB_FILENAME = "nba.sqlite"
SECONDS_PER_PERIOD = 12*60
SECONDS_PER_GAME   = 4*SECONDS_PER_PERIOD

HOME_TEAM  = 'OKC'
AWAY_TEAM  = 'OKC'

from plots import plot3


dfs = {}            # has everthing that was in db as dict of DateFrame by column name
gamesByTeam = {}    # reorganized game data is in gamesByTeam
db_con = None

def loadNBA():

    global db_con

    _dfs, db_con = loadNBA_data(DB_FILENAME)
    _gamesByTeam = {}

    print('LOAD COMPLETE') 

    #for nickName in _dfs['team'].abbreviation:
    for nickName in [HOME_TEAM]:

        _games = getGames(_dfs['team'], _dfs['game'], nickName, 'Regular Season', START_SEASON)
        seasons = list(set(_games.season_id))
        seasons.sort()
        print(nickName, end = ' ')
        _gamesBySeason = {}
        for season in seasons:
            seasonGames = _games.query(f'season_id == "{season}"')
            
            _gamesByDate = {}
            badBunny = 0
            for index, _game in seasonGames.iterrows():
                gameDay = _game.game_date.split(' ')[0] # trims the h:m:s part off

                qs = f"select * from play_by_play where game_id == '{_game.game_id}'"
                pbps = pd.read_sql_query(qs, db_con)
                if pbps.shape[0] == 0:
                    badBunny += 1
                    if _game.play_by_play[0].shape[0] != 0:
                        print('BADBAD', _game.game_date, _game.game_id)
                    #print('BB ',gameDay,season,game.game_id)
                else:
                    _dfs['game'].loc[index, 'play_by_play'] = [pbps]
                    _game.play_by_play = [pbps]
                    #print(index,gameDay,pbps.shape)
                _gamesByDate[gameDay] = _game

            print(f' {season}:{len(_gamesByDate)}:{badBunny} ',end='')
            _gamesBySeason[season] = _gamesByDate
        print()
        
        _gamesByTeam[nickName] = _gamesBySeason      

    return _dfs, _gamesByTeam       
  
def getGames(teams, games, teamNickName, seasonType, startDate):
    teamID = teams.query(f'abbreviation == "{teamNickName}"').id.values[0] 
    return games.query(f'season_id >= "{startDate}" and season_type == "{seasonType}" and (team_id_home == "{teamID}" or team_id_away == "{teamID}")')

def filterGamesByDateRange(start, stop, games):
    return  {key: value for key, value in games.items() if start <= key <= stop}

def getTestData():

    _START_DAY = '2023-01-01'
    _STOP_DAY = '2023-03-31'
    _TEAM = HOME_TEAM
    _SEASON = '2022'

    results = filterGamesByDateRange( _START_DAY, _STOP_DAY, gamesByTeam[_TEAM][_SEASON])
    return results, _START_DAY, _STOP_DAY, _TEAM, _SEASON

def dump(df,keepers):
    for i in df.index:
        ts = ''
        for col in keepers:
            t =  df[col].loc[i:i].values[0]
            if t != None :
                ts += f'{t} '
        print(ts)

def dump_play_by_play(players,events,pbp):

    for player in players:
        print()
        print(player,' -----------------')
        subs = pbp[0].query(
            f'(eventmsgtype == 8) and (player1_name == "{player}" or player2_name == "{player}")'
            )
        if subs.shape[0] == 0: print('dump_play_by_play() Error A', player, e.eventnum, e.game_id)
        else:
            for key,e in subs.iterrows():
                print(
                    f'{e.period} {e.pctimestring:<5} IN:{e.player2_name:<20} OUT:{e.player1_name:<20} {e.homedescription}'
                )

def getTimeSpansByPlayer(games,players):
    _timeSpans = {}  # collect timespans played by this player
    for player in players:
        _timeSpans[player] = []
        for x in games.index:
            z = games.loc[x]
            p1 = z['player1_name']
            p2 = z['player2_name']
            if (p1 == player) or (p2 == player):
                t = 'IN' if p2 == player else "OUT"
                _timeSpans[player].append([t,z.period,z.pctimestring]) 
    return _timeSpans

def generatePBP():
   
    test_data, _start, _stop, _team, _season = getTestData()
 
    test_days = list(test_data.keys())

    starttime_duration_bydate = {}
    for date in test_days:

        starttime_duration_byPlayer = {}

        pbp_forDate = test_data[date].play_by_play[0]
        if pbp_forDate.shape[0] != 0:   

            sc1 = pbp_forDate.query('eventmsgtype == 1 or eventmsgtype == 3')
            scores = list(filter(lambda x:x != None,sc1.score))
            score_errors = 0
            for x,y in zip(scores,scores[1:]):
                a = x.split(' - ')
                b = y.split(' - ')
                if a[0] == b[0]  :
                    if a[1] == b[1]: 
                        score_errors += 1
                        #print('ERROR A',x,y)
                else: 
                    if a[1] != b[1]:
                        score_errors += 1
                        #print('ERROR B',x,y) 
            # 8 substitution event, get our players thata are subbed IN/OUT
            pbp_subs = pbp_forDate.query('eventmsgtype == 8') 

            # player1 IN, player2 OUT 
            p1s = pbp_subs.query('player1_team_abbreviation == "OKC"')['player1_name'] 
            p2s = pbp_subs.query('player2_team_abbreviation == "OKC"')['player2_name']

            playersInGame = list(set(p1s) | set(p2s))          
             
            timeSpans = getTimeSpansByPlayer(pbp_subs,playersInGame)  # collect timespans played by this player

            for player in list(timeSpans.keys()):
                _tss = timeSpans[player]
                starttime_duration_byPlayer[player] = []

                if len(_tss) > 0:

                    # our problem of the minute is lineup
                    # changes are not reported if they occur
                    # during stopage at end of period. so fix it by ...

                    # if first entry is OUT add IN at start of period
                    if _tss[0][0] == 'OUT':
                        _tss = [['IN',_tss[0][1],'12:00']] + _tss
                    # if last entry is IN add OUT at end of period     
                    if _tss[-1][0] == 'IN':
                        _tss.append(['OUT',_tss[-1][1],'0:00'])

                    # if we find two INs or OUTs together
                    # insert IN or OUT bettween them at the begining of period
                    insertsAdded = True    
                    while insertsAdded:
                        insertsAdded = False
                        lenTss = len(_tss)
                        for x in zip(range(0,lenTss),range(1,lenTss)):
                            ts1 = _tss[x[0]]
                            ts2 = _tss[x[1]]
                            if ts2[0] == ts1[0]:  # both INs or OUTs
                                if ts1[0] == 'IN':
                                    newTimeStamp = ['OUT', ts1[1], '00:00']
                                else: 
                                    newTimeStamp = ['IN',ts2[1],'12:00']
                                _tss.insert(x[1],newTimeStamp) 
                                #print(player,x)
                                insertsAdded = True
                                break
                    
                    lenTss = len(_tss)
                    for x,y in zip(range(0,lenTss,2),range(1,lenTss,2)):
                        start_ts  = _tss[x]
                        stop_ts   = _tss[y]
                        if start_ts[0] == 'IN' and stop_ts[0] == 'OUT':
                            ts = secDiff(start_ts,stop_ts)
                            #ts_str = str(timedelta(seconds=ts))
                            #print(f'{date} [{start_ts[0]:>2}, {start_ts[1]:>1}, {start_ts[2]:>5}], [{stop_ts[0]:>2}, {stop_ts[1]:>1}, {stop_ts[2]:>5}], {ts_str}')

                            starttime_duration_byPlayer[player].append([start_ts,ts,stop_ts])
                        else:
                            print('Error',player,x)   
            
            starttime_duration_bydate[date] = [starttime_duration_byPlayer,score_errors]

    return starttime_duration_bydate

def main():

    global dfs 
    global gamesByTeam

    # gamesByTeam['OKC']['2022]['2023-01-03']  -- gets game via team,year,game_date

    dfs, gamesByTeam = loadNBA()

    start_duration_by_date = generatePBP()

    testPBPforErrors(start_duration_by_date)

    dates = list(start_duration_by_date.keys())

    for date in dates:
        g = gamesByTeam[HOME_TEAM]['2022'][date]
        g.pts_home
        g.pts_away
        if g.matchup_home.split(' vs. ')[0] == HOME_TEAM:
            score = f'{int(g.pts_home)}-{int(g.pts_away)}'
        else:
            score = f'{int(g.pts_away)}-{int(g.pts_home)}'

        total = totalTeamMinutes(start_duration_by_date, date)
        t = str(timedelta(seconds=total)).split(':')
        title = f'{g.matchup_home} {score} {date} {t[0]}:{t[1]} {g.game_id}'

        if total != SECONDS_PER_GAME*5 or True: 
            players = list(start_duration_by_date[date][0].keys())
            dump_play_by_play(players,[8],g.play_by_play)
            plot3(start_duration_by_date[date], title, g.play_by_play)    


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