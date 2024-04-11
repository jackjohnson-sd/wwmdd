from datetime import datetime,timedelta

def totalTeamMinutes(starttime_duration_bydate, date):
    total = 0
    for key, b in starttime_duration_bydate[date][0].items():
        tmin = sum(list(map(lambda x:x[1],b)))
        total += tmin
    return total
 
def period_clock_seconds(pc):
    _period = int(pc[0]) - 1
    _clock = datetime.strptime(pc[1], '%M:%S') 
    return datetime.strptime('12:00', '%M:%S') - _clock + timedelta(seconds = _period * 12 * 60)

def secDiff(start,stop):        

    # flip clock time so its from the start of the period o.e starts at 00:00 vs 12:00
    # add offset for diferences in periods
    startDelta = period_clock_seconds(start[1:3])
    stopDelta  = period_clock_seconds(stop[1:3])
 
    difference = stopDelta - startDelta

    return int(difference.total_seconds())

def dump(df,keepers):
    for i in df.index:
        ts = ''
        for col in keepers:
            t =  df[col].loc[i:i].values[0]
            if t != None :
                ts += f'{t} '
        print(ts)
