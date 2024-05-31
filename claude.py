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
    
def stream_claude(system_prompt, prompt ):

    doit = True
    the_responce = ''
    new_responce = ''

    print('\n\n\n  ------ system_prompt')
    print(system_prompt)
    print('\n\n')

    while doit:
        
        # messages are state less.  
        # i.e. no memory this is it.
         
        # system prompt is the this is our format
        # this is the events, here is a sample game
        
        # prompt is give me play by play from this game
        # and contine from from from where it left off
        print('\n\n\n  ------ prompt')
        print(prompt)
        print('\n')
                 
        with client.messages.stream(


            system = system_prompt,

            messages = [
                { "role": "user", "content": prompt}
            ],
            max_tokens=2000,
            model = sonnet,
        ) as stream:
            for text in stream.text_stream:
                print('.', end="", flush=True)
                the_responce += text
        print()
        
        t = the_responce.split('\n')
        # clean up the response
        # delete last partial. assumed for the moment
        # and the first which is the column headers
        t2 = ('\n').join(t[1:-1])
     
        # append to our total responess so far
        new_responce += t2
         
        prompt = \
        """
        This is a partial play by play for an OKC vs GSW game in Jan 2023
        """ + \
        new_responce + \
        """
        Please complete the play by play from where it left off.
        """
    
        # end when we see end of ENDOFPERIOD,4
        doit = 'ENDOFPERIOD,4,0:00' not in the_responce
    
    print('the end')
def claude_test(system_prompt_file,prompt_file):
    
    with open(system_prompt_file, 'r') as content_file:
        _system_prompt = content_file.read()

    with open(prompt_file, 'r') as content_file:
        _prompt = content_file.read()
        
    stream_claude(_system_prompt,_prompt)

def main(file_directory):

    import os

    if os.path.isdir(file_directory):
        cwd = os.getcwd() + '/' + file_directory
        files = [os.path.join(cwd, f) for f in os.listdir(cwd) if os.path.isfile(os.path.join(cwd, f))]
    else:
        files = [file_directory]

    claude_test(files[0],files[1])

# anthropic-cookbook/misc/metaprompt.ipynb