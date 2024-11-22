import os
import shutil
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED


def run():
    levels = ["EZ", "HD", "IN", "AT"]

    shutil.rmtree("phira", True)
    os.mkdir("phira")
    for level in levels:
        os.mkdir("phira/%s" %level)

    infos = {}
    with open("info.csv", encoding="utf8") as f:
        while True:
            line = f.readline()
            if not line:
                break
            line = line[:-1].split("\\")
            infos[line[0]] = {"Name": line[1], "Composer": line[2], "Illustrator": line[3], "Chater": line[4:]}
    with open("difficulty.csv", encoding="utf8") as f:
        while True:
            line = f.readline()
            if not line:
                break
            line = line[:-1].split(",")
            infos[line[0]]["difficulty"] = line[1:]
    for id, info in infos.items():
        print(info["Name"], info["Composer"])
        for level in range(len(info["difficulty"])):
            with ZipFile("phira/%s/%s-%s.pez" % (levels[level], id, levels[level]), "x", compression=ZIP_STORED) as pez:
                pez.writestr("info.txt", "#\nName: %s\nSong: %s.wav\nPicture: %s.png\nChart: %s.json\nLevel: %s Lv.%s\nComposer: %s\nIllustrator: %s\nCharter: %s" % (info["Name"], id, id, id, levels[level], info["difficulty"][level], info["Composer"], info["Illustrator"], info["Chater"][level]))
                pez.write("Chart_%s/%s.0.json" % (levels[level], id), "%s.json" % id)
                pez.write("Illustration/%s.0.png" % id, "%s.png" % id)
                pez.write("music/%s.0.wav" % id, "%s.wav" % id)

if __name__=="__main__":
    run()