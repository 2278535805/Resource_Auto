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
from UnityPy import Environment
from UnityPy.enums import ClassIDType
from zipfile import ZipFile



class ByteReader:
    def __init__(self, data):
        self.data = data
        self.position = 0

    def readInt(self):
        self.position += 4
        return self.data[self.position-4]^self.data[self.position-3]<<8^self.data[self.position-2]<<16

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
        if item == None:
            break
        elif type(item) == list:
            env = Environment()
            for i in range(1, len(item)):
                env.load_file(item[0].read("assets/aa/Android/%s" % item[i][1]), name=item[i][0])
            queue_out.put(env)
            del env
        else:
            path, resource = item
            print(path)
            if type(resource) == BytesIO:
                with resource:
                    with open(path, "wb") as f:
                        f.write(resource.getbuffer())
            else:
                with open(path, "wb") as f:
                    f.write(resource)

def save_image(path, image):
    bytesIO = BytesIO()
    # t1 = time.time()
    image.save(bytesIO, "png")
    # print("%f秒" % round(time.time() - t1, 4))
    queue_in.put((path, bytesIO))

def save_music(path, music):
    # t1 = time.time()
    queue_in.put((path, music.samples["music.wav"]))
    # print("%f秒" % round(time.time() - t1, 4))

# classes = ClassIDType.TextAsset, ClassIDType.Sprite, ClassIDType.AudioClip 看起来导出Sprite的图像质量更高
classes = ClassIDType.TextAsset, ClassIDType.Texture2D, ClassIDType.AudioClip
def save(key, entry):
    obj = entry.get_filtered_objects(classes)
    obj = next(obj).read()
    if config["avatar"] and key[:7] == "avatar.":
        key = key[7:]
        '''if key != "Cipher1":
            key = avatar[key]'''
        bytesIO = BytesIO()
        obj.image.save(bytesIO, "png")
        queue_in.put((f"avatar/%s.png" % key, bytesIO))
    elif key[:13] == "Introduction/":
        try:
            os.mkdir(f"{type_list}Introduction")
        except FileExistsError:
            pass
        if config["Chart"] and key[-5:] == ".json":
            queue_in.put((f"{type_list}%s" % (key), obj.script))
        elif config["music"] and key[-10:] == "/music.wav":
            pool.submit(save_music, f"{type_list}%s" % (key), obj)
        elif config["Illustration"] and key[-17:] == "/Illustration.png":
            pool.submit(save_image, f"{type_list}%s" % (key), obj.image)
    elif config["Chart"] and key[-14:-7] == "/Chart_" and key[-5:] == ".json":
        try:
            os.mkdir(type_list+key[:-16])
        except FileExistsError:
            pass
        queue_in.put((f"{type_list}%s/Chart_%s%s.json" % (key[:-16], key[-7:-5], key[-16:-14]), obj.script)) # /Chart_xx.json
    elif config["Chart"] and key[-18:-11] == "/Chart_" and key[-5:] == ".json":
        try:
            os.mkdir(type_list+key[:-20])
        except FileExistsError:
            pass
        queue_in.put((f"{type_list}%s/Chart_%s%s.json" % (key[:-20], key[-11:-5], key[-20:-18]), obj.script)) # /Chart_Legacy.json
    elif config["IllustrationBlur"] and key[-21:] == "/IllustrationBlur.png":
        try:
            os.mkdir(type_list+key[:-23])
        except FileExistsError:
            pass
        bytesIO = BytesIO()
        obj.image.save(bytesIO, "png")
        queue_in.put((f"{type_list}%s/IllustrationBlur%s.png" % (key[:-23], key[-23:-21]) , bytesIO))
    elif config["IllustrationLowRes"] and key[-23:] == "/IllustrationLowRes.png":
        try:
            os.mkdir(type_list+key[:-25])
        except FileExistsError:
            pass
        pool.submit(save_image, f"{type_list}%s/IllustrationLowRes%s.png" % (key[:-25], key[-25:-23]), obj.image)
    elif config["Illustration"] and key[-17:] == "/Illustration.png":
        try:
            os.mkdir(type_list+key[:-19])
        except FileExistsError:
            pass
        pool.submit(save_image, f"{type_list}%s/Illustration%s.png" % (key[:-19], key[-19:-17]), obj.image)
    elif config["music"] and key[-10:] == "/music.wav":
        try:
            os.mkdir(type_list+key[:-12])
        except FileExistsError:
            pass
        pool.submit(save_music, f"{type_list}%s/music%s.wav" % (key[:-12], key[-12:-10]), obj)

def run(path, c):
    global config
    global type_list
    config = c
    type_list = "chart/"

    print("#1")
    with ZipFile(path) as apk:
        with apk.open("assets/aa/catalog.json") as f:
            data = json.load(f)
    
    shutil.rmtree(type_list, True)
    os.mkdir(type_list)
    if config["avatar"]:
        shutil.rmtree("avatar", True)
        os.mkdir("avatar")


    key = base64.b64decode(data["m_KeyDataString"])
    bucket = base64.b64decode(data["m_BucketDataString"])
    entry = base64.b64decode(data["m_EntryDataString"])

    table = []
    reader = ByteReader(bucket)
    for x in range(reader.readInt()):
        key_position = reader.readInt()
        key_type = key[key_position]
        key_position += 1
        if key_type == 0:
            length = key[key_position]
            key_position += 4
            key_value = key[key_position:key_position+length].decode()
        elif key_type == 1:
            length = key[key_position]
            key_position += 4
            key_value = key[key_position:key_position+length].decode("utf16")
        elif key_type == 4:
            key_value = key[key_position]
        else:
            raise BaseException(key_position, key_type)
        for i in range(reader.readInt()):
            entry_position = reader.readInt()
            entry_value = entry[4+28*entry_position:4+28*entry_position+28]
            entry_value = entry_value[8]^entry_value[9]<<8
        table.append([key_value, entry_value])
    for i in range(len(table)):
        if table[i][1] != 65535:
            table[i][1] = table[table[i][1]][0]
    for i in range(len(table) - 1, -1, -1):
        if type(table[i][0]) == int or table[i][0][:15] == "Assets/Tracks/#" or table[i][0][:14] != "Assets/Tracks/" and table[i][0][:7] != "avatar.":
            del table[i]
        elif table[i][0][:14] == "Assets/Tracks/":
            table[i][0] = table[i][0][14:]
    for key, value in table:
        print(key, value)

    print("#2")

    thread = threading.Thread(target=io)
    thread.start()
    ti = time.time()
    global pool
    with ThreadPoolExecutor(6) as pool:
        with ZipFile(path) as apk:
            size = 0
            l = [apk]
            for key, entry in table:
                l.append((key, entry))
                info = apk.getinfo("assets/aa/Android/%s" % entry)
                size += info.file_size
                # print('size:', size)
                '''if size > 32 * 1024 * 1024:
                    queue_in.put(l)
                    env = queue_out.get()
                    for ikey, ientry in env.files.items():
                        save(ikey,ientry)
                    size = 0
                    del env
                    gc.collect()
                    l = [apk]'''
            queue_in.put(l)
            env = queue_out.get()
            for ikey, ientry in env.files.items():
                save(ikey,ientry)
    queue_in.put(None)
    thread.join()
    print("%f秒" % round(time.time() - ti, 4))

if __name__=="__main__":
    run(sys.argv[1], {
        "Chart": 1,
        "IllustrationBlur": 0,# 用不到还没做完(新手教程的)
        "IllustrationLowRes": 0,# 反正先别开
        "Illustration": 1,
        "music": 1,
        "avatar": 0
    })
