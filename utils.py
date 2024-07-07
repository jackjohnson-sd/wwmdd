def period(sec) : return int(sec / 720) + 1

def period_time_to_sec(period,mmss): 
    # period 1:4, mmss 1:23 1 minute 23 seconds left in period
    _period = int(period)
    _minsec = mmss.split(':')
    _secs =  (_period * 720) - (int(_minsec[0]) * 60) - int(_minsec[1])
    return _secs

def sec_to_period_time(sec):

    p = int(sec / 720)
    
    remaining_secs = int(sec) - p * 720
    remaining_minutes = int(remaining_secs / 60)
    remaining_secs = int(sec - p * 720 - remaining_minutes * 60)  

    if remaining_secs == 0:# and remaining_minutes == 0:
        remaining_secs = 60
    else:
        remaining_minutes += 1
        
    remaining_secs = 60 - remaining_secs
    remaining_minutes = 12 - remaining_minutes
    
    return f'{p+1} {remaining_minutes}:{remaining_secs:02d}'

def sec_to_period_time2(sec):

    p = int(sec / 720)
    
    remaining_secs = int(sec) - p * 720
    remaining_minutes = int(remaining_secs / 60)
    remaining_secs = int(sec - p * 720 - remaining_minutes * 60)  

    if remaining_secs == 0: remaining_secs = 60
    else: remaining_minutes += 1
        
    remaining_secs = 60 - remaining_secs
    remaining_minutes = 12 - remaining_minutes
    
    return f'{p+1}:{remaining_minutes:02d}:{remaining_secs:02d}'

def ms(_sec):  # p eriod m inute s econd
    
    m_into_q = int(_sec / 60)
    s_into_m = int(_sec % 60)
    s = f'{int(m_into_q):02d}:{int(s_into_m):02d}'
    return s

def _ms(_sec) : return pms(_sec).replace(' ',',')[1:]
        
def pms(_sec):  # p eriod m inute s econd
    
    q        = int(_sec / 720) + 1
    s_into_q = int(_sec % 720)
    m_into_q = s_into_q / 60
    s_into_m = int(s_into_q % 60)
    if s_into_m == 0: s_into_m = 60
    if m_into_q == 0 and s_into_m == 60:
        m_into_q = 12
        q -= 1
    s = f'{q},{int(12-m_into_q)}:{int(60-s_into_m):02d}'
    return s

def ms(sec):
    m = int(sec / 60)
    s = int(sec % 60)
    return f'{m:02d}:{s:02d}'

def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3
