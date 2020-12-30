# mft_common.py
# Ben Fisher, 2019
# Released under the GNU General Public License version 3

import sys
import urllib
sys.path.append('bn_python_common.zip')
from bn_python_common import *

# use a 4mb buffer
memBufferSize = 4 * 1024 * 1024

useHardcodedServerAddress = False
useHardcodedFilesToSend = False
useHardcodedToken = False

def memoryEfficientCopyFileObject(src, dest):
    while True:
        data = src.read(memBufferSize)
        if not len(data):
            break
        dest.write(data)

def memoryEfficientCopyFromStreamLen(serverRStream, f, expectedLen):
    countBytesGot = 0
    while countBytesGot < expectedLen:
        needTotal = expectedLen - countBytesGot
        needNext = min(needTotal, 4 * 1024 * 1024)
        got = serverRStream.read(needNext)
        countBytesGot += len(got)
        f.write(got)
        showMsg(msgVerbose,
            f'got {formatSize(countBytesGot)}/{formatSize(expectedLen)}')

def getPortNumber():
    return 8123

def getOurDirectory():
    import os
    return os.path.dirname(os.path.abspath(__file__))

# the real params object returns an array,
# we'd rather go straight to the value.
class GetParamWrapper(object):
    def __init__(self, params):
        self.params = params

    def get(self, key):
        '''returns empty string if not found.'''
        ret = self.params.get(key, [''])
        return ret[0]

def displayActual192_168Address():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ret = s.getsockname()[0]
    s.close()
    if ret.startswith('192') or ret.startswith('172') or ret.startswith('10'):
        return ret
    else:
        return '(Could not get local address... please run ifconfig ' + \
            'or ipconfig and get address that usually looks like 192.168.*)'

def genToken():
    if useHardcodedToken:
        getPressEnterToContinue("We're using a hard-coded token " +
            "for testing, don't run this in production :)")
        return useHardcodedToken
    else:
        import secrets
        return secrets.token_urlsafe(6)

def debugMode():
    return not not useHardcodedToken

class MoltenTFException(Exception):
    pass

def assertTrueMolten(b, context1='', context2='', context3=''):
    if not b:
        msg = 'An error occurred, ' + context1 + context2 + context3
        raise MoltenTFException(msg)

def getPortNumberAsString():
    return ':' + str(portNumber())

def isSimpleAlphaNumOrSymbolOrHigherUnicode(s):
    for c in s:
        n = ord(c)
        if n < 32:
            return False
        elif c in '"<>&|?~`':
            return False
        elif n > 126 and n <= 128:
            return False
        elif n > 128:
            return True
    return True

class SerializableListOfFileInfo(object):
    def __init__(self):
        self._listOfFilenames = []
        self._listOfChecksums = []

    def len(self):
        return len(self._listOfFilenames)

    def addFiles(self, listFileFullPaths):
        for f in listFileFullPaths:
            self._listOfFilenames.append(f)
            self._listOfChecksums.append(files.computeHash(f, 'sha256'))

    def serializeWithOnlyLeafNames(self):
        assertEq(len(self._listOfFilenames), len(self._listOfChecksums))
        listOfNamesOnly = [files.getname(f) for f in self._listOfFilenames]
        zipped = zip(listOfNamesOnly, self._listOfChecksums)
        return '\n'.join('|'.join(parts) for parts in zipped)

    def deserialize(self, s):
        for pts in s.replace('\r\n', '\n').split('\n'):
            infos = pts.split('|')
            self._listOfFilenames.append(infos[0])
            self._listOfChecksums.append(infos[1])

    def infoAtIndex(self, index):
        assertTrue(index >= 0,
            'cannot get a negative index', index)
        assertTrue(index < len(self._listOfFilenames),
            f'asked for index {index} but there are only ' +
            f'{len(self._listOfFilenames)} files')
        return Bucket(
            filename=self._listOfFilenames[index],
            checksum=self._listOfChecksums[index])

    def infoAtIndexString(self, params, key):
        index = params.get(key)
        if index is None:
            raise Exception(f'Missing parameter: {key}')
        try:
            index = int(index)
        except:
            raise Exception(f'Parameter {key} must be an integer')
        return self.infoAtIndex(index)

    def addFromSpec(self, path, isStar):
        if isStar:
            import glob
            fs = glob.glob(path, recursive=False)
            for f in fs:
                if files.isfile(f):
                    self.addFiles([f])
        else:
            assertTrue(files.isfile(path), path)
            self.addFiles([path])

def isOkExtension(s):
    status = files.extensionPossiblyExecutable(s)
    if status == 'warn':
        warn('Warning: extension ' + ext + ' might be executable. continue?')
        return True
    elif status:
        return False
    else:
        return True

