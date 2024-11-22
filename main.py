import wget
from configparser import ConfigParser
import os
import time

import taptap
import gameInformation
import getResource
import phira


ver_now = "3.10.2"
#ver_now = input("请输入当前版本号:")

r = taptap.taptap(165287)
print(f"TapTap: {r["data"]["apk"]["version_name"]}")


while ver_now == r["data"]["apk"]["version_name"]:
    time.sleep(5)
    r = taptap.taptap(165287)
    print(f"TapTap: {r["data"]["apk"]["version_name"]}")
'''else:
    print("New Version")'''

ver = r["data"]["apk"]["version_name"]
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

#input("Finish")