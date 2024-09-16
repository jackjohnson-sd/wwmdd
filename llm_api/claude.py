from cleaner import cleaner, progress
from loguru import logger

from utils import get_file_names,save_files 

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
        max_tokens  = 2000,
        temperature = 0.0,
        system      = system_prompt,
        messages=[ { "role" : "user" , "content" : prompt}]
    )

    return message.content

def stream_claude(prompt,system_prompt,assistant_prompt):
    
    the_responce = ''
    
    logger.info('CLAUDE stream START')
    try:
   
        with client.messages.stream (

            system = system_prompt,

            messages = [
                { "role": "user",       "content": prompt},
                { "role": "assistant",  "content": assistant_prompt},
            ],

            max_tokens=MAX_TOKENS,
        
            model = MODEL,
        
        ) as stream:
           
            for text in stream.text_stream:
                # if LOG == 'OFF': 
                progress.show()
                the_responce += text
        
        logger.info('CLAUDE stream END')
        
        return the_responce
    
    except Exception as err:
        logger.error(f'CLAUDE: start_stream ERROR  {err}')
        return '','' 

def ask_claude(prompt,system_prompt,example_game,continue_prompt, file_directory ):

    # 13 rows and don't duplicate the header
    clnr = cleaner(13)
    
    hdr = ',eventmsgtype,period,pctimestring,neutraldescription,score,scoremargin,player1_name,player1_team_abbreviation,player2_name,player2_team_abbreviation,player3_name,player3_team_abbreviation'
    clnr.set_header(hdr)

    do_no_more = False

    assistant_prompt = 'Hello, no responce needed.'
    
    # insert our example files
    key1 = '<example_play_by_play>'
    key2 = '<\\example_play_by_play>'
    
    s = system_prompt.find(key1) + len(key1)
    e = system_prompt.find(key2)
    
    if e == -1 :
        logger.error('\nCLAUDE ERROR NO PLACE FOR EXAMPLE FILE IN SYSTEM PROMPT ----------\n')           
        do_no_more = True
        
    system_prompt = system_prompt[0:s] + '\n' + example_game + system_prompt[e:-1]
    
    total_responce = ''
    total_raw_resp = ''

    logger.error(f'CLAUDE Model {MODEL}')
    
    while not do_no_more :
        
        # messages are state less.  
        # i.e. no memory this is it.
             
        the_responce = ''        
        
        the_responce = stream_claude(
            prompt,
            system_prompt,
            assistant_prompt
        )
        
        if '' == the_responce:
            do_no_more = True 
            logger.error('CLAUDE:ERROR No response.')
        else: 
            
            try:            
                cleaned, good_line_cnt, dead_line_cnt, cln_error = clnr.clean_responce([prompt,assistant_prompt,system_prompt],the_responce)
                if cln_error:
                    do_no_more = True
                else:
                    total_responce += '\n' + cleaned
                    total_raw_resp += '\n' + the_responce
                    
                    assistant_prompt = cleaned #'<hypothetical_play_by_play>\n' + t2 + '\n<\\hypothetical_play_by_play>' 

                    # end when we see ENDOFPERIOD,4
                    do_no_more = clnr.are_we_done()

            except Exception as err: # ABORT
                logger.error(f'CLAUDE:CLNR ERROR {err}')
                do_no_more = True
                            
            prompt = continue_prompt

    
    clnr.browse()
    
    the_files = [
        ['made_by_claude.csv', total_responce],
        ['made_by_claude_raw.txt', total_raw_resp]
    ]
    
    save_files('CLAUDE', file_directory,the_files)

def main(file_directory):

    files = get_file_names(file_directory)
    
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
        logger.error('\n ERROR -- CLAUDE file(s) missing!\n' )
        logger.error('Need initial_prompt.txt, system_prompt.txt, example_game.csv, continue_prompt.txt')

        
# anthropic-cookbook/misc/metaprompt.ipynb