def checkOkDestPath(itemPath):
    # let's be really strict and check the filename
    if '/' in itemPath or '\\' in itemPath or ':' in itemPath:
        raise MoltenTFException('We do not support sending a file in a subdir')
    if '..' in itemPath:
        raise MoltenTFException('We do not support sending relative paths')
    if not isSimpleAlphaNumOrSymbolOrHigherUnicode(itemPath):
        raise MoltenTFException('Invalid char in path, we dissallow most ' +
            'unicode characters for security reasons')
    if not isOkExtension(itemPath):
        raise MoltenTFException('Disallowed extension')
    if not len(itemPath.strip()):
        raise MoltenTFException('Path is empty or whitespace')

def doAndCatchMftException(fn):
    ret = None
    caught = None
    try:
        ret = fn()
    except:
        caught = sys.exc_info()[1]
        if debugMode() and not isinstance(caught, MoltenTFException) \
                and not isinstance(caught, KeyboardInterrupt):
            raise
    return ret, caught

def doAndCheckForFileAccessErrAndReRaise(fn, filepath):
    try:
        fn()
    except OSError:
        getPressEnterToContinue(f"Looks like we could not access a file " +
            f"({filepath}). Unless you're already doing so, try running" +
            f" this script in a writable directory, and try again.")
        raise

def getStrInput(s, allowEmptyString=False):
    while True:
        ret = rinput(s)
        ret = ret.strip()
        if ret or allowEmptyString:
            return ret

def getPressEnterToContinue(s):
    s += '\nPress ENTER to continue'
    getStrInput(s, True)

def showMsg(level, s1, s2=None, s3=None):
    s = s1
    if s2:
        s += ' ' + str(s2)
    if s3:
        s += ' ' + str(s3)

    if level < 10 or debugMode():
        # use trace as it handles printing unicode characters
        trace(s)


msgInfo = 11
msgVerbose = 9
msgMed = 6
msgHigh = 1

def encodeForGet(s):
    s = str(s)
    return urllib.parse.quote(s)

def createServerUrlString(cxnParams, suburl='/', moreGetParams=None):
    assertTrue(suburl.startswith('/'))

    args = {}
    if moreGetParams:
        args.update(moreGetParams)

    if 'token' not in args:
        args['token'] = cxnParams.token

    partOfUrl = suburl
    partOfUrl += '?'
    partOfUrl += '&'.join([key + '=' + encodeForGet(args[key]) for key in args])
    url = f'http://{cxnParams.ip}:{getPortNumber()}{partOfUrl}'
    return url, partOfUrl

def expectResponseStartsWithCorrectPrefix(s):
    if not s.startswith('Molten:'):
        raise MoltenTFException('Did not start with expected prefix ' + s)
    else:
        return s[len('Molten:'):]

def smallTests():
    checkOkDestPath('a')
    checkOkDestPath('abc')
    checkOkDestPath('abc def')
    checkOkDestPath('abc.doc')
    checkOkDestPath('abc def.jpg')
    checkOkDestPath('a.jpg')
    assertException(lambda: checkOkDestPath('b/a.jpg'), Exception, 'subdir')
    assertException(lambda: checkOkDestPath('b\\a.jpg'), Exception, 'subdir')
    assertException(lambda: checkOkDestPath('C:a.jpg'), Exception, 'subdir')
    assertException(lambda: checkOkDestPath('..a.jpg'), Exception, 'relative')
    assertException(lambda: checkOkDestPath('a\n.jpg'), Exception, 'Invalid char')
    assertException(lambda: checkOkDestPath('a&.jpg'), Exception, 'Invalid char')
    assertException(lambda: checkOkDestPath('a|.jpg'), Exception, 'Invalid char')
    assertException(lambda: checkOkDestPath('a\0.jpg'), Exception, 'Invalid char')
    assertException(lambda: checkOkDestPath('a.exe'), Exception, 'extension')
    assertException(lambda: checkOkDestPath('a.jpg.exe'), Exception, 'extension')
    assertException(lambda: checkOkDestPath('a.jpg.Exe'), Exception, 'extension')
    assertException(lambda: checkOkDestPath('a.jpg.EXE'), Exception, 'extension')
    assertException(lambda: checkOkDestPath('a.app'), Exception, 'extension')
    assertException(lambda: checkOkDestPath('a.jpg.app'), Exception, 'extension')
    assertException(lambda: checkOkDestPath('a.jpg.App'), Exception, 'extension')
    assertException(lambda: checkOkDestPath('a.jpg.APP'), Exception, 'extension')
    assertException(lambda: checkOkDestPath(''), Exception, 'empty')
    assertException(lambda: checkOkDestPath('  '), Exception, 'empty')
    trace('small tests pass')


if debugMode():
    smallTests()
