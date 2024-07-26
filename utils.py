import re
import os

from loguru import logger
from settings import defaults


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

def ms(sec):
    m = int(sec / 60)
    s = int(sec % 60)
    return f'{m:02d}:{s:02d}'

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

def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3

def removeLower(str): 
    regex = "[a-z .-]"
    return (re.sub(regex, "", str))

def shorten_player_name(what, max_length):
    # if name longer than max turns 'firstname lastname' to 'first_intial.lastname'
    if len(what) < max_length: return what

    if ' ' in what:
        ret_v = what[0] + '. ' + what.split(' ')[1]
        if len(ret_v) > max_length:
            return removeLower(ret_v)

        return what[0] + '. ' + what.split(' ')[1]
    return what

def get_file_names(file_directory):

    if os.path.isdir(file_directory):
        cwd = os.getcwd() + '/' + file_directory
        files = [os.path.join(cwd, f) for f in os.listdir(cwd) if os.path.isfile(os.path.join(cwd, f))]
    else:
        files = [file_directory]
    return files


def fn_root(game_data):
    t = game_data.matchup_home.split(' ')
    return f'{t[0]}v{t[2]}{game_data.game_date.replace('-','')}'

def save_files(who,directory,the_files):
    
    """ for example
    the_files = [
        ['made_by_gemini.csv', total_responce],
        ['made_by_gemini_raw.txt', total_raw_resp]
    ]
    """
    
    fn = ''
    for file in the_files:
        if file[1] != '':
            fn = os.getcwd() + '/' + directory + '/' + file[0]
            with open(fn, 'w') as content_file:
                content_file.write(file[1])
    if fn != '':
        logger.info(f'\n\n{who} is done.  Look here: {fn}\n')
    else:
        logger.debug(f'\n\n!!! {who} created no files.')
                
def save_file(who, game_data, where, data):
    
    DBG = defaults.get('DBG')
    SAVE_PRE = defaults.get('SAVE_PREFIX')
    
    cwd = os.path.join(os.getcwd(), defaults.get(where))
    
    dstr = 'DBG_' if DBG else ''
    fn = f'{SAVE_PRE}{dstr}{who}{fn_root(game_data)}.csv'
    
    fn = os.path.join(cwd, fn) 
    
    if not(os.path.exists(cwd)): os.mkdir(cwd)   
    
    logger.info(f'saving {os.path.basename(fn)}')
    
    fl_s = open(fn,"w")
    
    if type(data) == type([]): fl_s.writelines(data)
    else: fl_s.write(data)
    
    fl_s.close()
