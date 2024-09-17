import os
import datetime
import time
import json
from collections import namedtuple

from loguru import logger
import google.generativeai as genai
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
from google.generativeai import caching

import utils
from utils import get_file_names,filter_by_extension


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

def equal(a,b):     return a == b
def not_equal(a,b): return a != b
def more_than(a,b): return a > b
def less_than(a,b): return a < b
def has_this(a,b):  return a in b
def not_has_this(a,b): return not a in b

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
    'SHOW'   : [ 1,0,],      # SHOW SN [LOG]
}

cmp = {
    'IN'        :has_this,
    'NOT_IN'    :not_has_this,
    'NOT_EQUAL' :not_equal,
    'EQUAL'     :equal,
    'MORE_THAN' :more_than,
    'LESS_THAN' :less_than,
    'NO'        :has_this,
    'NOT_NO'    :not_has_this,
    'YES'       :has_this,
    'NOT_YES'   :not_has_this
}


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

def get_files_for_cache(files, file_dir_name, cache_file_spec, args):

    try:
        #     in dest directory, if so skip   
        args['FILEDIR'] = file_dir_name
        for line in cache_file_spec:
            for arg in args: line = line.replace(arg,args[arg])
            import subprocess
            import sys
            logger.info(f'{line}')
            subprocess.run(line.split(' '), stderr=sys.stderr, stdout=sys.stdout)

        return files

    except Exception as ex:
        logger.error(f' getting cache files {file_dir_name} {ex}')
        return None
    
def make_model(config, file_path, args):

    cached_name     = config['name']
    file_dir        = os.path.join(file_path,config['cached_dir'])
    cache_ttl       = config['ttl']
    llm_model       = config['model']
    system_prompt   = config['system_prompt']
    cache_file_src = config['cache_file_src']
    
    cached_files = []

    if os.path.isdir(file_dir):
        try:
            cwd = os.path.join(os.getcwd(), file_dir)
            files = [
                os.path.join(cwd, f)
                for f in os.listdir(cwd)
                if os.path.isfile(os.path.join(cwd, f))
            ]
        except:
            logger.error(" file error")
    else:
        cached_name = [file_dir]

    if len(files) == 0:
        logger.debug(f"{cached_name} NO files found ... {file_dir}")

    else:
    
        files = get_files_for_cache(files, file_dir, cache_file_src, args)
        
        if files is None:
            logger.error(f"loading cache files. {cached_name} model {llm_model}, {file_dir} ")
            return None
        
        logger.info(f'{cached_name} model {llm_model}, {file_dir} {len(files)} files.')

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
        logger.error(f"no cached_files in {file_dir}")
        return None

    try:
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
   
    except Exception as ex:
        logger.error(f'gemini model generation {ex}') 
        return None
           
trys = {}

"""
COPY    src dst     - moves storage from src to dst
READ    fn  AS  dst - moves file contents to dst
SAVE    dst fn      - moves storage to file 
INSERT  sn          - moves sn contents to prompt string

IMPORT  fn  AS  dst - moves file contents to dst, creates a FN

SHOW    sn  LOG SHRINK - show storage location 
SHOW    sn  LOG        - show storage location 
SHOW    sn  SHRINK     - show storage location
SHOW    sn             - show storage location 

QUIT                   - ends execution of script
RETURN                 - return execution to CALL-ing script
CALL    ln             - pushes application context unto stack 
GOTO    ln             - shift execution to label name


IF sn  EQUAL      val1 STOP AFTER max_trys TRYS
IF sn  NOT_EQUAL  val1 STOP AFTER max_trys TRYS

IF sn  MORE_THAN  val1 STOP AFTER max_trys TRYS
IF sn  LESS_THAN  val1 STOP AFTER max_trys TRYS

IF sn  IN         val1 STOP AFTER max_trys TRYS
IF sn  NOT_IN     val1 STOP AFTER max_trys TRYS

IF sn  NO              STOP AFTER max_trys TRYS
IF sn  NOT_NO          STOP AFTER max_trys TRYS

IF sn  YES             STOP AFTER max_trys TRYS
IF sn  NOT_YES         STOP AFTER max_trys TRYS


MODEL   skill   AS sn
PROMPT  sn             - collect lines until next blank

'IN','NOT_IN','NOT_EQUAL','EQUAL','MORE_THAN','LESS_THAN','NO','NOT_NO','YES','NOT_YES']
"""


