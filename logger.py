import logging

from settings import defaults 

LOG     = defaults.get('LOG')      
CON     = defaults.get('CONSOLE')       

if LOG == 'ON':
    logging.basicConfig(filename='wwmdd.log',
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)
    _log = logging.getLogger("wwmdd")

def log(txt):
    if LOG == 'ON': _log.info(txt)
    if CON == 'ON': print(txt)   

def logd(txt):
    if LOG == 'ON': _log.debug(txt)
    if CON == 'ON': print(txt)   

def loge(txt):
    if LOG == 'ON': _log.error(txt)
    if CON == 'ON': print(txt)   
