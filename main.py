import wget
from configparser import ConfigParser
import os
import time

import taptap
import gameInformation
import getResource
import phira
import ttools


#ver_now = "3.10.2"
ver_now = input("请输入当前版本号:")

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

gameInformation.run(apk_name)

c = ConfigParser()
c.read("config.ini", "utf8")
types = c["TYPES"]
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

phira.run(False)

render = c["RENDER"]
output_directory = os.path.join("output")

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
    pushRender(difficulty[0], output_directory)
    pushRender(difficulty[1], output_directory)
    pushRender(difficulty[2], output_directory)
    pushRender(difficulty[3], output_directory)

if render.getboolean("autoCover"):
    import autoImage
    input_directory = "Illustration"

    for file in os.listdir(input_directory):
        if file.endswith(".png"):
            print(file)
            input_file_path = os.path.join(input_directory, file)
            output_file_path = os.path.join(output_directory, "Cover", file)
            autoImage.run(input_file_path, output_file_path)


input("Finish")