def next_blank_line(msg_idx,script):
    
    bcount = 1
    
    while bcount > 0: 
        msg_idx +=1
        
        if msg_idx  >= len(script): 
            return msg_idx
        
        next_line = script[msg_idx].strip() 
        if next_line == '':
            bcount -= 1
        elif next_line[0:6] == 'PROMPT':
            bcount += 1
        elif next_line[0:3] == 'IF':
            bcount += 1
                                      
    return msg_idx - 1

def check_retry(ret_val, idx, max_trys, script):

    if idx not in trys.keys(): trys[idx] = 0

    if ret_val == 'SUCCESS' or ret_val:
        
        if max_trys == 0: return idx
        
        trys[idx] += 1
        if trys[idx] > max_trys: 
            logger.error(f'max retrys exceeded, giving up on {script[idx]}')
            idx = -1
    else:    
        trys[idx] = 0
        idx = next_blank_line(idx,script)    
                
    return idx

def get_score(data):
    try :
        
        d = data.split('\n')[0].upper()
        n = d.find('OF 10')

        if n == -1: 
            if d.isnumeric(): 
                return d
            return None
            
        the_answer = d[0:n]
        # extract numbers prior to 'OF 10'
        score = [int(s) for s in the_answer.split() if s.isdigit()]        

        if len(score) != 1: return None
    except:
        logger.error(f'processing score {d}')
        return None
    
    return score[0]

def get_text(the_response):
    # we store the reponse from the AI or text from python code
    # so figure out which this is
    if isinstance(the_response,int):   return str(the_response)
    if isinstance(the_response,str):   return the_response
    
    return the_response.text.copy()   
    
def get_labels(script, key_words):
   
    labels = {}
    for i,a in enumerate(script):
        b = a.strip().split(' ')
        if b[0].isupper():
            if b[0] not in key_words:
                if script[i+1].strip().split(' ')[0] in key_words:
                    labels[b[0]] = i
    return labels

stores = {}
models = {}

def get_script(fn, key_words, stuff, file_dir_name):
    
    try:
        with open(fn, "r") as f:
            new_script = f.readlines()

        for i,nn in enumerate(new_script):
            for arg in stuff['args']:
                new_script[i] = new_script[i].replace(arg, stuff['args'][arg])
        
        l_abels = get_labels(new_script, key_words) # places to call or goto in scripts

        for lb in l_abels:
            stores[f'{lb}'] = i
                        
        if not link_check(new_script, key_words, file_dir_name, stuff):
            return None
    
        return new_script
    
    except Exception as ex:
        
        logger.error(f'troubles loading {fn} {ex}')
        return None

