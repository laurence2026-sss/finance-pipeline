Set WshShell = CreateObject("WScript.Shell")

Dim batPath
batPath = Replace(WScript.ScriptFullName, "start_dashboard.vbs", "start_dashboard.bat")
WshShell.Run Chr(34) & batPath & Chr(34), 0, False
