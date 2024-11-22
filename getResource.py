import base64
from concurrent.futures import ThreadPoolExecutor
from configparser import ConfigParser
import gc
from io import BytesIO
import json
import os
from queue import Queue
import shutil
import sys
import threading
import time
from tqdm import tqdm
from UnityPy import Environment
from UnityPy.classes import AudioClip
from UnityPy.enums import ClassIDType
from zipfile import ZipFile
from fsb5 import FSB5

class ByteReader:
    def __init__(self, data):
        self.data = data
        self.position = 0

    def readInt(self):
        self.position += 4
        return int.from_bytes(self.data[self.position-4:self.position], 'little')

queue_out = Queue()
queue_in = Queue()

def getbool(t):
    if t[:6] == "Chart_":
        return config["Chart"]
    else:
        return config[t]

def io():
    while True:
        item = queue_in.get()
        if item is None:
            break
        elif isinstance(item, list):
            env = Environment()
            for i in range(1, len(item)):
                env.load_file(item[0].read(f"assets/aa/Android/{item[i][1]}"), name=item[i][0])
            queue_out.put(env)
            del env
        else:
            path, resource = item
            if isinstance(resource, BytesIO):
                with resource:
                    with open(path, "wb") as f:
                        f.write(resource.getbuffer())
            else:
                with open(path, "wb") as f:
                    f.write(resource)

def save_image(path, image):
    bytesIO = BytesIO()
    image.save(bytesIO, "png")
    queue_in.put((path, bytesIO))

def save_music(path, music: AudioClip):
    # queue_in.put((path, music.samples["music.wav"]))
    fsb = FSB5(music.m_AudioData)
    rebuilt_sample = fsb.rebuild_sample(fsb.samples[0])
    '''with open(path, 'wb') as fp:
        fp.write(rebuilt_sample)'''
    queue_in.put((path, rebuilt_sample))

classes = ClassIDType.TextAsset, ClassIDType.Sprite, ClassIDType.AudioClip

def save(key, entry, pbar):
    obj = next(entry.get_filtered_objects(classes)).read()
    if config["avatar"] and key.startswith("avatar."):
        key = key[7:] if key != "Cipher1" else avatar.get(key[7:], key)
        pbar.set_postfix_str(key)
        bytesIO = BytesIO()
        obj.image.save(bytesIO, "png")
        queue_in.put((f"avatar/{key}.png", bytesIO))
    elif config["Chart"] and key[-14:-7] == "/Chart_" and key[-5:] == ".json":
        name = key[:-14]
        file_name = (name[:17] + '...') if len(name) > 20 else name
        pbar.set_postfix_str(file_name)
        queue_in.put(("Chart_%s/%s.json" % (key[-7:-5], name), obj.script))
    elif config["Chart"] and key[-18:-11] == "/Chart_" and key[-5:] == ".json":
        name = key[:-18]
        file_name = (name[:17] + '...') if len(name) > 20 else name
        pbar.set_postfix_str(file_name)
        queue_in.put(("Chart_%s/%s.json" % (key[-11:-5], name), obj.script))
    elif config["IllustrationBlur"] and key.endswith("/IllustrationBlur.png"):
        bytesIO = BytesIO()
        obj.image.save(bytesIO, "png")
        name = key[:-21]
        file_name = (name[:17] + '...') if len(name) > 20 else name
        pbar.set_postfix_str(file_name)
        queue_in.put((f"IllustrationBlur/{name}.png", bytesIO))
    elif config["IllustrationLowRes"] and key.endswith("/IllustrationLowRes.png"):
        name = key[:-23]
        file_name = (name[:17] + '...') if len(name) > 20 else name
        pbar.set_postfix_str(file_name)
        bytesIO = BytesIO()
        obj.image.save(bytesIO, "png")
        queue_in.put((f"IllustrationLowRes/{name}.png", bytesIO))
        #pool.submit(save_image, f"IllustrationLowRes/{name}.png", obj.image)
    elif config["Illustration"] and key.endswith("/Illustration.png"):
        name = key[:-17]
        file_name = (name[:17] + '...') if len(name) > 20 else name
        pbar.set_postfix_str(file_name)
        bytesIO = BytesIO()
        obj.image.save(bytesIO, "png")
        queue_in.put((f"Illustration/{name}.png", bytesIO))
        #pool.submit(save_image, f"Illustration/{name}.png", obj.image)
    elif config["music"] and key.endswith("/music.wav"):
        name = key[:-10]
        file_name = (name[:17] + '...') if len(name) > 20 else name
        pbar.set_postfix_str(file_name)
        #pool.submit(save_music, f"music/{name}.wav", obj)
        #queue_in.put((f"music/{name}.wav", obj.samples["music.wav"]))
        save_music(f"music/{name}.ogg", obj)

