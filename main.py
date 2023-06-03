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
import time



def get_log_path(): # Returns the path to the log file
    return os.path.join(os.getenv('APPDATA'), os.pardir, "LocalLow", "Boundless Dynamics, LLC", "VTOLVR", "player.log") 

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

def renameFilesRandomly(directory): # This shuffles the songs in the radio folder
    for filename in os.listdir(directory):
        if filename.endswith(".mp3"):
            if filename.startswith("randomSong"):
                originalName = filename[17:-5]
            else:
                originalName = filename[:-4]
            os.rename(os.path.join(directory, filename), os.path.join(directory, "randomSong" + str(uuid.uuid4())[:5] + f" ({originalName})" +".mp3")) # This renames the file to randomSong + a random string + the original name + .mp3


if __name__ == "__main__": #This handles the log file, new lines and setting the pilot name
    counter = 0
    deaths = 0
    Directory = getDirectory()
    pilot = None
    numberOfLines = 0 #Number of lines at startup
    currentLine = 0 #Number of lines processed
    logFilePath = get_log_path()
    currentVersion = "v1.0.3"
    print(f"VTOL VR Radio Shuffler {currentVersion}")

    #Detect new version on github
    try:
        import requests
    except (ImportError):
        print("Requests not installed, skipping update check")
    else:
        api_page = "https://api.github.com/repos/PyroCalzone/VTOL-VR-Shuffle/releases/latest"
        request = requests.get(api_page).json()
        newestVersion = request["tag_name"]
        if newestVersion > currentVersion:
            print(f"Update detected ({newestVersion}) check out the update on github: https://github.com/PyroCalzone/VTOL-VR-Shuffle/releases/latest")
            print(f'Changelog : \n{request["body"]}\n-------\n')
    

    #add a flag to see if we've reached the end of the log file on startup

    with open(logFilePath, "r", encoding="utf-8", errors="ignore") as f:
        numberOfLines = len([line for line in f.readlines() if line.strip()])
    

    def on_new_line(line):
        global pilot
        global counter
        global deaths
        if "Set current pilot to " in line:
            pilot = line.split("Set current pilot to ")[1]
            print(f"Set pilot to {pilot}")
        elif "Returning to briefing room." in line:
            counter += 1
            if counter == 2: # "Returning to briefing room." is printed twice when the pilot dies, wait for the second one
                deaths += 1
                counter = 0
                if currentLine > numberOfLines:
                    print(f"{pilot} died, shuffling songs. Death count: {deaths}")
                    time.sleep(2.5)
                    try:
                        renameFilesRandomly(Directory)
                    except PermissionError:
                        print("PermissionError, trying again")
                        time.sleep(2)
                        renameFilesRandomly(Directory)
        elif "Stopping EndMission" in line:
            print(f"{pilot} left the lobby, shuffling songs")
            if currentLine > numberOfLines: 
                renameFilesRandomly(Directory)
            deaths = 0

    tail_process = subprocess.Popen(["powershell.exe", 'Get-Content ', f'"{logFilePath}"', '-Wait'], stdout=subprocess.PIPE) # open the log file and waits for new lines

    while True:
        line = tail_process.stdout.readline()
        line = line.decode("utf-8", errors='ignore').strip()
        if line:
            currentLine += 1
            on_new_line(line)
