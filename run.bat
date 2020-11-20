cd scripts\chinjucc
set PATH=%PATH%;..\anaconda3;..\anaconda3\Scripts;..\anaconda3\Library\bin
set QT_PLUGIN_PATH=..\anaconda3\Library\plugins
..\PortableGit\bin\git.exe pull
..\anaconda3\pythonw main_chinjucc.py