def link_check(script, key_words, file_dir_name, stuff):
    
    def src_check(loc,i,line):
        
        if ',' in loc:
            j = loc.split(',')
        else:
            j = [loc]
            
        for src in j:        

            if src in stores:
                return True
                  
            if '.' in src:

                k = loc.split('.')
                
                if k[0] in stores:
                    if k[1] in stores: return True
                    elif k[1] == 'RESPONSE': return True
                    else:   
                        logger.error(f'invalid storage name {k[1]}, line {i + 1}: {line}')
                        return False
                else:  
                    logger.error(f'invalid storage name {k[0]}, line {i + 1}: {line}')
                    return False
        return True       

    cmp_codes = list(cmp.keys())
    
    code_imports = []
    code_call = []
        
    for i,line in enumerate(script):
        if  line[0:6] == 'IMPORT': 
            code_imports.append(i)            
        elif line[0:4] == 'CALL': 
            code_call.append(i)
            
    for i,line in enumerate(script):
        
        line = line.strip()
        l = line.split(' ')
        while '' in l: l.remove('')

        if len(l) == 0: continue
        if  l[0][0] == '#': continue
                 
        if l[0] not in key_words:
            if l[0].isupper():
                stores[l[0]] = i
        else:
            fn = ''
            
            try:
                match l[0]:
                    
                    case 'SHOW':  # SHOW STORAGE_NAME [LOG] [SHRINK]

                        if not src_check(l[1],i,line): return False
                        
                    case 'READ':  # READ FN AS STORAGE_NAME
                        fn = l[1]
                        stores[l[3]] = i
                    
                    case 'SAVE':  # SAVE STORAGE_NAME AS FN
                        if l[1] not in stores:
                            logger.error(f'not a valid storage name {fn}, line {i + 1}: {line}')
                            return False
                        # file name is in l[3]
                        
                    case 'COPY':  # COPY STORAGE1 STORAGE2

                        stores[l[2]] = i
                        
                        if not src_check(l[1],i,line): return False
                        
                    case 'INSERT':# INSERT STORAGE_NAME
                        if not src_check(l[1],i,line): return False
                                                
                    case 'QUIT'  : pass # QUIT
                    case 'RETURN': pass # RETURN
            
                    case 'GOTO'  :# GOTO LABEL
                        if l[1] not in stores:
                            logger.error(f'not a valid storage name {fn}, line {i + 1}: {line}')
                            return False
                        
                    case 'IMPORT':# IMPORT CODE_FN AS STORAGE_NAME
                        
                        stores[l[3]] = i
                        
                        # fn_I = os.path.join(file_dir_name,l[1])
                        # new_script = get_script(fn_I, key_words, stuff, file_dir_name)
                        
                        # if new_script is None: return False
                                             
                    case 'CALL'  :# CALL STORAGE_NAME.LABEL,  CALL LABEL
                        pass
                    
                        # if not src_check(l[1],i,line): return False

                        # we should check the rest of args.  they should be in storage                        
                    case 'IF'    :# IF q1 LESS_THAN 6 STOP AFTER 2 TRYS

                        if not src_check(l[1],i,line): return False
                        
                        if l[2] not in cmp_codes:
                            logger.error(f'not valid compare code {fn}, line {i + 1}: {line}')
                            return False
                        
                    case 'PROMPT':# PROMPT MODEL
                        if l[1] not in stores:
                            logger.error(f'not a valid storage name {fn}, line {i + 1}: {line}')
                            return False
                        
                    case 'MODEL' :# MODEL SKILL AS STORAGE_NAME 
                        stores[l[3]] = i
                        models[l[3]] = i
            
            except Exception as ex:
                logger.error(f'{ex} likely missing feilds, line {i + 1}: {line}')
                return False     
                
            if fn != '':
                if not os.path.isfile(os.path.join(file_dir_name, fn)):
                    logger.error(f'not a file {fn}, line {i + 1}: {line}')
                    return False     

    for i in code_imports:
        line = script[i]
        if  line[0] == '#': continue
        
        line = line.strip()
        l = line.split(' ')
        while '' in l: l.remove('')

        if len(l) == 0: continue

        
        fn_I = os.path.join(file_dir_name, l[1])
        new_script = get_script(fn_I, key_words, stuff, file_dir_name)
        if new_script is None: return False
 
    for i in code_call:
        
        line = script[i]
        if  line[0] == '#': continue
        
        line = line.strip()
        l = line.split(' ')
        while '' in l: l.remove('')

        if len(l) == 0: continue

        if not src_check(l[1],i,line): 
            return False


    return True

