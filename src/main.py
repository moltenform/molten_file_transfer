# main.py
# Ben Fisher, 2019
# Released under the GNU General Public License version 3

import sys
from mft_common import *
from mft_server_top import *
import mft_impl_send
import mft_impl_receive

# the 'requests' module is a dependency
# for running a 'client', not a 'server'

def main():
    msg = '''\nWelcome to molten_file_transfer.\n''' \
        '''Ben Fisher, 2019.\n''' \
        '''https://github.com/moltenform/molten_file_transfer''' \
        '''\n(For virtual machines, I recommend\n to 'start a server' ''' \
        '''on the host machine \nand 'connect to server' in the vm)\n\n'''
    
    while True:
        trace(msg)
        choices = [
            'Start a mft server and send files',
            'Start a mft server and receive files',
            'Connect to a mft server and send files',
            'Connect to a mft server and receive files',
        ]

        chosen = getInputFromChoices('', choices, cancelString='0) Exit')
        caught = None
        chosen = chosen[0]
        trace('')
        if chosen == 0:
            ret, caught = doAndCatchMftException(initStartServerSend)
        elif chosen == 1:
            ret, caught = doAndCatchMftException(initStartServerReceive)
        elif chosen == 2:
            ret, caught = doAndCatchMftException(initClientSend)
        elif chosen == 3:
            ret, caught = doAndCatchMftException(initClientReceive)
        else:
            return
        if caught:
            if isinstance(caught, KeyboardInterrupt):
                sys.exit(0)
            elif isinstance(caught, MoltenTFException):
                trace(str(caught))
                getPressEnterToContinue('')
            else:
                if debugMode():
                    raise caught
                else:
                    trace('Uncaught exception.')
                    trace(str(caught))
                    sys.exit(1)

def initStartServerSend():
    trace('Which file(s) should we host on the server?')
    isStar, path = getUserTypedFilesOrThrow()
    listOfFiles = SerializableListOfFileInfo()
    listOfFiles.addFromSpec(path, isStar)
    if not listOfFiles.len():
        raise MoltenTFException('No files found at this location')
    goStartServer(isStar, path)

def initStartServerReceive():
    goStartServer('listen', 'listen')

def initClientSend():
    cxnParams = goClientConnectOrThrow()
    trace('Which file(s) should we send to the server?')
    isStar, path = getUserTypedFilesOrThrow()
    mft_impl_send.goClientSend(cxnParams, isStar, path)
    
def initClientReceive():
    cxnParams = goClientConnectOrThrow()
    getPressEnterToContinue('Start receiving files from the server?')
    mft_impl_receive.goClientReceive(cxnParams)

def getUserTypedFilesOrThrow():
    example = 'C:\\MyFiles\\* or C:\\MyFiles\\*.jpg' if sys.platform == 'win32' \
        else '/home/me/myfiles/* or /home/me/myfiles/*.jpg'
    
    if useHardcodedFilesToSend:
        trace('using this path,', useHardcodedFilesToSend)
        typed = useHardcodedFilesToSend
    else:
        typed = getStrInput('Please enter the path of a file or ' +
            'directory \nFor example, you could type ' + example + '\n')
    
    isStar, path = parseWildcardExpr(typed)
    return isStar, path

def parseWildcardExpr(s):
    tooComplex = 'We currently only support simple wildcards ' + \
        'like *.jpg or *'
    parts = s.split('*')
    if len(parts) <= 1:
        if files.isdir(s):
            raise MoltenTFException('To send all files in a directory, ' +
                'type something like "/home/myfiles/*"')
        if not files.exists(s):
            raise MoltenTFException('file does not exist: ' + s)
        return False, s
    if len(parts) >= 3:
        raise MoltenTFException(tooComplex)
    
    return True, s

def goClientConnectOrThrow():
    cxnParams = Bucket()
    if useHardcodedServerAddress:
        cxnParams.ip = useHardcodedServerAddress
    else:
        cxnParams.ip = getStrInput("What is the IP address for the server?\n")
    
    if useHardcodedToken:
        cxnParams.token = useHardcodedToken
    else:
        cxnParams.token = getStrInput("What is the token for the server?\n")
        
    # verify that the connection works
    trace('Attempting to connect...')
    url, urlpart = createServerUrlString(cxnParams, suburl='/ping')
    trace(url)
    import requests
    res = requests.get(url, timeout=10)
    if res.text.strip() == 'Molten:Success':
        trace('Successfully connected.')
        return cxnParams
    else:
        msg = f'Could not connect. Status={res.status_code}, ' + \
            f'Details={res.text.strip()}'
        raise MoltenTFException(msg)


if __name__ == '__main__':
    main()
