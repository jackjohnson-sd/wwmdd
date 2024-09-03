import os
import google.generativeai as genai
from google.generativeai import caching
import datetime
import time
import json

from loguru import logger
from utils import save_files, get_file_names,get_all_files,get_files_in_path,filter_by_extension
import utils

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
from cleaner import cleaner, progress


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

def shrink_this(text, max_line_cnt):
    lc = text.count('\n')
    if lc < max_line_cnt: return text
    
    tt = text.split('\n')
    s1 = '\n'.join(tt[0:int(max_line_cnt/2)]) 
    s2 = f'\n\n    ... {lc - max_line_cnt} removed ...\n\n'
    s3 = '\n'.join(tt[-int(max_line_cnt/2):])
    
    return s1 + s2 + s3

def get_l_parts(msg_idx,call_and_response,offset=0):
        
    line1 = call_and_response[msg_idx][offset].split(':')     
    del line1[0]
    
    call_type    = line1[0]   # model name or pyhton code name
    storage_name = line1[1]  # where in the resonce dict to store the results of this call
    l2 = ''
    if len(line1) > 2: l2 = line1[2]
    l3 = ''
    if len(line1) > 3: l3 = line1[3]
    l4 = ''
    if len(line1) > 4: l4 = line1[4]
    
    return call_type,storage_name,l2,l3,l4
        
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
    
    try:   # fails if not valid
    
        creator_config    = stuff['creator_config']
        critic_config     = stuff['critic_config']
        call_and_response = stuff['call_and_response']
        
        team1 = stuff['TEAM1']
        team2 = stuff['TEAM2']

        for i,mm in enumerate(call_and_response):
            for k,nn in enumerate(call_and_response[i]):
                oo = nn.replace('TEAM1', team1)
                call_and_response[i][k] = oo.replace('TEAM2', team2)

    except Exception as ex:
        
        logger.error(f'troubles, not our json? loading {fn} {ex}')
        return
        
    labels = {}
    
    for i,a in enumerate(call_and_response):
        if a[0][0] != ':':        
            b = a[0].split(':')
            labels[b[0]] = i

    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

    try:
        
        creator = make_model(creator_config, file_dir_name)
        
        critic = make_model(critic_config, file_dir_name)
        
    except Exception as ex:
        
        logger.error(f'loading cached files {ex}')
        return
  
    responses = {}    
    msg_idx = 0
    
    while msg_idx < len(call_and_response):
                   
        # skip section if commented out
        if '#' in call_and_response[msg_idx][0]:
            logger.info(f'skipping {call_and_response[msg_idx][0]}')
            msg_idx += 1
            continue

        # first line identifies which model gets the prompt
        call_type, storage_name,l2,l3,l4 = get_l_parts(msg_idx, call_and_response)
        
        # actual prompt starts on second line
        this_prompt = ''
        next_data = 1

        if '$$SAVE' == call_type:
            responese_s = storage_name.split(',')
            
            resp_data = ''
            for r in responese_s:
                resp_data += get_text(responses[r])
            
            fn = l2
            utils.save_file('', None, os.path.join(file_dir_name,fn), resp_data)

            msg_idx += 1
            continue
        
        if '$$READ' == call_type:

            fn = l2
            responses[storage_name] = utils.read_file(os.path.join(file_dir_name,fn))
            
            msg_idx += 1
            continue            

        if '$$JSON' == call_type:

            fn = l2
            with open(fn, "r") as f:
                new_stuff = json.load(f)
        
            responses[storage_name] = new_stuff
            msg_idx += 1
            
            continue

        if '$$IF' == call_type:
            
            max_retrys = int(l4)
            data = get_text(responses[storage_name])
              
            match l2:
                
                case '_LT_':
                    
                    threshold = int(l3)
                    result = check_if_less_than(msg_idx, data.split('\n')[0].upper(), threshold, max_retrys,'SUCCESS')
        
                    if result == 'FAILED':
                        # means are score exceeded becuase it a less than check
                        # so go one to next item
                        msg_idx +=1
                        continue
                    
                    elif result == 'SUCCESS':
                        # we are less than, do remediation in this msg follow
                        call_type, storage_name,l2,l3,l4 = get_l_parts(msg_idx,call_and_response,offset=1)
                        next_data += 1
                    
                    else: # FAILED_MAX_RETRYS
                        logger.error(f'max retrys exceeded, giving up on {call_and_response[msg_idx][0]}')
                        return
                    
                case '_NOT_YES_': 
                    # this means we should do the retry 
                    # when there is NO yes in the message
                    
                    # 'SUCCESS' means a YES was found
                    result = check_if_yes(msg_idx, data.split('\n')[0].upper(), max_retrys,'FAILED')
                    
                    if result == 'SUCCESS':
                        # _NOT_YES_ is false, do remdial action
                        msg_idx +=1
                        continue
                    
                    elif result == 'FAILED':
                        # we failed -- form retry prompt 
                        call_type, storage_name,l2,l3,l4 = get_l_parts(msg_idx,call_and_response,offset=1)          
                        next_data += 1
                    
                    else: # FAILED_MAX_RETRYS
                        logger.error(f'max retrys exceeded, giving up on {call_and_response[msg_idx][0]}')
                        return
            
        goto_idx = -1
        
        for partial in call_and_response[msg_idx][next_data:]:
            
            if '$$GOTO' in partial:
                
                b = partial.split('|')
                goto_idx = labels[b[1]]
                break
                    
            elif '$$R' in partial: 

                this_prompt += '\n' + get_text(responses[partial]) + '\n'
                
            elif '#' == partial[0]:
                logger.info(f'# skipped {partial}')
                continue
                         
            else:
                this_prompt += partial
            
        if this_prompt != '':

            logger.info(f'{call_type}.{storage_name} prompt \n{shrink_this(this_prompt,20)}')
            
            if '$$CREATOR' in call_type:        
                responses[storage_name] = creator.generate_content(this_prompt)
                
            elif '$$CRITIC' in call_type:
                responses[storage_name] = critic.generate_content(this_prompt)

            else:
                logger.error(f'invalid llm name {call_type}.{storage_name}')    
                return
        
            logger.info(f'{call_type}.{storage_name} response \n{shrink_this(get_text(responses[storage_name]),20)}')
       
        # where do we go next
        if goto_idx != -1 : msg_idx = goto_idx
        else: msg_idx += 1



def main(file_directory):
    
    start_conversation(file_directory[0])
