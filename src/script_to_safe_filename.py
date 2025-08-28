# script_to_safe_filename.py
# Ben Fisher, 2019
# Released under the GNU General Public License version 3

# it can be useful to run this script before transferring files,
# since different operating systems are more restrictive
# in which characters are allowed in a filename.

from mft_common import *

def toWindowsSafeFilename(d, maxNameLen):
    for f, short in list(files.recurseFiles(d)):
        if short == '.DS_Store':
            files.deleteSure(f)
            continue

        fRenamed = toValidFilename(getPrintable(f), dirsepOk=True)
        if len(files.getName(fRenamed)) > maxNameLen:
            truncated = files.getName(fRenamed)[0:maxNameLen - 10]
            newShort = truncated + '...' + files.splitExt(fRenamed)[1]
            fRenamed = files.join(files.getParent(fRenamed), newShort)

        if f != fRenamed:
            if files.exists(fRenamed):
                fRenamed = addNumber(fRenamed)

            if os.path.sep in fRenamed:
                files.makeDirs(files.getParent(fRenamed))

            files.move(f, fRenamed, False, doTrace=True)

def addNumber(f):
    for i in range(100):
        attempt = files.splitExt(f)[0] + '.%03d'%i + files.splitExt(f)[1]
        if not files.exists(attempt):
            return attempt

    assertWarn(False, "Cannot rename", f)

def makeDirList(dir, outfile):
    with open(outfile, 'w', encoding='utf-8') as fout:
        for f, short in sorted(list(files.recurseFiles(dir))):
            fout.write(f)
            fout.write('\t')
            fout.write(str(files.getSize(f)))
            fout.write('\t')
            fout.write(str(files.getLastModTime(f)))
            fout.write('\n')

if __name__ == '__main__':
    maxNameLen = 75
    dir = '/path'
    toWindowsSafeFilename(dir, maxNameLen)
