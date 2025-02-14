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
    #ver = "3.10.1"
    apk_name = f"Phigros_{ver}.apk"
    if os.path.exists(apk_name):
        print("Apk exists, skip download")
    else:
        wget.download(r["data"]["apk"]["download"], apk_name)


    apk_name = f"Phigros_{ver}.apk"
else:
    apk_name = f"Phigros_{ver_now}.apk"

gameInformation.run(apk_name)


start_time = time.time()
getResource.run(apk_name, {
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
phira.run(False)
print(f"elapsed time: {time.time() - start_time} s")


output_directory = os.path.join("output")
cover_output_directory = os.path.join(output_directory, "Cover")

if render.getboolean("autoCover"):
    start_time = time.time()
    import autoImage
    input_directory = "Illustration"

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

def pushRender(difficulty, output_directory):
    if render.getboolean(difficulty):
        input_folder = os.path.join("phira", difficulty)
        output_folder =os.path.join(output_directory, difficulty)
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
