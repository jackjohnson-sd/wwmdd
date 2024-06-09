import pathlib
import textwrap
import os

import google.generativeai as genai

MODEL = 'models/gemini-1.5-pro-latest'

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
    if os.path.isdir(file_directory):
        cwd = os.getcwd() + '/' + file_directory
        files = [os.path.join(cwd, f) for f in os.listdir(cwd) if os.path.isfile(os.path.join(cwd, f))]
    else:
        files = [file_directory]
        
    for fn in files:
        with open(fn, 'r') as content_file:
            prompt = content_file.read()
        resp = token_count(prompt)
        print(f'{resp.total_tokens:<10} tokens from {fn}')
    
def start_stream(prompt, chat):
    
    print('GEMINI:  ', end="", flush=True)

    try:      
        response = chat.send_message(prompt, stream=True)
        gemini_data = ''
        for chunk in response:
            gemini_data += chunk.text
            progress.show()
            
        print()
    except Exception as err:
        print('start_stream ERROR', err)
        return '','' 
        
    return gemini_data,response
    
# def stream_gemini(prompt,system_prompt,example_game,continue_prompt,file_directory):
def stream_gemini(prompt,
                  system_prompt,
                  example0_game,
                  example1_game,
                  example2_game,
                  example3_game,
                  continue_prompt,
                  file_directory):
            
    
    x = [example0_game,example1_game,example2_game,example3_game]
    for i,d in enumerate(x):
        
        key1 = f'<example{i}_play_by_play>'
        key2 = f'<\\example{i}_play_by_play>'
        
        s = system_prompt.find(key1) + len(key1)
        e = system_prompt.find(key2)
        
        system_prompt = system_prompt[0:s] + '\n' + d + system_prompt[e:-1]

    prompt = system_prompt
    err_count = 0
    cnt = 0
    total_responce = ''
    total_raw_resp = ''
    do_no_more = False
    doit = True
    
    clnr = cleaner(13)
    hdr = ',eventmsgtype,period,pctimestring,neutraldescription,score,scoremargin,player1_name,player1_team_abbreviation,player2_name,player2_team_abbreviation,player3_name,player3_team_abbreviation'
    clnr.set_header(hdr)

    print('Using Model',MODEL)
    model = genai.GenerativeModel(MODEL)
    chat = model.start_chat(history=[])

    while doit and not do_no_more:
        
        try:
            
            gemini_responce, gemini_raw = start_stream(prompt, chat)

            if '' == gemini_responce:
                do_no_more = True 
                print('ERROR No response from gemini')
            else: 
                do_no_more = False

                cleaned_responce, good_line_cnt, dead_line_cnt, cln_error = clnr.clean_responce([prompt],gemini_responce)

                if cln_error: do_no_more = True
                else:
            
                    total_raw_resp += '\n'+ gemini_raw.text
                    total_responce += '\n'+ cleaned_responce 
                        
                    prompt = f'{system_prompt[e:-1]} {total_responce} {continue_prompt}'
                    cnt =+ 1
                    
                    # end when we see end of ENDOFPERIOD,4
                    do_no_more = clnr.are_we_done()
                    
        except Exception as err:
            print('doit ERROR',err)
            err_count += 1
            do_no_more = True

        doit = not do_no_more

    clnr.browse()
    
    if total_responce != '':
        fn = os.getcwd() + '/' + file_directory + '/' + 'made_by_gemini.csv'
        with open(fn, 'w') as content_file:
            content_file.write(total_responce)

    print(f'\n\nGEMINI is done.  Look here: {fn}\n')

    if total_raw_resp != '':
        fn = os.getcwd() + '/' + file_directory + '/' + 'raw_made_by_gemini.txt'
        with open(fn, 'w') as content_file:
            content_file.write(total_raw_resp)


def gemini_test(files,file_directory):
    prompt = None; system_prompt = None; example0_game = None; continue_prompt = None
    example1_game = None; example2_game = None; example3_game = None; continue_prompt = None
    for fn in files:
        with open(fn, 'r') as content_file:
            if 'initial_prompt' in fn: prompt = content_file.read()       
            if 'system_prompt'  in fn: system_prompt = content_file.read() 
            if 'example0_game'   in fn: example0_game = content_file.read()       
            if 'example1_game'   in fn: example1_game = content_file.read()       
            if 'example2_game'   in fn: example2_game = content_file.read()       
            if 'example3_game'   in fn: example3_game = content_file.read()       
            if 'coninue_prompt' in fn: continue_prompt = content_file.read()  


    tmp = [  prompt != None\
           , system_prompt != None\
           , example0_game != None\
           , example1_game != None\
           , example2_game != None\
           , example3_game != None\
           , continue_prompt != None
           ]

    if not all(tmp):
        names = ['initial_prompt.txt', 'system_prompt.txt', 'example0_game.csv', 'example1_game.csv', 'example2_game.csv', 'example3_game.csv', 'coninue_prompt.txt']  
        l = list(map(lambda x: x[1] if x[0] else None ,zip(tmp,names)))
        print('MISSIING FILES :', ', '.join(l))
    else:     
        stream_gemini(prompt,system_prompt,
                      example0_game,
                      example1_game,
                      example2_game,
                      example3_game,
                      continue_prompt,
                      file_directory)

def main(file_directory):
    
    import os

    if os.path.isdir(file_directory):
        cwd = os.getcwd() + '/' + file_directory
        files = [os.path.join(cwd, f) for f in os.listdir(cwd) if os.path.isfile(os.path.join(cwd, f))]
    else:
        files = [file_directory]
        
    gemini_test(files,file_directory)

    # for m in genai.list_models():
    #     if 'generateContent' in m.supported_generation_methods:
    #         print(m.name)
            
   