def run(path, c):
    global config
    config = c
    with ZipFile(path) as apk:
        with apk.open("assets/aa/catalog.json") as f:
            data = json.load(f)

    type_list = ["avatar", "Chart_Legacy", "Chart_EZ", "Chart_HD", "Chart_IN", "Chart_AT", "IllustrationBlur", "IllustrationLowRes", "Illustration", "music"]
    for directory in filter(lambda x: getbool(x), type_list):
        shutil.rmtree(directory, True)
        os.mkdir(directory)

    key = base64.b64decode(data["m_KeyDataString"])
    bucket = base64.b64decode(data["m_BucketDataString"])
    entry = base64.b64decode(data["m_EntryDataString"])

    table = []
    reader = ByteReader(bucket)
    for _ in range(reader.readInt()):
        key_position = reader.readInt()
        key_type = key[key_position]
        key_position += 1
        if key_type == 0:
            length = key[key_position]
            key_position += 4
            key_value = key[key_position:key_position + length].decode()
        elif key_type == 1:
            length = key[key_position]
            key_position += 4
            key_value = key[key_position:key_position + length].decode("utf16")
        elif key_type == 4:
            key_value = key[key_position]
        else:
            raise ValueError(f"Unknown key type: {key_type}")
        for _ in range(reader.readInt()):
            entry_position = reader.readInt()
            entry_value = entry[4 + 28 * entry_position:4 + 28 * entry_position + 28]
            entry_value = int.from_bytes(entry_value[8:10], 'little')
        table.append([key_value, entry_value])
    for i in range(len(table)):
        if table[i][1] != 65535:
            table[i][1] = table[table[i][1]][0]
    for i in range(len(table) - 1, -1, -1):
        if type(table[i][0]) == int or table[i][0][:15] == "Assets/Tracks/#" or table[i][0][:14] != "Assets/Tracks/" and table[i][0][:7] != "avatar.":
            del table[i]
        elif table[i][0][:14] == "Assets/Tracks/":
            table[i][0] = table[i][0][14:]

    global avatar
    if config["avatar"]:
        with open("avatar.csv", encoding="utf8") as f:
            avatar = dict(line.strip().split(",")[:2] for line in f)

    thread = threading.Thread(target=io)
    thread.start()

    global pool
    with ThreadPoolExecutor() as pool:
        if all(v == 0 for v in config["UPDATE"].values()):
            with ZipFile(path) as apk:
                size = 0
                batch = [apk]
                pbar = tqdm(table, desc="Extract")
                for key, entry in pbar:
                    batch.append((key, entry, pbar))
                    size += apk.getinfo(f"assets/aa/Android/{entry}").file_size
                    if size > 32 * 1024 * 1024:
                        queue_in.put(batch)
                        env = queue_out.get()
                        for ikey, ientry in env.files.items():
                            save(ikey, ientry, pbar)
                        size = 0
                        batch = [apk]
                queue_in.put(batch)
                env = queue_out.get()
                for ikey, ientry in env.files.items():
                    save(ikey, ientry, pbar)
        else:
            l = []
            with open("difficulty.csv", encoding="utf8") as f:
                line = f.readline()
                while line:
                    l.append(line.split(",", 2)[0])
                    line = f.readline()
            index1 = l.index("Doppelganger.LeaF")
            index2 = l.index("Poseidon.1112vsStar")
            # index2 = l.index("Random.SobremSilentroom") + 1 # Test Random
            del l[index2:len(l) - config["UPDATE"]["side_story"]] 
            del l[index1:index2 - config["UPDATE"]["other_song"]] 
            del l[:index1 - config["UPDATE"]["main_story"]]

            env = Environment()
            with ZipFile(path) as apk:
                # pbar = tqdm(table, desc="Extract")
                with tqdm(table, desc="FindChart") as pbar:
                    for key, entry in pbar:
                        if key.startswith("avatar."):
                            env.load_file(apk.read(f"assets/aa/Android/{entry}"), name=key)
                        if any(key.startswith(f"{id}") for id in l):
                            env.load_file(apk.read(f"assets/aa/Android/{entry}"), name=key)
                with tqdm(env.files.items(), desc="Extract") as pbar:
                    for ikey, ientry in pbar:
                        save(ikey, ientry, pbar)

    queue_in.put(None)
    thread.join()

if __name__ == "__main__":
    c = ConfigParser()
    c.read("config.ini", encoding="utf8")
    types = c["TYPES"]
    run(sys.argv[1], {
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
