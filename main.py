#Author: Pyro
#Description: This script shuffles songs in VTOL VR when the pilot dies or leaves the lobby
#Version: 1.0.0
#Date: 5-27-2023

'''
MIT License

Copyright (c) 2023 Pyro

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

'''


import os
import subprocess
import uuid
import vdf
import winreg


def get_log_path(): # Returns the path to the log file
    appdata_path = os.path.abspath(os.path.join(os.getenv('APPDATA'), os.pardir)) # This is the path to the appdata folder (C:\Users\USERNAME\AppData\)
    return os.path.join(appdata_path, "LocalLow", "Boundless Dynamics, LLC", "VTOLVR", "player.log") 

def getDirectory(): # Returns the path to the radio folder
    steam_path = winreg.QueryValueEx(winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\WOW6432Node\Valve\Steam"), "InstallPath") # This grabs the steam installation folder from the registry

    libraryfoldersPath = os.path.abspath(os.path.join(steam_path[0], "config", "libraryfolders.vdf")) #The libraryfolders.vdf file contains the paths to all the steam libraries folders (installations on different drives)

    with open(libraryfoldersPath, "r") as f:
        libraryfolders = vdf.load(f)

    for key in libraryfolders["libraryfolders"]: # Loops through the libraryfolders.vdf file and finds the path to the drive where VTOL VR is installed
        for app in libraryfolders["libraryfolders"][key]["apps"]:
            if app == "667970": # This is the app id for VTOL VR
                appDrive = libraryfolders["libraryfolders"][key]["path"]
                break

    finalPath = os.path.join(appDrive, "steamapps", "common", "VTOL VR", "RadioMusic")
    return finalPath

Directory = getDirectory()
def renameFilesRandomly(): # This shuffles the songs in the radio folder
    for filename in os.listdir(Directory):
        if filename.endswith(".mp3"):
            if filename.startswith("randomSong"):
                originalName = filename[17:-5]
            else:
                originalName = filename[:-4]
            os.rename(os.path.join(Directory, filename), os.path.join(Directory, "randomSong" + str(uuid.uuid4())[:5] + f" ({originalName})" +".mp3")) # This renames the file to randomSong + a random string + the original name + .mp3
            continue
        else:
            continue


if __name__ == "__main__": #This handles the log file, new lines and setting the pilot name
    pilot = None

    def on_new_line(line):
        global pilot
        if "Set current pilot to " in line:
            pilot = line.split("Set current pilot to ")[1]
        elif f"{pilot} was killed" in line:
            renameFilesRandomly()
        elif f"{pilot} ejected." in line:
            renameFilesRandomly()
        elif "Stopping EndMission" in line:
            renameFilesRandomly()
        elif "LeaveLobby()" in line:
            renameFilesRandomly()

    logFilePath = get_log_path()
    tail_process = subprocess.Popen(["powershell.exe", 'Get-Content ', f'"{logFilePath}"', '-Wait'], stdout=subprocess.PIPE) # open the log file and waits for new lines

    while True:
        line = tail_process.stdout.readline()
        line = line.decode("utf-8").strip()
        if line:
            on_new_line(line)
