Set WshShell = CreateObject("WScript.Shell")
Set FileSystem = CreateObject("Scripting.FileSystemObject")
ProjectFolder = FileSystem.GetParentFolderName(WScript.ScriptFullName)
PythonwPath = ProjectFolder & "\.venv\Scripts\pythonw.exe"
LoginPath = ProjectFolder & "\login_gui.py"
WshShell.CurrentDirectory = ProjectFolder
WshShell.Run Chr(34) & PythonwPath & Chr(34) & " " & Chr(34) & LoginPath & Chr(34), 0, False