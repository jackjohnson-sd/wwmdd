import re
import os

from loguru import logger
from settings import defaults


import os

# what period is this
def period_from_sec(sec) :
    if sec < 2880:  return int(sec / 720) + 1
    else:           return int((sec - 2880)/300) + 5 

# at what second did this period start
def period_start_sec(sec) :
    if sec < 2880:  return sec - sec % 720
    else:
        OT = sec - 2880
        SEC_INTO_OT = OT - OT % 300
        return 2880 + SEC_INTO_OT           

# how many seconds into this period is this
def time_into_period_from_sec(sec) :
    return sec - period_start_sec(sec)
    
def ms(sec):
    m = int(sec / 60)
    s = int(sec % 60)
    return f'{m:02d}:{s:02d}'

# what second does this period start
def sec_at_start_of_period(period):
    if period < 5 : return (period - 1) * 720
    return 2880 + (period - 5) * 300

# given period and clock time i.e P1, 7:39, 
# return second of game from start

def period_time_to_sec(period, mmss): 
    # period 1:4, mmss 1:23 1 minute 23 seconds left in period
    
    period_start_sec_offset = sec_at_start_of_period(int(period))
    
    _minsec = mmss.split(':')
    
    clock_sec = 720 if int(period) < 5 else 300
    
    clock_sec -= (int(_minsec[0]) * 60) + int(_minsec[1])
    
    _secs =  period_start_sec_offset + clock_sec
    
    return _secs

def pms_as_sec(pms_str):
    # 1,5:31
    pc = pms_str.split(',')
    return period_time_to_sec(pc[0],pc[1])
    
def pms(_sec, delim1=',', delim2=':'):  # p eriod m inute s econd
    # return "1,5:31", 1,12:00, 1,11:59, 1,0:01, 2,12:
    
    if _sec < 2880:
        max_min = 12
        q_        = int(_sec / 720) 
        s_into_q  = 720 - int(_sec % 720)
        
    else:
        max_min = 5
        _sec -= 2880
        q_        = int(_sec / 300) + 4 
        s_into_q  = 300 - int(_sec % 300)
        
    m_        = int(s_into_q / 60)
    s_        = int(s_into_q % 60)
    
    # if s_ == 0 and m_ == max_min:
    #     m_ = 0
    #     q_ -= 1
        
    s = f'{q_ + 1}{delim1}{int(m_)}{delim2}{int(s_):02d}'
    return s

def sec_to_period_time(sec): return pms(sec,delim1=' ')
    
if False: 
    
    period_start_sec(2880 + 300)

    testsecs = [719,720,721,
                2879,2880,2881,
                3179,3180,3181,
                3479,3480,3481,
                3779,3780,3781,
                ]

    for i in testsecs:
        
        a = pms(i)
        b = pms_as_sec(a)
        s = period_start_sec(i)
        t = time_into_period_from_sec(i)
        print(i,a,b,s,t)

    def aa(a):
        a1 = pms_as_sec(a)
        a2 = pms(a1)
        print(a,a1,a2)
        
            
    aa('1,12:00')
    aa('1,0:00')
    aa('2,12:00')
    aa('2,0:00')
    aa('3,12:00')
    aa('4,12:00')
    aa('5,5:00')
    aa('6,5:00')
    aa('1,12:00')
    aa('1, 0:00')
    aa('2,12:00')
    aa('2, 0:00')
    aa('3,12:00')
    aa('2, 0:00')
    aa('4,12:00')
    aa('4, 0:00')
    aa('5,5:00')
    aa('5, 0:00')
    aa('6,5:00')
    aa('6, 0:00')
    print('done')

    print('done')


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
    keys = game_data.keys().tolist()
    if 'matchup_home' in keys:
        t = game_data.matchup_home.split(' ')
    else:
        t = game_data.matchup.split(' ')

    for x in ['@','vs.']: 
        while x in t: 
            t.remove(x)
    t.sort()        
    return f'{t[0]}v{t[1]}{game_data.game_date.replace('-','')}'

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
            

def make_cache_fn(game_data):
    
    cwd = os.path.join(os.getcwd(), '.wwmdd/.csvs')
    fn = f'{fn_root(game_data)}.csv'
    fn = os.path.join(cwd, fn) 
    return fn, cwd, os.path.isfile(fn)
    
def make_file_name(who, game_data, where):
    
    DBG = defaults.get('DBG')
    SAVE_PRE = defaults.get('SAVE_PREFIX')
    
    cwd = os.path.join(os.getcwd(), defaults.get(where))
    
    dstr = 'DBG_' if DBG else ''
    fn = f'{SAVE_PRE}{dstr}{who}{fn_root(game_data)}.csv'
    fn = os.path.join(cwd, fn) 
    return fn,cwd,os.path.isfile(fn)
    

def save_file(who, game_data, where, data):
    
    fn, cwd, exists = make_file_name(who, game_data, where)
        
    if not os.path.exists(cwd): os.mkdir(cwd)   
    
    logger.info(f'saving {os.path.basename(fn)}')
    
    fl_s = open(fn,"w")
    
    if type(data) == type([]): fl_s.writelines(data)
    else: fl_s.write(data)
    
    fl_s.close()

def save_subs(sub_events,game):
    if defaults.get('SAVE_SUBS_FILE'):
        f = ',eventmsgtype,period,pctimestring,neutraldescription,score,scoremargin,player1_name,player1_team_abbreviation,player2_name,player2_team_abbreviation,player3_name,player3_team_abbreviation\n,' + \
            ('\n,').join(sub_events)  

        ma = game.matchup_away.split(' @ ')
        gd = game.game_date.split('-')
        fn = f'SUBS_{ma[0]}v{ma[1]}{gd[0]}{gd[1]}{gd[2]}.csv'

        save_files(fn,'_save_and_ignore',[[fn,f]])

def time_sorted(cwd,dirpath):
    a = [s for s in os.listdir(dirpath)
         if os.path.isfile(os.path.join(dirpath, s))]
    a.sort(key=lambda s: os.path.getmtime(os.path.join(dirpath, s)))
    a = list(map(lambda x:os.path.join(cwd,x),a))
    return a
