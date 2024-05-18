from datetime import datetime,timedelta


def dump_play_by_play(players,pbp):

    if players == []:
       players =  list(set(pbp.player1_name) | set(pbp.player2_name))

    for player in players:
        subs = pbp.query(
            f'(player1_name == "{player}" or player2_name == "{player}")'
            )
        if subs.shape[0] > 0:
            print()
            print(player,' -----------------')
            for key,e in subs.iterrows():
                p1 = '' if type(e.player1_name) == type(None) else e.player1_name
                p2 = '' if type(e.player2_name) == type(None) else e.player2_name
                desc = '' if type(e.homedescription) == type(None) else e.homedescription    
                if desc == '':  desc = '' if type(e.visitordescription) == type(None) else e.visitordescription
                if desc == '':  desc = '' if type(e.neutraldescription) == type(None) else e.neutraldescription
                print(
                    f'{e.period} {e.pctimestring:<5} {e.eventmsgtype} {p1:<20} {p2:<20} {desc}'
                )

def totalTeamMinutes(starttime_duration_bydate, date):
    total = 0
    for key, b in starttime_duration_bydate[date][0].items():
        tmin = sum(list(map(lambda x:x[1],b)))
        total += tmin
    return total
 
def period_clock_seconds(pc):
    _period = int(pc[0])
    _minsec = pc[1].split(':')
    _secs =  (_period * 720) - (int(_minsec[0]) * 60) - int(_minsec[1])
    return _secs


    _period = int(pc[1]) - 1
    _clock = datetime.strptime(pc[2], '%M:%S') 
    delta = datetime.strptime('12:00', '%M:%S') - _clock + timedelta(seconds = _period * 12 * 60)
    return int(delta.total_seconds())

def dump(df,keepers):
    for i in df.index:
        ts = ''
        for col in keepers:
            t =  df[col].loc[i:i].values[0]
            if t != None :
                ts += f'{t} '
        print(ts)
