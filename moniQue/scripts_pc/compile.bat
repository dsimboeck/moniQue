@echo off
call "C:\Program Files\QGIS 3.26.1\bin\o4w_env.bat"
call "C:\Program Files\QGIS 3.26.1\bin\qt5_env.bat"
call "C:\Program Files\QGIS 3.26.1\bin\py3_env.bat"

@echo on
pyrcc5 -o C:\Users\sfloe\Software\moniQue\moniQue\gui\resources.py C:\Users\sfloe\Software\moniQue\moniQue\gui\resources.qrc
pyrcc5 -o C:\Users\sfloe\Software\moniQue\moniQue\gui\resources_orient.py C:\Users\sfloe\Software\moniQue\moniQue\gui\resources_orient.qrc