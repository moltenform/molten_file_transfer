# molten_file_transfer

If you can install Python on it, you can transfer files to it!

Why use this script instead of a VirtualBox shared folder?
* Works on a virtual machine running a more-obscure OS that doesn't support shared folders
* Can transfer files out of a potentially-malware-infected computer or vm, because you can precisely specify the only files that are copied. For example, it is safe against malware mechanisms that spread over SMB shares or USB drives
* Control the direction in which files can be sent, host-to-guest or guest-to-host

Why use this script to transfer files across a local network?
* No need to set up NFS, webdav, an rsync daemon, or windows file sharing - just type in an IP address
* SHA256 hashes verify that the file contents are correct

Example:
* Run main.py on your host machine
* Select `Start a mft server and send files`
* Type a directory, like `/home/me/myfiles/*`
* Install Python in your VM.
* Run main.py in your VM.
* Select `Connect to a mft server and receive files`
* Type the IP address and other info, then the files will be transfered!

More info
* Uses a per-session token so that only an authorized client can connect
* Files are only be sent into a designated destination directory and cannot overwrite existing files
* Executable file extensions are always blocked
* Can transfer large files, even multi-gigabyte files that are too big to fit in RAM!





