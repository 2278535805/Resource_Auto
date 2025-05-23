import wget
from configparser import ConfigParser
import os
import time

import taptap
import gameInformation
import getResource
import phira
import ttools


c = ConfigParser()
c.read("config.ini", "utf8")
types = c["TYPES"]
render = c["SETTING"]


ver_now = input("请输入当前版本号:")

if render.getboolean("autoUpdate"):
    times = 0
    r = taptap.taptap(165287)
    print(f"TapTap: {r["data"]["apk"]["version_name"]} ({times})", end="\r")


    while ver_now == r["data"]["apk"]["version_name"]:
        times += 1
        time.sleep(10)
        try:
            r = taptap.taptap(165287)
            print(f"TapTap: {r["data"]["apk"]["version_name"]} ({times})")
        except:
            print("null")
    else:
        print()

    #r = taptap.taptap(165287)
    ver = r["data"]["apk"]["version_name"]
    chdir = os.path.join(ver)
    #ver = "3.10.1"
    apk_name = f"Phigros_{ver}.apk"
    if os.path.exists(apk_name):
        print("Apk exists, skip download")
    elif render.getboolean("autoDownload"):
        wget.download(r["data"]["apk"]["download"], apk_name)
    else:
        print(r["data"]["apk"]["download"])
        apk_name_input = input(f"Download the apk manually \nrename to {apk_name} or input apk_name \n")
        if len(apk_name_input) > 0:
            apk_name = apk_name_input
else:
    apk_name = f"Phigros_{ver_now}.apk"
    chdir = os.path.join(ver_now)

if not os.path.exists(chdir):
    os.makedirs(chdir)

gameInformation.run(apk_name, chdir)


start_time = time.time()
getResource.run(apk_name, chdir, {
    "avatar": types.getboolean("avatar"),
    "Chart": types.getboolean("Chart"),
    "IllustrationBlur": types.getboolean("illustrationBlur"),
    "IllustrationLowRes": types.getboolean("illustrationLowRes"),
    "Illustration": types.getboolean("illustration"),
    "music": types.getboolean("music"),
    "UPDATE": {
        "main_story": c["UPDATE"].getint("main_story"),
        "side_story": c["UPDATE"].getint("side_story"),
        "other_song": c["UPDATE"].getint("other_song")
    }
})
print(f"elapsed time: {time.time() - start_time} s")

start_time = time.time()
phira.run(chdir, False)
print(f"elapsed time: {time.time() - start_time} s")


output_directory = os.path.join(chdir, "output")
cover_output_directory = os.path.join(output_directory, "Cover")

if render.getboolean("autoCover"):
    start_time = time.time()
    import autoImage
    input_directory = os.path.join(chdir, "Illustration")

    if not os.path.exists(cover_output_directory):
        os.makedirs(cover_output_directory)

    for file in os.listdir(input_directory):
        if file.endswith(".png"):
            print(file)
            input_file_path = os.path.join(input_directory, file)
            output_file_path = os.path.join(cover_output_directory, file)
            autoImage.run(input_file_path, output_file_path)
    print(f"elapsed time: {time.time() - start_time} s")

difficulty = ["AT", "IN", "HD", "EZ"]

if not os.path.exists(output_directory):
        os.makedirs(output_directory)

def pushRender(difficulty: str, output_directory: str):
    if render.getboolean(difficulty):
        input_folder = os.path.join(chdir, "phira", difficulty)

        if not os.path.exists(input_folder) or not os.listdir(input_folder):
            return
    
        output_folder = os.path.join(output_directory, difficulty)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        ttools.sfileTask(render.get("phiRender"), input_folder, output_folder)

if render.getboolean("autoRender"):
    start_time = time.time()
    pushRender(difficulty[0], output_directory)
    pushRender(difficulty[1], output_directory)
    pushRender(difficulty[2], output_directory)
    pushRender(difficulty[3], output_directory)
    print(f"elapsed time: {time.time() - start_time} s")


input("Finish")
