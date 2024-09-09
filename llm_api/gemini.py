import os
import google.generativeai as genai
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

from google.generativeai import caching
import datetime
import time
import json
from collections import namedtuple


from loguru import logger

from utils import get_file_names,filter_by_extension,shrink_this
import utils

_parts = namedtuple('_parts','CMD,L1,L2,L3,L4,L5,L6')


MODEL = "models/gemini-1.5-flash-latest"

"""
    models/gemini-1.0-pro
    models/gemini-1.0-pro-001
    models/gemini-1.0-pro-latest
    models/gemini-1.0-pro-vision-latest
    models/gemini-1.5-flash
    models/gemini-1.5-flash-001
    models/gemini-1.5-flash-latest
    models/gemini-1.5-pro
    models/gemini-1.5-pro-001
    models/gemini-1.5-pro-latest
    models/gemini-pro
    models/gemini-pro-vision
"""

def token_count(source):
    model = genai.GenerativeModel(MODEL)
    return model.count_tokens(source)

def do_tokens(file_directory):

    files = get_file_names(file_directory)

    for fn in files:
        with open(fn, "r") as content_file:
            prompt = content_file.read()
        resp = token_count(prompt)
        logger.info(f"{resp.total_tokens:<10} tokens from {fn}")


def make_model(config, file_path):

    cached_name     = config['name']
    file_dir_name   = os.path.join(file_path,config['cached_dir'])
    cache_ttl       = config['ttl']
    llm_model       = config['model']
    system_prompt   = config['system_prompt']
     
    
    cached_files = []

    if os.path.isdir(file_dir_name):
        try:
            cwd = os.path.join(os.getcwd(), file_dir_name)
            # files = time_sorted(cwd,file_dir_name)
            files = [
                os.path.join(cwd, f)
                for f in os.listdir(cwd)
                if os.path.isfile(os.path.join(cwd, f))
            ]
        except:
            logger.error("sorted file error")
    else:
        cached_name = [file_dir_name]

    if len(files) == 0:
        logger.debug(f"{cached_name} NO files found ... {file_dir_name}")

    else:
        logger.info(f'{cached_name} model {llm_model}, {file_dir_name} {len(files)} files.')

        for filename in files:

            if not (os.path.isfile(filename)):
                logger.error(f"file {filename} fails isfile . Skipped.")
                continue

            cached_file = genai.upload_file(path=filename)

            # Wait for the file to finish process
            while cached_file.state.name == "PROCESSING":
                logger.info("Waiting for cached file to be processed.")
                time.sleep(2)

            cached_files.extend([genai.get_file(cached_file.name)])

    if len(cached_files) == 0:
        logger.error(f"no cached_files in {file_dir_name}")
        return None

    cache = caching.CachedContent.create(
        model= llm_model,
        display_name = cached_name,  # used to identify the cache
        system_instruction = system_prompt,
        contents = cached_files,
        ttl = datetime.timedelta(minutes=cache_ttl),
    )

    # mak model the uses created cache.
    model = genai.GenerativeModel.from_cached_content(cached_content=cache)
    
    return model
        
trys = {}

def check_retry(ret_val, idx, max_trys, retry_val):
                
    if idx not in trys.keys(): trys[idx] = 0

    if ret_val != retry_val: trys[idx] = 0    
    else:
        trys[idx] += 1
        if trys[idx] > max_trys: 
            ret_val = 'FAILED_MAX_TRYS' 
        
    return ret_val
    
def check_if_yes(idx, data, max_trys, retry_on):
    
    ret_val = 'SUCCESS' if 'YES' in data else 'FAILED'
            
    return check_retry(ret_val, idx, max_trys, retry_on)

def check_if_less_than(idx, data, threshold, max_trys, retry_on):
    
    n = data.find('OF 10')

    if n == -1: ret_val = 'FAILED'
    else:
        
        the_answer = data[0:n]
        # extract numbers prior to 'OF 10'
        score = [int(s) for s in the_answer.split() if s.isdigit()]        

        if len(score) != 1: ret_val = 'FAILED'
        else:
            ret_val =\
            'SUCCESS' if score[0] <= threshold else 'FAILED'

    return check_retry(ret_val, idx, max_trys,retry_on)

def get_text(the_response):
    # we store the reponse from the AI or text from python code
    # so figure out which this is
    return the_response if type(the_response) == type('aa') else the_response.text    
    
def get_labels(script,key_words):
   
    labels = {}
    for i,a in enumerate(script):
        b = a.strip().split(' ')
        if b[0].isupper():
            if b[0] not in key_words:
                if script[i+1].strip().split(' ')[0] in key_words:
                    labels[b[0]] = i
    return labels


