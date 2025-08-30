from tb_src.main_classes import scrapping as s
from tb_src.usefull_functions import *
import dill
import tempfile
import os

scrapper = s(iniciar_web = False)



def leer_BD(scrapper = False):
    if scrapper:
        print(dill.loads(scrapper.collection.find_one({"_id": "telegram_bot"})["cookies"])["scrapper"])
    else:
        with open(os.path.join(tempfile.tempdir, "bot_cookies.pkl"), "rb") as f:
            f.seek(0)
            print(dill.loads(f.read())["scrapper"])

    return

breakpoint()

print("hola")




