import os
from cleaner import cleaner, progress

import anthropic

client = anthropic.Anthropic()

# defaults to os.environ.get("ANTHROPIC_API_KEY")
# https://docs.anthropic.com/en/docs/quickstart-guide#step-3-optional-set-up-your-api-key

haiku = 'claude-3-haiku-20240307'
sonnet	= 'claude-3-sonnet-20240229'
opus   = 'claude-3-opus-20240229'

MODEL = sonnet
MAX_TOKENS = 2000

def to_claude(system_prompt='', prompt = ''):
    
    message = client.messages.create(
        model       = "claude-3-opus-20240229",
        max_tokens  = 1000,
        temperature = 0.0,
        system      = system_prompt,
        messages=[ { "role" : "user" , "content" : prompt}]
    )

    return message.content

def stream_claude(prompt,system_prompt,assistant_prompt):
    
    the_responce = ''
    try:
        print('CLAUDE: ', end="", flush=True)
 
        with client.messages.stream(

        system = system_prompt,

        messages = [
            { "role": "user",       "content": prompt},
            { "role": "assistant",  "content": assistant_prompt},
        ],

        max_tokens=MAX_TOKENS,
        model = MODEL,
        ) as stream:
            for text in stream.text_stream:
                progress.show()
                # print('.', end="", flush=True)
                the_responce += text

        print()
        
        return the_responce
    
    except Exception as err:
        print('\nCLAUDE STREAM ERROR ----------\n',err)
        return ''


def ask_claude(prompt,system_prompt,example_game,continue_prompt, file_directory ):

    clnr = cleaner(13)
    hdr = ',eventmsgtype,period,pctimestring,neutraldescription,score,scoremargin,player1_name,player1_team_abbreviation,player2_name,player2_team_abbreviation,player3_name,player3_team_abbreviation'
    
    clnr.set_header(hdr)

    doit = True
    err_count = 0

    cnt = 0
    total_responce = ''
    total_raw_resp = ''

    assistant_prompt = 'Hello, no responce needed.'
    
    key1 = '<example_play_by_play>'
    key2 = '<\\example_play_by_play>'
    
    s = system_prompt.find(key1) + len(key1)
    e = system_prompt.find(key2)
    system_prompt = system_prompt[0:s] + '\n' + example_game + system_prompt[e:-1]
    
    # print(f'\n{0}------system prompt --- \n{system_prompt} \n')
    
    while doit :
        
        # messages are state less.  
        # i.e. no memory this is it.
         
        # system prompt is the this is our format
        # this is the events, here is a sample game
        
        # prompt is give me play by play from this game
        # and continue from from from where it left off
        
        # print(f'\n{cnt}------prompt --- \n{prompt} \n')
        # print(f'\n{cnt}------assistant ---\n {assistant_prompt} \n')
        the_responce = ''        
        do_no_more = False
        
        the_responce = stream_claude(
            prompt,
            system_prompt,
            assistant_prompt
        )
        
        if the_responce == '':  
            print('\nGEMININI NO RESP ERROR ----------\n')           
            do_no_more = True
        else:   
            
            try:            
                cleaned, good_line_cnt, dead_line_cnt, cln_error = clnr.clean_responce([prompt,assistant_prompt,system_prompt],the_responce)
                if cln_error:
                    do_no_more = True
                else:
                    total_responce += '\n' + cleaned
                    assistant_prompt = cleaned #'<hypothetical_play_by_play>\n' + t2 + '\n<\\hypothetical_play_by_play>' 

                    # end when we see ENDOFPERIOD,4
                    do_no_more = clnr.are_we_done()

            except Exception as err: # ABORT
                print('\nCLNR ERROR ----------\n',err)           
                do_no_more = True 
                            
            prompt = continue_prompt
            cnt =+ 1

        doit = not do_no_more
    
    clnr.browse()
    
    fn = os.getcwd() + '/' + file_directory + '/' + 'made_by_claude.csv'
    with open(fn, 'w') as content_file:
        content_file.write(total_responce)

    fn = os.getcwd() + '/' + file_directory + '/' + 'raw_made_by_claude.txt'
    with open(fn, 'w') as content_file:
        content_file.write(total_raw_resp)

    print(f'\n\nCLAUDE is done.  Look here: {fn}\n')

def claude_get_files(files,file_directory):
    
    prompt = None; system_prompt = None; example_game = None; continue_prompt = None
    for fn in files:
        with open(fn, 'r') as content_file:
            if 'initial_prompt' in fn: prompt = content_file.read()       
            if 'system_prompt'  in fn: system_prompt = content_file.read() 
            if 'example_game'   in fn: example_game = content_file.read()       
            if 'coninue_prompt' in fn: continue_prompt = content_file.read()  
    
    tmp = [prompt == None, system_prompt == None, example_game == None, continue_prompt == None]
    if not any(tmp):    
        
        ask_claude(prompt,system_prompt,example_game,continue_prompt,file_directory)
    else:
        print('\n ERROR -- CLAUDE file(s) missing!\n' )
        print('Need initial_prompt.txt, system_prompt.txt, example_game.csv, continue_prompt.txt')

def main(file_directory):

    import os

    if os.path.isdir(file_directory):
        cwd = os.getcwd() + '/' + file_directory
        files = [os.path.join(cwd, f) for f in os.listdir(cwd) if os.path.isfile(os.path.join(cwd, f))]
    else:
        files = [file_directory]
        
    claude_get_files(files,file_directory)

# anthropic-cookbook/misc/metaprompt.ipynb