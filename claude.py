import os
import anthropic

client = anthropic.Anthropic()

# defaults to os.environ.get("ANTHROPIC_API_KEY")
# https://docs.anthropic.com/en/docs/quickstart-guide#step-3-optional-set-up-your-api-key

haiku = 'claude-3-haiku-20240307'
sonnet	= 'claude-3-sonnet-20240229'
opus   = 'claude-3-opus-20240229'


def to_claude(system_prompt='', prompt = ''):
    
    message = client.messages.create(
        model       = "claude-3-opus-20240229",
        max_tokens  = 1000,
        temperature = 0.0,
        system      = system_prompt,
        messages=[ { "role" : "user" , "content" : prompt}]
    )

    return message.content


def stream_claude(prompt,system_prompt,example_game,continue_prompt, file_directory ):

    def show_progress():
        a = ['a','b','c','d','e']
        i = 0
        while True:
            print('\010', end="", flush=True) 
            print(a[i], end="", flush=True) 
            i += 1
            i = i % 5

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
    
    print(f'\n{0}------system prompt --- \n{system_prompt} \n')
    
    while doit :
        
        # messages are state less.  
        # i.e. no memory this is it.
         
        # system prompt is the this is our format
        # this is the events, here is a sample game
        
        # prompt is give me play by play from this game
        # and continue from from from where it left off
        
        print(f'\n{cnt}------prompt --- \n{prompt} \n')
        print(f'\n{cnt}------assistant ---\n {assistant_prompt} \n')
        the_responce = ''        
        do_no_more = False
        try:
            with client.messages.stream(

                system = system_prompt,

                messages = [
                    { "role": "user", "content": prompt},
                    { "role": "assistant", "content": assistant_prompt},
                ],
                
                max_tokens=4000,
                model = sonnet,
            ) as stream:
                for text in stream.text_stream:

                    print('.', end="", flush=True)
                    the_responce += text
            print()
        except Exception as err:
            print(err)
            
        try:
            the_responce += '\n'
            if the_responce == '':
                err_count += 1
                if err_count == 5: break
            else:
                err_count = 0
                total_raw_resp += the_responce
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
            total_responce += t2
            a = t[-1].split(',')
            period = a[2]
            time = a[3]
            assistant_prompt = t2 #'<hypothetical_play_by_play>\n' + t2 + '\n<\\hypothetical_play_by_play>' 
 
        except Exception as err: 
            print(err)           
            do_no_more = True 
        
        prompt = continue_prompt
        cnt =+ 1
        # end when we see end of ENDOFPERIOD,4
        doit = 'ENDOFPERIOD,4,0:00' not in the_responce or do_no_more
    
    fn = os.getcwd() + '/' + file_directory + '/' + 'made_by_claude.csv'
    with open(fn, 'w') as content_file:
        content_file.write(total_responce)

    fn = os.getcwd() + '/' + file_directory + '/' + 'raw_made_by_claude.txt'
    with open(fn, 'w') as content_file:
        content_file.write(total_raw_resp)

    print('the end look here',fn)

def claude_test(files,file_directory):
    
    prompt = None; system_prompt = None; example_game = None; continue_prompt = None
    for fn in files:
        with open(fn, 'r') as content_file:
            if 'initial_prompt' in fn: prompt = content_file.read()       
            if 'system_prompt'  in fn: system_prompt = content_file.read() 
            if 'example_game'   in fn: example_game = content_file.read()       
            if 'coninue_prompt' in fn: continue_prompt = content_file.read()  
    
    tmp = [prompt == None, system_prompt == None, example_game == None, continue_prompt == None]
    if not any(tmp):    
        
        stream_claude(prompt,system_prompt,example_game,continue_prompt,file_directory)

def main(file_directory):

    import os

    if os.path.isdir(file_directory):
        cwd = os.getcwd() + '/' + file_directory
        files = [os.path.join(cwd, f) for f in os.listdir(cwd) if os.path.isfile(os.path.join(cwd, f))]
    else:
        files = [file_directory]
        
    claude_test(files,file_directory)

# anthropic-cookbook/misc/metaprompt.ipynb