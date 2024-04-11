
from datetime import datetime,timedelta
import pandas as pd
import numpy as np

from utils import totalTeamMinutes

# TESTS TESTS TESTS TESTS TESTS TESTS TESTS TESTS
def tests(_testdata,dfs,db_con):
    
    results     = _testdata[0]
    _START_DAY  = _testdata[1]
    _STOP_DAY   = _testdata[2]
    _TEAM       = _testdata[3]
    _SEASON     = _testdata[4]

    resDates = list(results.keys())

    t =  np.array(dfs['game'].team_abbreviation_home) == _TEAM
    t |= np.array(dfs['game'].team_abbreviation_away) == _TEAM
    t &= np.array(dfs['game'].season_id) == _SEASON
    t &= ((
        np.array(dfs['game'].game_date >= resDates[0] + " 00:00:00")
        & np.array(dfs['game'].game_date <= resDates[-2] + " 00:00:00") ))

    g0 = dfs['game'][list(t)].iloc[0]
    r0 = results[resDates[0]]

    print()
    print('testing filterGamesByDateRange',_TEAM, _START_DAY, _STOP_DAY, _SEASON)
    print()

    print('g0',g0.game_date,g0.season_id,g0.matchup_away)
    print('r0',r0.game_date,r0.season_id,r0.matchup_away)

    print()
    print('data for date range',_TEAM, _START_DAY, _STOP_DAY, _SEASON)
    print()

    t_res = pd.DataFrame(results).T

    # TEST list and sum of columns that are numeric

    for colname in t_res.columns:
        firstValueOfColumn = t_res[colname][0:1].values[0]
        if type(firstValueOfColumn) in [type(1),type(1.0)]:
            tmp  = list(t_res[colname])
            print(colname, tmp, sum(tmp))
        #else:
        #    print(f'col name {colname} not numeric.')
            
    # print number of events in our pbp file        
    our_pbps = list(t_res['play_by_play'])

    def fnx(x): 
        if type(x) != pd.DataFrame: return 0
        return x.shape[0]

    pbp_steps = list(map(lambda x: fnx(x), our_pbps))

    print('play by play events', pbp_steps)
def testPBPforErrors(starttime_duration_bydate):

    for a in starttime_duration_bydate:
        total = totalTeamMinutes(starttime_duration_bydate, a)
        scoreErrors = starttime_duration_bydate[a][1]
        
        if total != 5*48*60:
            print(f'{a} {"Team":>22}',timedelta(seconds =total),scoreErrors)
            for key,b in starttime_duration_bydate[a][0].items():
                for c in starttime_duration_bydate[a][0][key]:
                    print(f'{key:<20} {str(c[0]):<20} {str(c[2]):<20} {str(timedelta(seconds=c[1]))}')
                print()
