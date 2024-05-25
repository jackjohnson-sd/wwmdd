import anthropic

client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key="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"
)


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
    while doit:
        with client.messages.stream(
            system = system_prompt,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
            model = haiku,
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
                the_responce += text
                
        t = the_responce.split('\n')
        t2 = ('\n').join(t[1:-1])
        t2 += """
            this is a partial play by play for and OKC vs PHI game in Jan 2023 please complete the play by play from where it left off
        """
        prompt += '\n' + t2

        doit = 'ENDOFPERIOD,4,0:00' not in text
    
    print('the end')
def claude_test(system_prompt_file,prompt_file):
    
    with open(system_prompt_file, 'r') as content_file:
        _system_prompt = content_file.read()

    with open(prompt_file, 'r') as content_file:
        _prompt = content_file.read()
        
    stream_claude(_system_prompt,_prompt)

def main(file_directory):
    return
    import os

    if os.path.isdir(file_directory):
        cwd = os.getcwd() + '/' + file_directory
        files = [os.path.join(cwd, f) for f in os.listdir(cwd) if os.path.isfile(os.path.join(cwd, f))]
    else:
        files = [file_directory]

    claude_test(files[0],files[1])

# anthropic-cookbook/misc/metaprompt.ipynb