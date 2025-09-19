import os
import shutil
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED
import json
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

def create_zip_file(chdir, id, info, levels, level, pbar):
    file_name = (id[:17] + '...') if len(id) > 20 else id
    pbar.set_postfix_str(file_name)
    pez_filename = f"{chdir}/phira/{levels[level]}/{id}-{levels[level]}.pez"
    num = ".0"
    if os.path.exists(f"{chdir}/Chart_{levels[level]}/{id}{num}.json"):
        with ZipFile(pez_filename, "w", compression=ZIP_DEFLATED) as pez:
            pez.writestr(
                "info.txt",
                "#\nName: %s\nSong: %s.ogg\nPicture: %s.png\nChart: %s.json\nLevel: %s  Lv.%s\nComposer: %s\nIllustrator: %s\nCharter: %s" % (
                    info["Name"], id, id, id, levels[level], info["difficulty"][level], 
                    info["Composer"], info["Illustrator"], info["Chater"][level]
                )
            )

            pez.write(f"{chdir}/Chart_{levels[level]}/{id}{num}.json", f"{id}.json")
            pez.write(f"{chdir}/Illustration/{id}{num}.png", f"{id}.png")
            pez.write(f"{chdir}/music/{id}{num}.ogg", f"{id}.ogg")
    pbar.update(1)

def create_file(chdir, id, info, levels, level, pbar):
    file_name = (id[:17] + '...') if len(id) > 20 else id
    pbar.set_postfix_str(file_name)
    dir_path = f"{chdir}/phira/{levels[level]}/{id}-{levels[level]}"
    num = ".0"
    os.makedirs(dir_path, exist_ok=True)

    with open(f"{dir_path}/info.txt", "w") as f:
        f.write(
            "#\nName: %s\nSong: %s.ogg\nPicture: %s.png\nChart: %s.json\nLevel: %s  Lv.%s\nComposer: %s\nIllustrator: %s\nCharter: %s" % (
                info["Name"], id, id, id, levels[level], info["difficulty"][level], 
                info["Composer"], info["Illustrator"], info["Chater"][level]
            )
        )

    shutil.copy(f"{chdir}/Chart_{levels[level]}/{id}{num}.json", f"{dir_path}/{id}.json")
    shutil.copy(f"{chdir}/Illustration/{id}{num}.png", f"{dir_path}/{id}.png")
    shutil.copy(f"{chdir}/music/{id}{num}.ogg", f"{dir_path}/{id}.ogg")

    pbar.update(1)

def run(chdir: str, nozip: bool):
    levels = ["EZ", "HD", "IN", "AT"]

    shutil.rmtree(os.path.join(chdir, "phira"), True)
    os.mkdir(os.path.join(chdir, "phira"))
    for level in levels:
        os.mkdir(f"{chdir}/phira/{level}")

    raw_infos = {}
    with open(os.path.join(chdir, "info.json"), encoding="utf8") as f:
        raw_infos = json.load(f)
    infos = {}
    for item in raw_infos:
        song_id = item[0]
        infos[song_id] = {
            "Name": item[1],
            "Composer": item[2],
            "Illustrator": item[3],
            "Chater": item[4:]
        }

    with open(os.path.join(chdir, "difficulty.json"), encoding="utf8") as f:
        difficulty_data = json.load(f)

    for item in difficulty_data:
        song_id = item[0]
        if song_id in infos:
            infos[song_id]["difficulty"] = item[1:]

    tasks = [(id, info, levels, level) for id, info in infos.items() for level in range(len(info["difficulty"]))]
    if nozip:
        with tqdm(total=len(tasks), desc="CreatePEZ") as pbar:
            with ThreadPoolExecutor() as executor:
                for id, info, levels, level in tasks:
                    executor.submit(create_file, chdir, id, info, levels, level, pbar)
    else:
        with tqdm(total=len(tasks), desc="CreatePEZ") as pbar:
            with ThreadPoolExecutor() as executor:
                for id, info, levels, level in tasks:
                    executor.submit(create_zip_file, chdir, id, info, levels, level, pbar)

if __name__ == "__main__":
    run(os.getcwd(), False)