def converse(file_dir_name):
    
    fn = ''
    try:
        # load the .json config file
        files = filter_by_extension(file_dir_name,'.json')
        
        if len(files) != 1:
            logger.error(f'one .json file allowed here. {file_dir_name} (for now)')
            return
        
        our_fn = os.path.join(file_dir_name,files[0])    
  
        if not os.path.isfile(our_fn):
            logger.error(f'not a file {our_fn}')
            return
        
        with open(our_fn, "r") as f:
            stuff = json.load(f)


        # load the script.txt file in this config
        fn = os.path.join(file_dir_name, stuff['script']['file_name'])   
        
        script = get_script(fn, key_words, stuff, file_dir_name)
    
        if script is None: return
    except Exception as ex:
        
        logger.error(f'troubles loading {our_fn} {fn} {ex}')
        return
            
    history = []    # every prompt to and response from and LLM
    
    # storage = {}    # labels,llm,file contents, prompt responces
            
    _prompt = None  # a string we're build to become a prompt for an LLM

    llm_model = None # the LLM we prompt to return a response
    
    call_stack = [] # place we push contex before script call 
    
    msg_idx = 0     # index into script to get line
        
    # interpret script a line at a time
    while True:
         
        while msg_idx < len(script):

            goto_idx = -1   # possible call, goto destination
                    
            line = script[msg_idx].strip()
            
            logger.debug(f'{msg_idx+1} {line}')

            line = line.split(' ')
            
            while '' in line: line.remove('')
            
            if len(line) == 0:
                
                # if prompt text collection over 
                # send PROMPT to LLM and get RESPONSE
                if _prompt != None: 

                    history.append([f'{llm_model}.PROMPT'])                     
                    history.append([_prompt])

                    our_model = stores[llm_model] 
                    stores[f'{llm_model}.RESPONSE'] = our_model.generate_content(_prompt).text

                    history.append([f'{llm_model}.RESPONSE'])
                    history.append([stores[f'{llm_model}.RESPONSE']])
                                                
                    _prompt = None
                    
            else:
                            
                # if a comment line
                if '#' == line[0][0]:
                    logger.info(f'-{script[msg_idx].strip()}')
                    msg_idx += 1
                    continue            
                
                # if this starts with a key word
                elif line[0] in key_words: 
                    
                    while len(line) < 10: line.extend([''])
                        
                    _line = _parts(line[0], line[1], line[2], line[3], line[4],line[5],line[6])
                    
                    match _line.CMD:
                        
                        case 'SHOW':    # SHOW sn [LOG] [SHRINK]
                            data = stores[_line.L1]
                            if isinstance(data, list):                           
                                data = ('').join(data)
                                
                            text = get_text(data)
                            
                            if 'SHRINK' in line:
                                text = utils.shrink_this(text,20)
                                
                            if 'LOG' in line:
                                logger.info(text)
                            else:
                                print(text)
                                
                        case 'READ':    # READ file_name AS sn

                            fn = _line.L1
                            storage_name = _line.L3
                            
                            try:
                                stores[storage_name] = utils.read_file(os.path.join(file_dir_name,fn))
                            except:
                                logger.error(f'bad file name {fn}, {msg_idx + 1} {script[msg_idx]}')
                                return
                                                    
                        case 'SAVE':    # SAVE s1 AS file_name 
                                        # SAVE s1,s2,s3 AS file_name
                                        
                            data_set = _line.L1.split(',')
                
                            _data = ''
                            
                            for r in data_set:
                                _data += get_text(stores[r])
                
                            try:
                                fn = _line.L3
                                utils.save_file('', None, os.path.join(file_dir_name,fn), _data)
                            
                            except:
                                logger.error(f'bad file name {fn}, {msg_idx} {script[msg_idx].strip()}')
                                return

                        case 'COPY':    # COPY sn to sn

                            names = _line.L1.split(',') 
                            
                            the_text = ''
                            for name in names:
                                if name in stores.keys(): 
                                    the_text += '\n' + get_text(stores[name]) + '\n'
                                else:
                                    logger.error(f'invalid source {name}, {msg_idx} {script[msg_idx].strip()}')
                                    return

                            else:
                                stores[_line.L2] = the_text
                                msg_idx += 1
                
                        case 'INSERT':  # INSERT sn
                            
                            if _line.L1 not in stores.keys():
                                logger.error(f'invalid source {_line.L1}, {msg_idx} {script[msg_idx]}')
                                return

                            _prompt += '\n' + get_text(stores[_line.L1]) + '\n' 

                        case 'IMPORT':  # IMPORT fn AS sn  # as scrupt
                            
                            import_fn = os.path.join(file_dir_name,_line.L1)                        

                            new_script = get_script(import_fn, key_words, stuff, file_dir_name)
                            
                            if new_script is None: return
      
                            storage_name = _line.L3                       
                            stores[storage_name] = new_script
                            # storag e[f'{storage_name}.labels'] = labels
                            stores[f'{storage_name}.file_path'] = import_fn
                
                            msg_idx += 1
                            continue


                        case 'QUIT':    # QUIT
                            logger.info(f'quit {script[msg_idx].strip()}')
                            return
                                    
                        case 'RETURN':  # RETURN
                            break
                        
                        case 'GOTO':    # GOTO label
                            
                            try :
                                goto_idx = stores[_line.L1]
                            except:
                                logger.error(f'invalid line lable {msg_idx} {script[msg_idx]}')
                                return
                                            
                        case 'CALL':    # CALL sn.label
                                        # CALL CALI
                                        
                            storage_name = _line.L1
                
                            global trys
                            
                            a = (script,trys,msg_idx + 1)
                            call_stack.extend([a])    
                            
                            h = storage_name.split('.')
                            if len(h) == 2:
                                storage_name = h[0]
                                destination = h[1]
                            else:
                                destination = h[0]
                                storage_name = ''
                                        
                            if storage_name != '':
                                
                                script = stores[storage_name]
                                xlabels = get_labels(script, key_words)
                                trys = {}      
                                        
                            msg_idx = stores[destination]
                            continue

                        case 'IF':      # IF sn compare [6] [STOP AFTER 2 TRYS]
                                                        
                            def xxx(msg_idx, threshold, score, evaluate, max_trys, script):
                                if type(threshold) != type(score):
                                    
                                    if isinstance(threshold,int):
                                        if score.isnumeric():
                                            score = int(score)
                                    else:
                                        if threshold.isnumeric():
                                            threshold = int(threshold)

                                ret_val = evaluate(score,threshold)
                                
                                return check_retry(ret_val, msg_idx, max_trys, script)
                            
                            data1 =\
                                _line.L1 if _line.L1 not in stores\
                                            else get_text(stores[_line.L1])
                                
                            data3 =\
                                _line.L3 if _line.L3 not in stores\
                                            else get_text(stores[_line.L3])
                            
                            match _line.L2:
                                
                                case 'IN' | 'NOT_IN': 
                                    
                                    max_retrys = 0 if _line.L6 == '' else int(_line.L6)
                                        
                                    msg_idx = xxx(msg_idx, data1, data3, cmp[_line.L2], max_retrys, script)

                                case 'NOT_EQUAL' | 'EQUAL' | 'MORE_THAN' | 'LESS_THAN':
                                                                        
                                    max_retrys = 0 if _line.L6 == '' else int(_line.L6)
                                    threshold = data3.split('\n')[0].upper()
                                    
                                    score = get_score(data1)
                                    if score == None:
                                        logger.error(f'processing score, {msg_idx}:{line}')
                                        return 
                            
                                    msg_idx = xxx(msg_idx, threshold, score, cmp[_line.L2], max_retrys, script)

                                case 'NO' | 'NOT_NO' | 'YES' | 'NOT_YES': 
                
                                    max_retrys = 0 if _line.L5 == '' else int(_line.L5)  
                                    data1 = data1.split('\n')[0].upper()
                                        
                                    msg_idx = xxx(msg_idx, data1, 'YES' if 'YES' in _line.L2 else 'NO', cmp[_line.L2], max_retrys, script)

                                case _ :
                                        
                                        logger.error(F'invalid compare skill {_line.L2} {msg_idx}:{line}')
                                        return 
                                    
                                                        
                        case 'PROMPT':  # PROMPT LLM_MODEL
                            _prompt = ''
                            llm_model = _line.L1
                        
                        case 'MODEL' :  # MODEL skill AS sn
                            
                            skill = _line.L1
                            name = _line.L3
                            
                            found = False
                            for x in stuff['models']:
                                if x['area_expert'] == skill:
                                    
                                    t = make_model(x, file_dir_name,stuff['args'])
                                    if t is None: return 
                                    
                                    stores[name] = t
                                    found = True
                                    break
                                    
                            if not found:
                                logger.error(F'no skill {skill} in models')
                                return                     

                # if its not a line label
                elif line[0] not in stores:
                    
                    # if we're making a prompt
                    if _prompt != None:
                            
                        _prompt += script[msg_idx].strip()
                        
                    # else this can be thought of aa comments in the script 
                    
            msg_idx = goto_idx if goto_idx != -1 else msg_idx + 1

        if len(call_stack) == 0: break
    
        script,trys,msg_idx = call_stack.pop() 

    # write history file        
    history_fn = our_fn.replace('.json', '.history.txt')
    fl_s = open(history_fn, 'w')
    for h in history: fl_s.write(h[0] + '\n')
    fl_s.close()
       
def main(file_directory):
    
    converse(file_directory[0])
