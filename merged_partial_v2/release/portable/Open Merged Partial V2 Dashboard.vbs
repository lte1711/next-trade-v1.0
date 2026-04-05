Set shell = CreateObject("WScript.Shell")
Dim currentDir
currentDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = currentDir
shell.Run "cmd /c start http://127.0.0.1:8787", 0, False
shell.Run Chr(34) & "merged_partial_v2_v1.exe" & Chr(34) & " --dashboard --dashboard-port 8787", 0, False
