from logger import log

from settings import defaults 

TRIM     = defaults.get('TRIM')       

class cleaner :
    
    good_stuff = [] 
    all_stuff = []
    prompts = []

    row_count = 0
    err_count = 0
    header    = ''
    # eventmsgtype,period,pctimestring,neutraldescription,score,scoremargin,player1_name,player1_team_abbreviation,player2_name,player2_team_abbreviation,player3_name,player3_team_abbreviation
    
    def __init__(self,row_count):
        
        self.good_stuff = []
        self.all_stuff = []
        
        self.row_count = row_count
        self.err_count = 0
        
        return   

    def browse(self):
        for i,a in enumerate(self.good_stuff):
            log(f'\n{i}- prompts         -------\n{self.trim(self.prompts[i])}')
            log(f'\n{i}- cleaned responce ------\n{self.trim(a)}')
            log(f'\n{i}- raw responce   --------\n{self.trim(self.all_stuff[i])}')
                    
    def trim(self, long_string):
        
        if TRIM == 'OFF': return long_string
        
        many_lines = long_string.split('\n')
        len_many_lines = len(many_lines)

        if len_many_lines > 20:
            long_string = ('\n').join(many_lines[0:5])
            long_string += f'\n\n\n      ....  {len_many_lines - 10} removed    .....\n\n\n'
            long_string += ('\n').join(many_lines[-5:])
            
        return long_string
    
    def set_row_count(self,new_count): self.row_count = new_count
    def set_header(self,header): self.header = header
    
    def clean_responce(self,prompt,the_responce):
        
        ps = ''
        for a,b in zip(prompt,['system','assistant','continue']):
            ps += f'{b}\n{a}\n\n'
        self.prompts += [ps]
        err_count = 0
        
        # we're assuming this is csv, comma-separated-values, data.
        # place new line at end. we get partials when we reach max tokens
        
        the_responce += '\n'
        dead_meat = []
        lines = []
    
        try:
            # blank line mildly bad
            if the_responce == '\n': 
                log('BLANK RESPONCE from model')
                err_count += 1
            else:
                
                err_count = 0
                # check line at a time 
                lines = the_responce.split('\n')
                
                # remove all  non csv lines. i.e. not lots of commas
                for i,line in enumerate(lines):
                    if len(line.split(',')) != self.row_count:
                        log(f'SHORT LINE {i} {len(line.split(","))} {line}')
                        dead_meat += [i]

                log(f'NON csv lines {len(dead_meat)} of {len(lines)}, {dead_meat}')
                
                lines = list(map(lambda i: lines[i] if i not in dead_meat else None, range(len(lines))))
                lines = list(filter(None, lines))

                if len(self.good_stuff) != 0:
                    
                    # if header delete, 
                    if lines[0] == self.header: 
                          lines.pop(0)
                          
                    # check did we start with the next event period, time, event number
                    prior_responce_last_line = self.good_stuff[-1] # last entry of prior event
                    last_values_from_prior_responce = prior_responce_last_line.split('\n')
                    last_values_from_prior_responce = last_values_from_prior_responce[-1].split(',')
                    first_values_from_this_responce = lines[0].split(',')
                    
                    try:
                        first_line_number = int(first_values_from_this_responce[0])
                        last_line_number = int(last_values_from_prior_responce[0])
                    except Exception as err:
                        log(f'LINE NO. ERROR ------\n{prior_responce_last_line} \n{lines[0]}')
                        return '', len(lines), len(dead_meat), True
                        
                    delta = first_line_number - last_line_number
                    if delta != 1:
                        log(f'WARN NON CONTIG -----\n {last_values_from_prior_responce[0:3]} {first_values_from_this_responce[0:3]}')
                        if abs(delta) > 2:
                            log(f'ERROR NON CONTIGOUS RESPONCE ------\n {lines[0]}')
                            return '', len(lines), len(dead_meat), True
        
                else:
                    # first time in start with header
                    # and start of game //TODO//
                    if self.header != lines[0]:
                        log(f'RESPONCE DID NOT START WITH HEADER {lines[0]}')
                        return '', len(lines), len(dead_meat), True
                
                t2 = ('\n').join(lines)

                self.good_stuff.extend([t2])
                self.all_stuff.extend([the_responce])
                
            return  t2,len(lines),len(dead_meat),False
    
        except Exception as err:
            log(f'CLEANER error ----------\n{err}')
            return '', 0, len(dead_meat), True

    def are_we_done(self):
        n = self.good_stuff[-1].find('ENDOFPERIOD')
        if n != -1:
            nx = self.good_stuff[-1][n + len('ENDOFPERIOD') :]
            period = nx[1]
            log(f'end of period {period}') 
            if period >= '4':
                log('End of game?')
                return True    
        return False
    
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