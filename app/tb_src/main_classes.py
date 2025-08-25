from selenium.webdriver.support.ui import WebDriverWait
import time
import os
import threading
import pprint
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from .usefull_functions import *
from f_src.chrome_driver import uc_driver





class scrapper:

    driver = uc_driver(True)
    
    if os.name == "nt":
        wait = WebDriverWait(driver, 80)
    else:
        wait = WebDriverWait(driver, 30)

    wait_s = WebDriverWait(driver, 8)
    temp_dict = {}
    cola = {"uso": False, "cola_usuarios": []}
    delay = 60
    password = True
    admin = None
    usuarios_permitidos = []
    

    def show(self, user):
        pprint.pprint(self.temp_dict[user], sort_dicts=False)

    def __str__(self):
        return """
dict cola: {}
dict temp_dict: {}
var delay: {}
var password: {}
var admin: {}
list usuarios_permitidos: {}
""".format(

    "Usuario actual: <code>" + str(self.cola["uso"]) + "</code> | Usuarios en espera: " + ", ".join(["<code>" + str(i) + "</code>" for i in self.cola["cola_usuarios"]]) if self.cola["cola_usuarios"] else "Usuario actual <code>" + str(self.cola["uso"]) + "</code> | " + "Actualmente no hay usuarios en cola",
    "\n".join(self.temp_dict), 
    self.delay,
    self.password,
    self.admin,
    self.usuarios_permitidos

    )



class Usuario:

    def __init__(self, telegram_id):
        self.id = time.time()
        self.telegram_id = telegram_id
        self.folder = user_folder(telegram_id)
        self.publicaciones: list[Publicacion] = None
        self.cookies: list[Cookies] = None
        self.temp_dict = {}
        


    def __setattr__(self, name, value):
        self[name] = value

class Cookies:

    def __init__(self, id_usuario, cookies_list, cookies_path):
        self.cookies_dict = cookies_list
        self.id_usuario = id_usuario
        self.cookies_path = cookies_path
        self.cuentas = []



class Publicacion:

    def __init__(self, id_usuario: int):
        self.id_usuario = id_usuario
        self.id_publicacion = False
        self.texto = False
        self.adjuntos = []
        self.titulo = False




class MediaGroupCollector:

    def __init__(self, user_id, telegram_id):
        self.user_id = user_id
        self.telegram_id = telegram_id
        self.timer = None
        self.fotos = []
        self.TIMEOUT = 8


