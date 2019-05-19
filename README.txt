Right now the script needs both grive_sync.py and security.py running at the same time.  The grive_sync.py script will constantly try to sync the Google drive folder with the cloud, while the security.py script will do the actual video recording.
1. Install SQLite3 On Mac.
Download the SQLite zip file from SQLite official website.
Then unzip the download file into a local folder such as /Users/zhaosong/Documents/WorkSpace/tool/sqlite-tools.
Now the SQLite server has been installed, it do not need any installation.
2. Start SQLite Server.
Open a terminal and CD to the SQLite file unzip folder.
Execute sqlite3 in command line, when you see below messages, the SQLite server has been started.
192:sqlite-tools zhaosong$ sqlite3
SQLite version 3.23.1 2018-04-10 17:39:29
Enter ".help" for usage hints.
Connected to a transient in-memory database.
Use ".open FILENAME" to reopen on a persistent database.
sqlite>
Now click Finder —> Go —> Applications to open MacOS application folder. And click Utilities —> Activity Monitor to open the activity monitor. You can find the sqlite3 process in this window.
