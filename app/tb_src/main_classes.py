import selenium
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
import time
import os
import threading
import pprint
import sys
from pymongo import MongoClient
from telebot.types import *
import undetected_chromedriver as uc

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from tb_src.usefull_functions import *
from f_src.chrome_driver import *




class uc_class(uc.Chrome):

    def __init__(self):

        self._temp_dict = {}
        self._cola = {}

        o = uc.ChromeOptions()
        
        o.add_experimental_option(
            "prefs", {
                "credentials_enable_service": False,
                "profile.password_manager_enabled" : False
            }
        )

        if os.name != "nt":
            o = anadir_opciones(o, container=True , mobile=True)

            super().__init__(
                options=o,
                log_level=3,
                keep_alive=True,
                driver_executable_path='/usr/lib/chromium/chromedriver')

        else:
            o = anadir_opciones(o, mobile=True)
            super().__init__(
                options=o,
                log_level=3,
                keep_alive=True,
                driver_executable_path=r'D:\Programacion\Proyectos personales\webscrapping\chromedriver-win64\chromedriver.exe')



        self.set_window_rect(height=851, width=450)
        self.set_window_position(x=0, y=0)

            


    def __existe(self):
        if not self._cola["uso"]:
            raise Exception("no")

        elif self._temp_dict.get(self._cola["uso"]):
            if self._temp_dict[self._cola["uso"]].get("cancelar") or self._temp_dict[self._cola["uso"]].get("cancelar_forzoso"):
                raise Exception("no")

        return "ok"


    def find_element(self, by=By.ID, value: Optional[str] = None) -> WebElement:
        self.__existe()

        return super().find_element(by, value)

    
    def find_elements(self, by=By.ID, value: Optional[str] = None) -> list[WebElement]:
        self.__existe()

        return super().find_elements(by, value)


    @property
    def cola(self):
        return self._cola


    @cola.getter
    def cola(self):
        return self._cola


    @property
    def temp_dict(self):
        return self._temp_dict

    @temp_dict.getter
    def temp_dict(self):
        return self._temp_dict







class scrapping():

    def __init__(self, iniciar_web=True):

        self._temp_dict = {}
        self._cola = {"uso": False, "cola_usuarios": []}
        self.delay = 60
        self.entrada = Entrada(True)
        self.interrupcion = False
        self.admin = None
        self.usuarios_permitidos = []

        if iniciar_web:

            self.driver = uc_class()

            if os.name == "nt":
                self.wait = WebDriverWait(self.driver, 80)
            else:
                self.wait = WebDriverWait(self.driver, 30)

            self.wait_s = WebDriverWait(self.driver, 8)


        

        if not "MONGO_URL" in os.environ:
            self.MONGO_URL = "mongodb://localhost:27017"
        else:
            self.MONGO_URL = os.environ["MONGO_URL"]

        self.cliente = MongoClient(self.MONGO_URL)
        self.db = self.cliente["face"]


        self.collection = self.db["usuarios"] 
        
        #Para tener mas detalles de la estructura de la base de datos consulte el archivo: "../BD structure.txt"

        #----------------------------------------------------------------

        return




    @property
    def cola(self):
        return self._cola


    @cola.setter
    def cola(self, value):
        self._cola = value
        self.driver._cola = value

        return

    @cola.getter
    def cola(self):
        return self._cola


    @property
    def temp_dict(self):
        return self._temp_dict


    @temp_dict.setter
    def temp_dict(self, value):
        self._temp_dict = value
        self.driver._temp_dict = value

        return

    @temp_dict.getter
    def temp_dict(self):
        return self._temp_dict

    
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
        
        
        if res.get("_temp_dict"):
        
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
            
            
            return limpiar_objetos(res, dic=res["_temp_dict"], key="root")

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

    def limpiar_usuarios(self, scrapper, bot = False, excepciones=[]):

        if bot:
            self.contrasena = True
            self.caducidad = False

        copia_usuarios = self.usuarios_permitidos.copy()

        for i in copia_usuarios:
            if not i in excepciones:

                if bot:
                    if not scrapper.cola["uso"] == i:
                        
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


