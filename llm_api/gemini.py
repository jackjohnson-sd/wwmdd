import os
from logger import log,logd,loge,LOG
from utils import save_files,get_file_names

import google.generativeai as genai

MODEL = 'models/gemini-1.5-flash-latest'

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
from cleaner import cleaner,progress

def token_count(source):
    model = genai.GenerativeModel(MODEL)
    return model.count_tokens(source)

def do_tokens(file_directory):
    
    files = get_file_names(file_directory)    
            
    for fn in files:
        with open(fn, 'r') as content_file:
            prompt = content_file.read()
        resp = token_count(prompt)
        log(f'{resp.total_tokens:<10} tokens from {fn}')
    
def start_stream(prompt, chat):
    
    if LOG == 'OFF': print('GEMINI?  ', end='', flush=True)
    else: log('GEMINI stream START')
    
    try:      
        response = chat.send_message(prompt, stream=True)
        gemini_data = ''
        for chunk in response:
            gemini_data += chunk.text
            if LOG == 'OFF': progress.show()
            
        if LOG == 'OFF': print()
        else: log('GEMINI stream END')
        
    except Exception as err:
        loge(f'GEMINI: start_stream ERROR  {err}')
        return '','' 
        
    return gemini_data,response
    
def gemini_stream(prompt,
                  system_prompt,
                  example_game0,
                  example_game1,
                  example_game2,
                  example_game3,
                  continue_prompt,
                  file_directory):
            
    
    x = [example_game0,example_game1,example_game2,example_game3]
    for i,d in enumerate(x):
        
        key1 = f'<example_play_by_play{i}>'
        key2 = f'<\\example_play_by_play{i}>'
        
        s = system_prompt.find(key1) + len(key1)
        e = system_prompt.find(key2)
        
        system_prompt = system_prompt[0:s] + '\n' + d + system_prompt[e:-1]

    prompt = system_prompt


    total_responce = ''
    total_raw_resp = ''
    
    clnr = cleaner(13)
    hdr = ',eventmsgtype,period,pctimestring,neutraldescription,score,scoremargin,player1_name,player1_team_abbreviation,player2_name,player2_team_abbreviation,player3_name,player3_team_abbreviation'
    clnr.set_header(hdr)

    log(f'GEMINI Model {MODEL}')
    model = genai.GenerativeModel(MODEL)
    chat = model.start_chat(history=[])

    do_no_more = False

    while not do_no_more:
        
        try:
            
            gemini_responce, gemini_raw = start_stream(prompt, chat)

            if '' == gemini_responce:
                do_no_more = True 
                log('GEMINI:ERROR No response.')
            else: 

                cleaned_responce, good_line_cnt, dead_line_cnt, cln_error = clnr.clean_responce([prompt],gemini_responce)

                if cln_error: do_no_more = True
                else:
            
                    total_raw_resp += '\n'+ gemini_raw.text
                    total_responce += '\n'+ cleaned_responce 
                        
                    prompt = f'{system_prompt[e:-1]} {total_responce} {continue_prompt}'
                    
                    # end when we see end of ENDOFPERIOD,4
                    do_no_more = clnr.are_we_done()
                    
        except Exception as err:
            loge(f'GEMINI:doit ERROR {err}')
            do_no_more = True

    clnr.browse()
    
    the_files = [
        ['made_by_gemini.csv', total_responce],
        ['made_by_gemini_raw.txt', total_raw_resp]
    ]
    
    save_files('GEMINI',file_directory,the_files)
           
def main(file_directory):
    
    files = get_file_names(file_directory)    
    
    prompt_initial = None; prompt_system = None; prompt_continue = None
    example_game0 = None; example_game1 = None; example_game2 = None; example_game3 = None; 
    
    for fn in files:
        with open(fn, 'r') as content_file:
            if 'prompt_initial' in fn: prompt_initial = content_file.read()       
            if 'prompt_system'  in fn: prompt_system = content_file.read() 
            if 'example_game0'  in fn: example_game0 = content_file.read()       
            if 'example_game1'  in fn: example_game1 = content_file.read()       
            if 'example_game2'  in fn: example_game2 = content_file.read()       
            if 'example_game3'  in fn: example_game3 = content_file.read()       
            if 'prompt_coninue' in fn: prompt_continue = content_file.read()  


    tmp = [  prompt_initial != None\
           , prompt_system != None\
           , example_game0 != None\
           , example_game1 != None\
           , example_game2!= None\
           , example_game3!= None\
           , prompt_continue != None
           ]

    if not all(tmp):
        names = ['prompt_initial.txt', 'prompt_system.txt', 'example_game0.csv', 'example_game1.csv', 'example_game2.csv', 'example_game3.csv', 'prompt_coninue.txt']  
        l = list(map(lambda x: x[1] if x[0] else None ,zip(tmp,names)))
        loge(f'GEMINI MISSIING FILES :  {",".join(l)}')
    else:     
        gemini_stream(prompt_initial,prompt_system,
                      example_game0,
                      example_game1,
                      example_game2,
                      example_game3,
                      prompt_continue,
                      file_directory)

            
   