import subprocess
import os

# Single Chart
def schartTask(dir,path):
    makeOneTask(dir, path)

# Single Folder
def sfileTask(dir,path):
    for file in os.listdir(path):
        if file.endswith(".pez"):
            #command = f"--render {path}/{file}"
            #makeTask(dir,command)
            makeOneTask(dir, f"{path}/{file}")

# All Folder
def fileTask(dir,path):
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".pez"):
                makeTask(dir, root, file)


# Create Task
def makeTask(dir,root, file):
    command = f"\"{dir}\" --render {os.path.abspath(root)}/{file}"

    print(command)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    process.wait()

def makeOneTask(dir, file):
    command = f"\"{dir}\" --render {os.path.abspath(file)}"
    
    print(command)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    process.wait()


def fileType(dir):
    for filename in os.listdir(dir):
        if filename in ['EZ','HD','IN','AT']:
            return "Phira"
    return ""
