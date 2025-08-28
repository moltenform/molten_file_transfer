# mft_impl_receive.py
# Ben Fisher, 2019
# Released under the GNU General Public License version 3

import requests
import time
from mft_common import *


def goClientReceive(cxnParams):
    # step 1: ask the server what files are there
    showMsg(msgMed, 'asking the server what files are there...')
    res, resText = sendGetAndCheckSuccess(cxnParams, '/get_file_list')
    listNames = resText
    assertTrue(len(listNames) > 0, 'listNames is empty?')
    listOfFiles = SerializableListOfFileInfo()
    listOfFiles.deserialize(listNames)

    if not listOfFiles or not listOfFiles.len():
        trace('server is not serving any files')
        return

    # step 2: get files from the server
    for i in range(listOfFiles.len()):
        item = listOfFiles.infoAtIndex(i)
        showMsg(msgMed, f'receiving file {i+1} of {listOfFiles.len()}...')
        getParams = {}
        getParams['index'] = str(i)
        res, resText = sendGetAndCheckSuccess(
            cxnParams, '/get_file', getParams, stream=True, timeout=None
        )
        fulldest = checkWriteFile(item.filename)

        doAndCheckForFileAccessErrAndReRaise(
            lambda: doWriteToFile(res, fulldest), fulldest
        )

        checksumGot = files.computeHash(fulldest, 'sha256')
        checksumExpected = item.checksum
        showMsg(msgMed, f'  {files.getName(fulldest)}')
        showMsg(
            msgVerbose,
            f'  checksumGot={checksumGot}|checksumExpected={checksumExpected}'
        )
        if checksumExpected != checksumGot:
            warning = f'{files.getName(fulldest)} wrong checksum, ' + \
                f'expected {checksumExpected} but got {checksumGot}'
            warn(warning)

    # step 3: tell server we are done
    showMsg(msgMed, 'tell server we are done...')
    res, resText = sendGetAndCheckSuccess(cxnParams, '/get_file_complete')
    assertTrueMolten(
        resText == 'Success', 'Server did not return expected response', resText
    )

    getPressEnterToContinue('Complete')


def doWriteToFile(res, fulldest):
    totalGot = 0
    with open(fulldest, 'wb') as f:
        for chunk in res.iter_content(
            chunk_size=memBufferSize, decode_unicode=False
        ):
            totalGot += len(chunk)
            showMsg(msgMed, f'received {formatSize(totalGot)}')
            f.write(chunk)


def checkWriteFile(itemPath):
    checkOkDestPath(itemPath)
    dest = f'{getOurDirectory()}/files_we_got_from_host/{itemPath}'
    parent = files.getParent(dest)
    doAndCheckForFileAccessErrAndReRaise(lambda: files.makeDirs(parent), parent)
    if files.exists(dest):
        warn('Already exists: ' + dest + ' replace?')

    return dest


def sendGetAndCheckSuccess(
    cxnParams, suburl, getParams=None, stream=False, timeout=10
):
    time.sleep(1)
    url, urlpart = createServerUrlString(cxnParams, suburl, getParams)
    showMsg(msgInfo, '---------------', urlpart)
    res = requests.get(url, stream=stream, timeout=timeout)
    resText = '' if stream else res.text.strip()

    if res.status_code != 200:
        trace(f'Error: returned code {res.status_code}')
        trace(resText)
        raise MoltenTFException('Got a message from server.')

    if not stream:
        res.encoding = 'utf=8'
        resText = expectResponseStartsWithCorrectPrefix(resText)
    return res, resText