def start_conversation(file_dir_name):

    try:
        files = filter_by_extension(file_dir_name,'.json')
        
        if len(files) != 1:
            logger.error(f' more than one .json file here. {file_dir_name} (for now)')
            return
        
        fn = os.path.join(file_dir_name,files[0])    
        
        with open(fn, "r") as f:
            stuff = json.load(f)
            
    except Exception as ex:
        
        logger.error(f'troubles loading {fn} {ex}')
        return
    
    try:   # fails if not valid json file
    
        # creator_config    = stuff['creator_config']
        # critic_config     = stuff['critic_config']
        script = stuff['script']
        
        team1 = stuff['TEAM1']
        team2 = stuff['TEAM2']

        fn = stuff['script']
        fn = os.path.join(file_dir_name,fn)
        with open(fn, "r") as f:
            script = f.readlines()

        for i,nn in enumerate(script):
            script[i] = nn.replace('TEAM1', team1).replace('TEAM2', team2)

    except Exception as ex:

        logger.error(f'troubles, not our json? loading {fn} {ex}')
        return
        
    key_words = {
        
        'READ'   : [ 1,3,],     # READ FN AS STORAGE_NAME
        'SAVE'   : [ 1,3,],     # SAVE STORAGE_NAME AS FN
        'COPY'   : [ 1,3,],     # COPY STORAGE1 STORAGE2
        'INSERT' : [ 1,0,],     # INSERT STORAGE_NAME
        'QUIT'   : [ 0,0,],     # QUIT
        'RETURN' : [ 0,0,],     # RETURN
        'GOTO'   : [ 1,0,],     # GOTO LABEL
        'IMPORT' : [ 1,2,],     # IMPORT CODE_FN STORAGE_NAME
        'CALL'   : [ 1,0,],     # CALL STORAGE_NAME.LABEL,  CALL LABEL
        'IF'     : [ 1,4,],     # IF q1 LESS_THAN 6 STOP AFTER 2 TRYS
        'PROMPT' : [ 1,0,],     # PROMPT MODEL     
        'MODEL'  : [ 1,3,],     # MODEL SKILL as STORAGE_NAME    
    }

    storage = {}
            
    _prompt = None

    llm_model = None
    
    labels = get_labels(script, key_words)

    call_stack = []
    
    msg_idx = 0
    
    carry_on = True
    
    while carry_on:
        
        while msg_idx < len(script):

            goto_idx = -1
                    
            line = script[msg_idx].strip()
            logger.debug(f'{msg_idx+1} {line}')
        
            line = line.split(' ')
            while '' in line: line.remove('')
            
            if len(line) == 0:
                
                if _prompt != None: 

                    our_model = storage[llm_model] 
                    storage[f'{llm_model}.RESP'] = our_model.generate_content(_prompt).text
                                      
                    _prompt = None
                    
            else:
                
                # comments to log
                if '#' == line[0][0]:
                    logger.info(f'-{script[msg_idx].strip()}')
                    msg_idx += 1
                    continue            
                
                # if this starts with a key word
                elif line[0] in key_words: 
                    
                    while len(line) < 10: line.extend([''])
                        
                    _line = _parts(line[0], line[1], line[2], line[3], line[4],line[5],line[6])
                    
                    match _line.CMD:
                        
                        case 'READ':    # READ file_name AS storage_name

                            fn = _line.L1
                            storage_name = _line.L3
                            
                            try:
                                storage[storage_name] = utils.read_file(os.path.join(file_dir_name,fn))
                            except:
                                logger.error(f'bad file name {fn}, {msg_idx + 1} {call_and_response[msg_idx]}')
                                return
                                                   
                        case 'SAVE':    # SAVE s1 AS file_name 
                                        # SAVE s1,s2,s3 AS file_name
                                        
                            data_set = _line.L1.split(',')
                
                            _data = ''
                            
                            for r in data_set:
                                _data += get_text(storage[r])
                
                            try:
                                fn = _line.L3
                                utils.save_file('', None, os.path.join(file_dir_name,fn), _data)
                            
                            except:
                                logger.error(f'bad file name {fn}, {msg_idx} {call_and_response[msg_idx].strip()}')
                                return

                        case 'COPY':    # COPY RO to R1

                            if _line.L1 not in storage.keys():
                                logger.error(f'invalid source {_line.L1}, {msg_idx} {script[msg_idx].strip()}')
                                return
        
                            else:
                                storage[_line.L2] = storage[_line.L1]
                                msg_idx += 1
                
                        case 'INSERT':  # INSERT RO
                            if _line.L1 not in storage.keys():
                                logger.error(f'invalid source {_line.L1}, {msg_idx} {script[msg_idx]}')
                                return
        
                            _prompt += '\n' + get_text(storage[_line.L1]) + '\n' 
                        
                        case 'QUIT':    # QUIT THIS IS_NOT USED
                            logger.info(f'quit {script[msg_idx].strip()}')
                            return
                                    
                        case 'RETURN':  # RETURN THIS_ IS NOT USED ...
                            break
                        
                        case 'GOTO':    # GOTO CRITIC_3
                            
                            try :
                                goto_idx = labels[_line.L1]
                            except:
                                logger.error(f'invalid line lable {msg_idx} {script[msg_idx]}')
                                return
                                          
                        case 'CALL':    # CALL UTILS.CLEAN
                                        # CALL CALI
                                        
                            storage_name = _line.L1
                
                            global trys
                            
                            a = (script,trys,msg_idx + 1,labels)
                            call_stack.extend([a])    
                            
                            h = storage_name.split('.')
                            if len(h) == 2:
                                storage_name = h[0]
                                destination = h[1]
                            else:
                                destination = h[0]
                                storage_name = ''
                                        
                            if storage_name != '':
                                
                                script = storage[storage_name]
                                labels = get_labels(script, key_words)
                                trys = {}      
                                     
                            msg_idx = labels[destination]
                            continue

                        case 'IF':      # IF q1 LESS_THAN 6 STOP AFTER 2 TRYS
                            
                            data = get_text(storage[_line.L1])
                            
                            match _line.L2:
                                
                                case 'IN'         : pass
                                case 'NOT_IN'     : pass
                                case 'EQ'         : pass
                                case 'NOT_EQ'     : pass
                                case 'MORE_THAN'  : pass
                                case 'NO'         : pass
                                case 'NOT_NO'     : pass
                                case 'YES'        : pass
                                
                                case 'LESS_THAN'  : 
                                    
                                    max_retrys = int(line[6])
                                    threshold = int(_line.L3)
                                    result = check_if_less_than(msg_idx, data.split('\n')[0].upper(), threshold, max_retrys,'SUCCESS')
                        
                                    if result == 'FAILED':
                                        # means our score exceeded because it a less than check
                                        # skip remediation, find next blank line
                                        # if a prompt along the way add an additional skip 
                                        bcount = 1
                                        while bcount > 0: 
                                            msg_idx +=1
                                            if script[msg_idx].strip() == '':
                                                bcount -= 1
                                            elif script[msg_idx].strip()[0:6] == 'PROMPT':
                                                bcount += 1
                                                
                                        continue
                                    
                                    elif result == 'SUCCESS':
                                        # we are less than, 
                                        # do remediation as the following statements
                                        
                                        msg_idx += 1
                                    
                                    else: # FAILED_MAX_RETRYS
                                        logger.error(f'max retrys exceeded, giving up on {script[msg_idx]}')
                                        return

                                case 'NOT_YES': 
                                    # this means we should do the retry 
                                    # when there is NO yes in the message
                                    
                                    # 'SUCCESS' means a YES was found
                                    
                                    max_retrys = int(line[5])
                                    
                                    result = check_if_yes(msg_idx, data.split('\n')[0].upper(), max_retrys,'FAILED')
                                    
                                    if result == 'SUCCESS':
                                        msg_idx +=1
                                        continue
                                    
                                    elif result == 'FAILED':
                                        # we failed -- form retry prompt 
                                        next_data += 1
                                    
                                    else: # FAILED_MAX_RETRYS
                                        logger.error(f'max retrys exceeded, giving up on {script[msg_idx][0]}')
                                        return
                       
                        case 'IMPORT':  # IMPORT UTILS code/sub_convo.txt
                            
                            fn = os.path.join(file_dir_name,_line.L2)
                            with open(fn, "r") as f:
                                new_stuff = f.readlines()
                                
                            storage_name = _line.L1
                            
                            storage[storage_name] = new_stuff
                
                            for i,nn in enumerate(storage[storage_name]):
                                storage[storage_name][i] = nn.replace('TEAM1', team1).replace('TEAM2', team2)

                            new_labels = get_labels(storage[storage_name],key_words)
                
                            storage[f'{storage_name}.labels'] = new_labels
                
                            msg_idx += 1
                            continue

                        case 'PROMPT':  # PROMPT LLM_MODEL
                            _prompt = ''
                            llm_model = _line.L1
                      
                        case 'MODEL' :
                            
                            skill = _line.L1
                            name = _line.L3
                            
                            found = False
                            for x in stuff['models']:
                                if x['area_expert'] == skill:
                                    storage[name] = make_model(x, file_dir_name)
                                    found = True
                                    break
                                    
                            if not found:
                                logger.error(F'no skill {skill} in models')
                                return                     

                # if its not a line label
                elif line[0] not in labels:
                    
                    # if we're making a prompt
                    if _prompt != None:
                         
                        _prompt += script[msg_idx].strip()
                        
                    # else this can be thought of aa comments in the script 
                    
            msg_idx = goto_idx if goto_idx != -1 else msg_idx + 1

        if len(call_stack) != 0:
            script,trys,msg_idx,labels = call_stack.pop() 
        else:
            carry_on = False


def main(file_directory):
    
    start_conversation(file_directory[0])
