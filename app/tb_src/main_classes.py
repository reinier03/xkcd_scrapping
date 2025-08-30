import selenium
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
import time
import os
import threading
import pprint
import sys
from pymongo import MongoClient
from seleniumbase.core.sb_driver import WebDriver
from telebot.types import *



sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from tb_src.usefull_functions import *
from f_src.chrome_driver import uc_driver





class scrapping:

    def __init__(self, iniciar_web=True):


        if iniciar_web:
            self.__iniciar()


        if not "MONGO_URL" in os.environ:
            self.MONGO_URL = "mongodb://localhost:27017"
        else:
            self.MONGO_URL = os.environ["MONGO_URL"]

        self.cliente = MongoClient(self.MONGO_URL)
        self.db = self.cliente["face"]


        self.collection = self.db["usuarios"] 
        
        #Para tener mas detalles de la estructura de la base de datos consulte el archivo: "../BD structure.txt"

        #----------------------------------------------------------------
        

        self.temp_dict = {}
        self.cola = {"uso": False, "cola_usuarios": []}
        self.delay = 60
        self.entrada = Entrada(True)
        self.interrupcion = False
        self.admin = None
        self.usuarios_permitidos = []

        return
    
    def __str__(self):
        texto = "Clase |<b>scrapping</b>| variables:\n\n"

        for k, v in self.__dict__.items():
            texto += "scrapping.<b>{}</b>  =>  {}\n".format(k, v)
        
        return texto


    def __getstate__(self):
        res = dict(self.__dict__.copy()).copy()
        
        # Eliminar TODOS los objetos no serializables
        elementos_a_eliminar = [
            "driver", "wait", "wait_s", 
            "collection", "db", "cliente"  # ← ¡MongoDB también tiene sockets!
        ]
        
        for elemento in elementos_a_eliminar:
            if elemento in res.keys():
                del res[elemento]
        
        
        if res.get("temp_dict"):
        
            def es_objeto_selenium(obj):
                """Detecta si es un objeto de Selenium o similar"""
                if obj is None:
                    return False

                # elif isinstance(obj, (WebDriver, WebElement, ActionChains, WebDriverWait)):
                #     return True

                clase_name = obj.__class__.__name__
                modulo_name = obj.__class__.__module__

                if (clase_name in ['WebElement', 'ActionChains', 'WebDriver'] or 'selenium' in str(modulo_name) or 'undetected_chromedriver' in str(modulo_name)):
                    return True
            
            def limpiar_objetos(obj, **kwargs):
                
                if kwargs["key"] == "lista_grupos" or es_objeto_selenium(obj):
                    return None
                elif isinstance(obj, dict):
                    return {k: limpiar_objetos(v, dic=kwargs.get("dic"), key=k) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [limpiar_objetos(item, dic=kwargs.get("dic"), key=obj) for item in obj]
                elif isinstance(obj, tuple):
                    return tuple(limpiar_objetos(item , dic=kwargs.get("dic"), key=obj) for item in obj)
                else:
                    return obj
            
            
            return limpiar_objetos(res, dic=res["temp_dict"], key="root")

        return res
        
        
        
    
    def __setstate__(self, state):
        # Restaurar el estado básico primero
        self.__dict__.update(state)
        
        # Reconstruir la conexión de MongoDB
        if not hasattr(self, 'MONGO_URL'):
            if not "MONGO_URL" in os.environ:
                self.MONGO_URL = "mongodb://localhost:27017"
            else:
                self.MONGO_URL = os.environ["MONGO_URL"]
        
        self.cliente = MongoClient(self.MONGO_URL)
        self.db = self.cliente["face"]
        self.collection = self.db["usuarios"]

        return
        


    
    
    def __iniciar(self):
        self.driver = uc_driver(True)

        if os.name == "nt":
            self.wait = WebDriverWait(self.driver, 80)
        else:
            self.wait = WebDriverWait(self.driver, 30)

        self.wait_s = WebDriverWait(self.driver, 8)

        return

    
    
    

    def show(self, user):
        pprint.pprint(self.temp_dict[user], sort_dicts=False)

    



class Entrada():
    def __init__(self, contrasena):
        """
        Clase para administrar el metodo de entrada al bot

        Si self.contrasena = False entonces todo el mundo podrá acceder al bot
        Si self.contrasena = True entonces NADIE podria acceder excepto los que estan en self.usuarios_permitidos: list
        """
        self.contrasena = contrasena 
        self.caducidad = False
        self.usuarios_permitidos = []
        self.usuarios_permitidos_permanente = []


    def __str__(self):
        texto = "Clase |Entrada| variables:\n\n"
        for k, v in self.__dict__.items():
            texto += "Entrada.<b>{}</b>  =>  {}\n".format(k, v)

        return texto

    def limpiar_usuarios(self, bot = False, excepciones=[]):

        if bot:
            self.contrasena = True
            self.caducidad = False

        copia_usuarios = self.usuarios_permitidos.copy()

        for i in copia_usuarios:
            if not i in excepciones:

                if bot:

                    try:
                        bot.send_message(i, m_texto("Mi administrador ha bloqueado el acceso, no podrás usarme más hasta nuevo aviso...\n\nContacta con él si tienes alguna queja"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👮‍♂️ Contacta con el admin", url="https://t.me/{}".format(bot.get_chat(int(os.environ["admin"])).username))]]))
                    except:
                        pass

                self.usuarios_permitidos.remove(i)

        return

    

        

        

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


