# mft_server_impl.py
# Ben Fisher, 2019
# Released under the GNU General Public License version 3

from mft_common import *


def parseIndexParam(params, fileState):
    if not fileState or not fileState.listOfFiles:
        raise MoltenTFException(
            'Internal error, get_file_list should have been called first'
        )
    return fileState.listOfFiles.infoAtIndexString(params, 'index')


def get_file_list(params, stateGetFile, path, isStar):
    stateGetFile.b = Bucket()
    stateGetFile.b.listOfFiles = SerializableListOfFileInfo()
    stateGetFile.b.listOfFiles.addFromSpec(path, isStar)
    response = stateGetFile.b.listOfFiles.serializeWithOnlyLeafNames()
    response = 'Molten:' + response
    return Bucket(directPath=None, response=response)


def get_file(params, stateGetFile):
    item = parseIndexParam(params, stateGetFile.b)
    showMsg(msgMed, f'  {files.getName(item.filename)}')
    return Bucket(response=None, directPath=item.filename)


def get_file_complete(params, stateGetFile):
    showMsg(msgMed, '\n\nget_file is complete :)\n\n')
    stateGetFile.b = None
    return Bucket(directPath=None, response='Molten:Success')


def send_file_list(params, stateSendFile):
    # sends files delimited by |
    # we're sending an advance notification of what the filenames should be.
    # not strictly necessary, but nice for symmetry
    fls = params.get('listOfFiles')
    if not fls:
        raise MoltenTFException('Missing parameter: listOfFiles')

    stateSendFile.b = Bucket()
    stateSendFile.b.warnings = []
    stateSendFile.b.listOfFiles = SerializableListOfFileInfo()
    stateSendFile.b.listOfFiles.deserialize(fls)
    return Bucket(directPath=None, response='Molten:Success')


def send_file(params, stateSendFile, serverRStream, headers):
    item = parseIndexParam(params, stateSendFile.b)
    checkOkDestPath(item.filename)

    dest = f'{getOurDirectory()}/files_we_got_from_guest'
    doAndCheckForFileAccessErrAndReRaise(lambda: files.makeDirs(dest), dest)
    fulldest = dest + '/' + item.filename
    if files.exists(fulldest):
        warn('Already exists: ' + fulldest + ' replace?')

    expectedLen = headers.get('content-length')
    try:
        expectedLen = int(expectedLen)
    except:
        showMsg(msgHigh, 'content-length not seen, assuming 0', expectedLen)
        expectedLen = 0
    showMsg(msgMed, f'reading data of length {formatSize(expectedLen)}')
    doAndCheckForFileAccessErrAndReRaise(
        lambda: send_file_stream_content(serverRStream, expectedLen, fulldest),
        fulldest
    )

    checksumGot = files.computeHash(fulldest, 'sha256')
    checksumExpected = item.checksum
    if checksumExpected != checksumGot:
        warning = f'{files.getName(fulldest)} wrong checksum, ' + \
            f'expected {checksumExpected} but got {checksumGot}'
        showMsg(msgHigh, warning)
        stateSendFile.b.warnings.append(warning)
    showMsg(msgMed, f'  {files.getName(fulldest)}')
    showMsg(
        msgVerbose,
        f'  checksumGot={checksumGot}|checksumExpected={checksumExpected}'
    )
    return Bucket(directPath=None, response='Molten:Success')


def send_file_stream_content(serverRStream, expectedLen, fulldest):
    with open(fulldest, 'wb') as f:
        memoryEfficientCopyFromStreamLen(serverRStream, f, expectedLen)


def send_file_complete(params, stateSendFile):
    showMsg(msgMed, '\n\nsend_file is complete :)\n\n')
    warningsOccurred = False
    if stateSendFile and stateSendFile.b and stateSendFile.b.warnings:
        warnings = stateSendFile.b.warnings
        warningsOccurred = True
        for warning in warnings:
            showMsg(msgHigh, 'WARNING: ' + warning)

    stateSendFile.b = None
    if warningsOccurred:
        response = 'Molten:' + ('\n'.join(warnings))[0:1024]
        return Bucket(directPath=None, response=response)
    else:
        return Bucket(directPath=None, response='Molten:Success')
