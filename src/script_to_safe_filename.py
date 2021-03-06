# script_to_safe_filename.py
# Ben Fisher, 2019
# Released under the GNU General Public License version 3

# it can be useful to run this script before transferring files,
# since different operating systems are more restrictive
# in which characters are allowed in a filename.

from mft_common import *

def toWindowsSafeFilename(d, maxNameLen):
    for f, short in list(files.recursefiles(d)):
        if short == '.DS_Store':
            files.deletesure(f)
            continue

        fRenamed = toValidFilename(getPrintable(f), dirsepOk=True)
        if len(files.getname(fRenamed)) > maxNameLen:
            truncated = files.getname(fRenamed)[0:maxNameLen - 10]
            newShort = truncated + '...' + files.splitext(fRenamed)[1]
            fRenamed = files.join(files.getparent(fRenamed), newShort)

        if f != fRenamed:
            if files.exists(fRenamed):
                fRenamed = addNumber(fRenamed)

            if os.path.sep in fRenamed:
                files.makedirs(files.getparent(fRenamed))

            files.move(f, fRenamed, False, traceToStdout=True)

def addNumber(f):
    for i in range(100):
        attempt = files.splitext(f)[0] + '.%03d'%i + files.splitext(f)[1]
        if not files.exists(attempt):
            return attempt

    assertWarn(False, "Cannot rename", f)

def makeDirList(outfile, dir):
    with open(outfile, 'w', encoding='utf-8') as fout:
        for f, short in sorted(list(files.recursefiles(dir))):
            fout.write(short)
            fout.write('\t')
            fout.write(str(files.getsize(f)))
            fout.write('\n')

if __name__ == '__main__':
    maxNameLen = 75
    dir = '/path'
    toWindowsSafeFilename(dir, maxNameLen)
