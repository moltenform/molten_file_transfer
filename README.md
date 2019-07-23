# Molten File Transfer

A simple tool to transfer files in and out of a VM, or across a local network

<br/><br/>

Example:
* Run main.py on your host machine
* Select `Start a mft server and send files`
* Type a directory, like `/home/me/myfiles/*`
* Run main.py in your virtual machine.
* Select `Connect to a mft server and receive files`
* Type the IP address and other info, then the files will be transferred!

Why use this script instead of a VirtualBox shared folder?
* Works on a virtual machine running an OS that doesn't support shared folders
* Can transfer files out of a potentially-malware-infected computer or vm, because you can precisely specify the only files that are copied. For example, it is safe against malware mechanisms that spread over SMB shares or USB drives
* Control the direction in which files can be sent, host-to-guest or guest-to-host

Why use this script to transfer files across a local network?
* No need to set up NFS, webdav, an rsync daemon, or windows file sharing - just type in an IP address
* SHA256 hashes verify that the file contents are correct

More info
* Uses a per-session token so that only an authorized client can connect
* Files are only be sent into a designated destination directory and cannot overwrite existing files
* Executable file extensions are always blocked
* Can transfer large files, even multi-gigabyte files that are too big to fit in RAM!


