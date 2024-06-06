import pathlib
import textwrap
import os

import google.generativeai as genai

MODEL = 'models/gemini-1.0-pro'

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
class sp:

    p_idx = 0
    emDash = u'\u2014'
    
    a = ['|','/',emDash,'\\','|','/',emDash,'\\']
    
    def __init__(self): self.idx = 0
    
    def show(self):
        print('\010', end="", flush=True) 
        print(self.a[self.p_idx], end="", flush=True) 
        self.p_idx += 1
        self.p_idx = self.p_idx % 8

progress = sp()

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
        print(f'{resp.total_tokens} tokens from {fn}')

    
def clean_responce(the_responce):
    try:
        the_responce += '\n'
        if the_responce == '':
            err_count += 1
        else:
            err_count = 0
            t = the_responce.split('\n')

            # clean up the response
            # THROUGH OUT NON CSV 
            
            while True:
                la = t[-1].split(',')
                if len(la) != 13:
                    t.remove(t[-1])
                else:
                    break
            while True:
                la = t[0].split(',')
                if len(la) != 13:
                    t.remove(t[0])
                else:
                    break
                
        t2 = ('\n').join(t)
        return  t2
    
    except Exception as err:
        print(err)
        return ''

def start_stream(prompt):
    
    try:      
        model = genai.GenerativeModel(MODEL)
        chat = model.start_chat(history=[])
        response = chat.send_message(prompt, stream=True)
        gemini_data = ''
        for chunk in response:
            gemini_data += chunk.text
            print(chunk.text)
            # progress.show()
            
        print()
    except Exception as err:
        print('start_strean ERROR', err)
        return '','' 
        
    return gemini_data,response
    
def stream_gemini(prompt,system_prompt,example_game,continue_prompt,file_directory):
                  

    key1 = '<example_play_by_play>'
    key2 = '<\\example_play_by_play>'
    
    s = system_prompt.find(key1) + len(key1)
    e = system_prompt.find(key2)
    prompt = system_prompt[0:s] + '\n' + example_game + system_prompt[e:-1]

    err_count = 0
    cnt = 0
    total_responce = ''
    total_raw_resp = ''
    do_no_more = False
    doit = True
    
    while doit and not do_no_more:
        
        try:
            
            print(f'\n{cnt}  prompt ------  \n' + prompt)
            gemini_responce, gemini_raw = start_stream(prompt)
            if '' != gemini_responce: 
                do_no_more = False
                # print(f'\n{cnt}  gemini raw responce ------ \n' + gemini_responce)
                cleaned_responce = clean_responce(gemini_responce)
            
                total_raw_resp += '\n'+ gemini_raw.text
                total_responce += '\n' + cleaned_responce + '\n'
                    
                prompt = f'{system_prompt[0:s]} {example_game} {total_responce}  {continue_prompt}'
                cnt =+ 1
            else: 
                do_no_more = True 
                print('ERROR No response from gemini')
                
        except Exception as err:
            print('doit ERROR',err)
            err_count += 1
            do_no_more = True
    
        doit = 'ENDOFPERIOD,4,0:00' not in  cleaned_responce


    if total_responce != '':
        fn = os.getcwd() + '/' + file_directory + '/' + 'made_by_gemini.csv'
        with open(fn, 'w') as content_file:
            content_file.write(total_responce)

    if total_raw_resp != '':
        fn = os.getcwd() + '/' + file_directory + '/' + 'raw_made_by_gemini.txt'
        with open(fn, 'w') as content_file:
            content_file.write(total_raw_resp)

def gemini_test(files,file_directory):
    prompt = None; system_prompt = None; example_game = None; continue_prompt = None
    for fn in files:
        with open(fn, 'r') as content_file:
            if 'initial_prompt' in fn: prompt = content_file.read()       
            if 'system_prompt'  in fn: system_prompt = content_file.read() 
            if 'example_game'   in fn: example_game = content_file.read()       
            if 'coninue_prompt' in fn: continue_prompt = content_file.read()  
    
    tmp = [prompt != None, system_prompt != None, example_game != None, continue_prompt != None]
    if all(tmp):     
        stream_gemini(prompt,system_prompt,example_game,continue_prompt,file_directory)

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
            
   