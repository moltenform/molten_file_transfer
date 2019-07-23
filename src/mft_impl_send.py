# mft_impl_send.py
# Ben Fisher, 2019
# Released under the GNU General Public License version 3

import requests
import time
from mft_common import *

def goClientSend(cxnParams, isStar, path):
    listOfFiles = SerializableListOfFileInfo()
    listOfFiles.addFromSpec(path, isStar)
    if not listOfFiles or not listOfFiles.len():
        getPressEnterToContinue('No files found to send')
        return
    
    # step 1: tell the server what files we are copying
    showMsg(msgMed, f'about to send {listOfFiles.len()} files...')
    showMsg(msgMed, 'telling the server what files we are copying...')
    getParams = {}
    getParams['listOfFiles'] = listOfFiles.serializeWithOnlyLeafNames()
    sendPostAndCheckSuccess(cxnParams, '/send_file_list', getParams)
    
    # step 2: send files to the server
    for i in range(listOfFiles.len()):
        item = listOfFiles.infoAtIndex(i)
        showMsg(msgVerbose, f'sending file {i+1} of {listOfFiles.len()}...')
        showMsg(msgMed, f'  {files.getname(item.filename)}')
        getParams = {}
        getParams['index'] = str(i)
        with open(item.filename, 'rb') as f:
            specialPostArgs = dict(data=f)
            sendPostAndCheckSuccess(cxnParams, '/send_file', getParams,
                specialPostArgs=specialPostArgs, timeout=None)
        
    # step 3: tell server we are done
    showMsg(msgMed, 'telling the server we are done...')
    sendPostAndCheckSuccess(cxnParams, '/send_file_complete', {})
    getPressEnterToContinue('Complete')

# requests supports sending a streaming POST body,
# skipping loading it all into memory,
# that's good, but the only way to do that is to send it raw,
# sending POST with no key/value pairs.
# so we'll send the other keys and values over query params like a GET
def sendPostAndCheckSuccess(cxnParams, suburl, getParams,
        specialPostArgs=None, timeout=10):
    time.sleep(1)
    
    args = {}
    if specialPostArgs:
        args.update(specialPostArgs)
    else:
        args['data'] = None
    
    url, urlpart = createServerUrlString(cxnParams, suburl, moreGetParams=getParams)
    showMsg(msgInfo, '---------------', urlpart)
    
    args['timeout'] = timeout
    args['url'] = url
    args['headers'] = {'Content-Type': 'application/octet-stream'}
    res = requests.post(**args)
    if res.status_code != 200:
        showMsg(msgHigh, f'Error: returned code {res.status_code}')
        showMsg(msgHigh, res.text.strip())
        raise MoltenTFException('Got a message from server.')
    
    assertTrueMolten('Molten:Success' == res.text.strip(),
        'Server did not return expected response', res.text.strip())
