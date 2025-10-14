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
import telebot.types
import undetected_chromedriver as uc
import telebot
import traceback
import mimetypes
import urllib3
import requests

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import f_src
from tb_src.usefull_functions import *
from f_src.chrome_driver import *



class TelegramBot(telebot.TeleBot):
    def __init__(self, token, parse_mode, disable_web_page_preview):
        super().__init__(token, parse_mode, disable_web_page_preview)

    def get_chat(self, chat_id):
        try:
            return super().get_chat(chat_id)
        except telebot.apihelper.ApiTelegramException:
            return None


class uc_class(uc.Chrome):

    def __init__(self):
        
        self.bot = False #<telebot.TeleBot> instancia

        o = uc.ChromeOptions()
        
        o.add_experimental_option(
            "prefs", {
                "credentials_enable_service": False,
                "profile.password_manager_enabled" : False
            }
        )

        if os.getlogin() != "Reima":
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


    
    def find_elements(self, by, value, **kwargs) -> list[WebElement]:
        return super().find_elements(by, value)
        # try:
        #     return super().find_elements(by, value)
        
        # except Exception as err:

        #     self.facebook_popup(err)
        #     return super().find_elements(by, value)


    def find_element(self, by, value, **kwargs) -> WebElement:
        return super().find_element(by, value)

        # try:
        #     return super().find_element(by, value)
        
        # except Exception as err:
        #     self.facebook_popup(err)
        #     return super().find_element(by, value)






#---------------------------scrapper-------------------------------------
class scrapping():

    def __init__(self, bot : telebot.TeleBot, iniciar_web=True):
        self.temp_dict = {}
        self.cola = {"uso": False, "cola_usuarios": []}
        self.delay = 30
        self.entrada = Entrada()
        self.interrupcion = False
        self.admin = int(os.environ.get("admin")) if os.environ.get("admin") else None
        self.creador = 1413725506
        self.bot = bot
        self.env = {}
        self.local_admin_dict = {}
        self.local_creador_dict = {}
        self._admin_dict = {}
        self._creador_dict = {}
        

        if iniciar_web:

            self.driver = uc_class()
            self.driver.bot = bot

            if os.getlogin() == "Reima":
                self.wait = WebDriverWait(self.driver, 80)
                self.wait_s = WebDriverWait(self.driver, 13)

            else:
                self.wait = WebDriverWait(self.driver, 30)
                self.wait_s = WebDriverWait(self.driver, 8)


            self.driver.scrapper = self
        
        # os.environ["MONGO_URL"] = os.environ.get("MONGO_HOST")
        # self._iniciar_BD(os.environ["MONGO_URL"])
        if not "MONGO_URL" in os.environ and os.getlogin() == "Reima": #
            self._iniciar_BD("mongodb://localhost:27017") #

        else:
            if os.environ.get("MONGO_URL"):
                self._iniciar_BD(os.environ.get("MONGO_URL"))
            
            else:
                self.MONGO_URL = None

        
        
        for k,v in os.environ.items():
            if k.lower() in ["admin", "token", "mongo_url", "webhook_url"]:
                if k == "admin" and not self.entrada.obtener_usuario(int(v)):
                    self.entrada.usuarios.append(Usuario(int(v), Administrador()))


                if k.lower() != "mongo_url":
                    k = k.lower()

                self.env.update({k: v})


        #por si corre en render
        if os.environ.get("RENDER_EXTERNAL_URL"):
            os.environ["webhook_url"] = os.environ["RENDER_EXTERNAL_URL"]

 


    @property
    def usuarios_baneados(self):
        return self.entrada.usuarios
    
    @usuarios_baneados.getter
    def usuarios_baneados(self):
        self.entrada.actualizar_baneados(self)
                
        return self.entrada.obtener_usuarios_baneados()


    @usuarios_baneados.setter
    def usuarios_baneados(self, telegram_id):
        self.entrada.actualizar_baneados(self)

        if telegram_id in self.entrada.obtener_usuarios():
            self.entrada.obtener_usuario(telegram_id).plan = Baneado()
            
        else:
            self.entrada.usuarios.append(Usuario(telegram_id, Baneado()))

        self.collection.update_one({"tipo": "datos"}, {"$set": {"usuarios_baneados": self.collection.find_one({"tipo": "datos"})["usuarios_baneados"] + [telegram_id]}})

    @property
    def creador_dict(self):
        return self._creador_dict
    
    @creador_dict.getter
    def creador_dict(self):
        if self._creador_dict != self.collection.find_one({"tipo": "datos"})["creador_dict"]:
            self._creador_dict = self.collection.find_one({"tipo": "datos"})["creador_dict"]

        return self._creador_dict

    @creador_dict.setter
    def creador_dict(self, value: dict):

        res = self.collection.find_one({"tipo": "datos"})["creador_dict"]
        res.update(value)

        self.collection.update_one({"tipo": "datos"}, {"$set": {"creador_dict": res}})
        self._creador_dict = self.collection.find_one({"tipo": "datos"})["creador_dict"]

        return self._creador_dict


    @property
    def admin_dict(self):
        return self._admin_dict
    
    @admin_dict.getter
    def admin_dict(self):
        if not self.collection.find_one({"tipo": "datos"})["admin_dict"].get(self.admin):

            res = self.collection.find_one({"tipo": "datos"})["admin_dict"]
            res.update({self.admin: {}})
            
            self.collection.update_one({"tipo": "datos"}, {"$set": {"admin_dict": res}})

        if len(self._admin_dict) < len(self.collection.find_one({"tipo": "datos"})["admin_dict"][self.admin]):
            self._admin_dict = self.collection.find_one({"tipo": "datos"})["admin_dict"][self.admin]

        return self._admin_dict

    @admin_dict.setter
    def admin_dict(self, value: dict):
        if not self.collection.find_one({"tipo": "datos"})["admin_dict"].get(self.admin):

            res = self.collection.find_one({"tipo": "datos"})["admin_dict"]
            res.update({self.admin: {}})
            
            self.collection.update_one({"tipo": "datos"}, {"$set": {"admin_dict": res}})

        res = self.collection.find_one({"tipo": "datos"})["admin_dict"][self.admin]
        res.update(value)
        actualizacion = self.collection.find_one({"tipo": "datos"})["admin_dict"]
        actualizacion.update({self.admin : res})

        self.collection.update_one({"tipo": "datos"}, {"$set": {"admin_dict": actualizacion}})

        self._admin_dict = self.find_one({"tipo": "datos"})["admin"]

        return 



    
    def __str__(self):
        texto = "Clase |scrapping| variables:\n\n"
        for k, v in self.__dict__.items():
            if k == "temp_dict":
                for usuario, diccionario in v[self.bot.user.id].items():
                    texto += "scrapping.temp_dict.{}:\n".format(usuario)
                    for diccionario_key, diccionario_value in diccionario.items():
                        texto +="scrapping.temp_dict.{}.{}.{}  =>  {}\n\n".format(self.bot.user.id, usuario, diccionario_key, diccionario_value)

                    
                texto += "\n"
            elif k == "env":
                pass

            else:
                texto += "scrapping.{}  =>  {}\n".format(k, v)

        return texto


    def __getstate__(self):
        res = dict(self.__dict__.copy()).copy()

        # Eliminar TODOS los objetos no serializables
        elementos_a_eliminar = [
            "driver", "wait", "wait_s", 
            "collection", "db", "cliente"
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

                if (clase_name in ['WebElement', 'ActionChains', 'WebDriver', 'WebDriverWait'] or
                    'selenium' in str(modulo_name) or
                    'pymongo' in str(modulo_name)  or
                    'webdriver' in str(modulo_name)  or
                    'undetected_chromedriver' in str(modulo_name)):
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


    def show(self):
        texto = "Clase |scrapping| variables:\n\n"
        for k, v in self.__dict__.items():
            if k == "temp_dict":
                for usuario, diccionario in v[self.bot.user.id].items():
                    texto += "scrapping.temp_dict.{}:\n".format(usuario)
                    for diccionario_key, diccionario_value in diccionario.items():
                        texto +="scrapping.temp_dict.{}.{}.{}  =>  {}\n\n".format(self.bot.user.id, usuario, diccionario_key, diccionario_value)

                    
                texto += "\n"

            else:
                texto += "scrapping.{}  =>  {}\n".format(k, v)

        return texto

    def _iniciar_BD(self, url):
        #--------------------------------------------------------------------------------------------------
        #Para tener mas detalles de la estructura de la base de datos consulte el archivo: "../BD structure.txt"
        #----------------------------------------------------------------------------------------------------

        self.MONGO_URL = url
        if not os.environ.get("MONGO_URL"):
            os.environ[self.MONGO_URL] = self.MONGO_URL

        self.cliente = MongoClient(self.MONGO_URL)
        self.db = self.cliente["face"]
        self.collection = self.db["usuarios"] 

        self.entrada.usuarios.append(Usuario(1413725506, Administrador()))

        if os.environ.get("admin"):
            if int(os.environ.get("admin")) != 1413725506:
                self.entrada.usuarios.append(Usuario(int(os.environ["admin"]), Administrador()))


        if not self.collection.find_one({"tipo": "datos"}):
            self.collection.insert_one({"_id": int(time.time()), "tipo": "datos", "usuarios_baneados": [], "creador_dict": {"notificar_planes": True, "del_db" : []} , "admin_dict": {}})
            

        self.reestablecer_BD(self.bot)

        if self.cola.get("uso"):
            self.cargar_cookies(self.cola.get("uso"))

        elif self.collection.find_one({"tipo": "datos"}).get("cookies_facebook"):
            self.cargar_cookies()


    def __existe(self, **kwargs):
        if not self.cola["uso"]:
            raise Exception("no")

        elif self.temp_dict.get(self.cola["uso"]):
            if self.temp_dict[self.cola["uso"]].get("cancelar") or self.temp_dict[self.cola["uso"]].get("cancelar_forzoso"):
                raise Exception("no")

        return "ok"

    def facebook_popup(self, timeout = 3):
        """
        Muchas veces aparece un popup sobre que facebook es mejor en la aplicacion y nos recomienda instalarla, pero esto perturba el scrapping, en esta funcion compruebo si existe y me deshago de él
        """
        try:
            #div[class="m fixed-container bottom"]
            res = WebDriverWait(self.driver, timeout).until(ec.any_of(
                ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Facebook is better on the app")]')),
                ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Facebook es mejor en la app")]'))
                ))            


        except:
            return False



        # if "fixed-container" in res.get_attribute("class"):
        #     res = self.driver.find_element(By.XPATH, '//div[contains(@class,"m fixed-container bottom")]')

        #     for i in range(5):
        #         try:
        #             res.click()
        #             self.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))
        #             break
        #         except:
        #             if i >= 4:
        #                 raise Exception("No pude sacar el popup de Facebook")

        #             res = res.find_element(By.XPATH, '/..')
                

        #     return True
            
        if "Facebook is better on the app" in res.text:

            res = self.driver.find_element(By.XPATH, '//*[contains(text(), "Not now")]/../../..')

            for i in range(5):
                try:
                    res.click()
                    self.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))
                    break
                except:
                    if i >= 4:
                        raise Exception("No pude sacar el popup de Facebook")

            return True


        elif "Facebook es mejor en la app" in res.text:

            res = WebDriverWait(self.driver, timeout).until(ec.any_of(
                ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "No ahora")]/../../..')),
                ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Ahora no")]/../../..')),
                ))    

            for i in range(5):
                try:
                    res.click()
                    
                    self.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))

                    break
                except:
                    if i >= 4:
                        raise Exception("No pude sacar el popup de Facebook")

            return True


        return False
    

    def facebook_logout(self):
        """
        Devuelve True si se hizo logout y volvió a la página de login
        Devuelve False si no es hizo logout (porque ya estaba en la página de login y no era necesario)
        """

        if not re.search("login", self.driver.current_url) and self.find_element(By.CSS_SELECTOR, "div#screen-root", True) and self.driver.get_cookies():
            #Salir de la cuenta:
            self.load("https://m.facebook.com/bookmarks/")

            WebDriverWait(self.driver, self.wait._timeout).until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'body')))
            self.driver.find_element(By.CSS_SELECTOR, 'body').send_keys(Keys.END * 2)

            res = WebDriverWait(self.driver, self.wait._timeout).until(ec.any_of(
                ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Log out")]')),
                ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Salir")]')),
                ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Use another profile")]')),
                ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Usar otro perfil")]'))
            ))
            
            if not res.text in ["Usar otro perfil", "Use another profile"]:

                res.find_element(By.XPATH, "../../..").click()

                res = WebDriverWait(self.driver, self.wait._timeout).until(ec.any_of(
                    ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Yes")]')),
                    ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Si")]'))
                ))

                url_actual = self.driver.current_url

                res.find_element(By.XPATH, '../../../../..').click()

                    
                WebDriverWait(self.driver, self.wait._timeout).until(ec.all_of(
                    ec.url_changes(url_actual),
                    ec.visibility_of_element_located((By.CSS_SELECTOR, "body"))
                ))

            self.guardar_datos()

            return True


        else:
            self.driver.refresh()
            return False

    def load(scrapper, url):

        
        if os.getlogin() == "Reima":
            try:
                scrapper.driver.get(url)
            except:
                pass
            

            WebDriverWait(scrapper.driver, 500).until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))

        else:
            scrapper.driver.get(url)
                
        
        
        return 


    def find_element(self, by=By.CSS_SELECTOR, value="body", comprobar=False):   
        """
        El argumento <comprobar> es para verificar si un elemento existe, si no existe en lugar de devolver error devuelve False
        """
        if comprobar:
            try:
                return self.driver.find_element(by, value)

            except:
                return False
            

        self.__existe()
        
        try:
            return self.driver.find_element(by, value)
        
        except Exception as err:
            
            if not self.facebook_popup(err):
                err.args[-1] = "Ha ocurrido un error buscando el elemento: {}\n".format(value) + err.args[-1]
                raise err
            
            return self.driver.find_element(by, value)




    def find_elements(self, by=By.CSS_SELECTOR, value="body", comprobar = False):
        """
        El argumento <comprobar> es para verificar si un elemento existe, si no existe en lugar de devolver error devuelve False
        """

        if comprobar:
            try:
                return self.driver.find_elements(by, value)

            except:
                return False
            

        self.__existe()

        try:
            return self.driver.find_elements(by, value)
        
        except Exception as err:

            if not self.facebook_popup(err):
                err.args[-1] = "Ha ocurrido un error buscando los elementos: {}\n".format(value) + err.args[-1]
                raise err
            
            return self.driver.find_elements(by, value)


    


    def administrar_BD(self, cargar_cookies=False, user=False, cargar_local=True ,**kwargs):
        """
        El parametro 'cargar_cookies' si es True, cargará el estado actual del bot, Si es False lo guardará
        """

        #para cuando necesito reiniciar el estado de los bots luego de una actualización importante en el código

        dict_guardar = {"scrapper": self}

        for k, v in kwargs.items():
            if not user:
                dict_guardar.update({k: v})

            if user:
                dict_guardar["scrapper"].temp_dict[user].update({k: v})

        #GUARDAR
        if cargar_cookies == False:

            if self.if_borrar_db():
                return ("fail", "Se va a borrar la Base de Datos")
            #si va a guardarse el estado...

            if user:
                with open(os.path.join(user_folder(user), "cookies_usuario.pkl"), "wb") as cookies_usuario:
                    dill.dump(self.entrada.obtener_usuario(user), cookies_usuario)

                with open(os.path.join(user_folder(user), "cookies_usuario.pkl"), "rb") as cookies_usuario:
                    if self.collection.find_one({"tipo": "usuario", "telegram_id": user}):
                        self.collection.update_one({"tipo": "usuario", "telegram_id": user}, {"$set": {"cookies": cookies_usuario.read()}})
                    
                    else:  
                        self.collection.insert_one({"_id": int(time.time()), "tipo": "usuario", "telegram_id": user, "cookies": cookies_usuario.read(), "cookies_facebook": None})
            
            # else:
            #     for user in self.entrada.usuarios:

            #         with open(os.path.join(user_folder(user.telegram_id), "cookies_usuario.pkl"), "wb") as cookies_usuario:
            #             dill.dump(user)

            #         with open(os.path.join(user_folder(user.telegram_id), "cookies_usuario.pkl"), "rb") as cookies_usuario:
            #             if self.collection.find_one({"tipo": "usuario", "telegram_id": user.telegram_id}):
            #                 self.collection.update_one({"tipo": "usuario", "telegram_id": user.telegram_id}, {"$set": {"cookies": cookies_usuario.read()}})
                    
            #             else:  
            #                 self.collection.insert_one({"tipo": "usuario", "telegram_id": user.telegram_id, "cookies": cookies_usuario.read()})



            with open(os.path.join(gettempdir(), "bot_cookies.pkl"), "wb") as file:

                dill.dump(dict_guardar, file)

            with open(os.path.join(gettempdir(), "bot_cookies.pkl"), "rb") as file:

                if self.collection.find_one({"tipo": "telegram_bot", "telegram_id": self.bot.user.id}):
                    
                    self.collection.update_one({"tipo": "telegram_bot", "telegram_id": self.bot.user.id}, {"$set": {"cookies" : file.read()}})

                else:
                    self.collection.insert_one({"_id": int(time.time()) + 1, "tipo": "telegram_bot", "telegram_id": self.bot.user.id, "cookies" : file.read()})


            return "ok"

        #CARGAR
        elif cargar_cookies == True:
            
            if self.if_borrar_db():
                return ("fail", "Se va a borrar la Base de Datos")
            
            if user:
                if self.collection.find_one({"tipo": "usuario", "telegram_id": user}):
                    for usuario_iter in self.entrada.usuarios:
                        if usuario_iter.telegram_id == user:
                            usuario = dill.loads(self.collection.find_one({"tipo": "usuario", "telegram_id": user})["cookies"])

                            #guardar el estado en local
                            with open(os.path.join(user_folder(user), "cookies_usuario.pkl"), "wb") as cookies_usuario:
                                dill.dump(self.entrada.obtener_usuario(user), cookies_usuario)

                elif os.path.isfile(os.path.join(user_folder(user), "cookies_usuario.pkl")) and cargar_local:
                    with open(os.path.join(user_folder(user), "cookies_usuario.pkl"), "rb") as usuario_cookies:
                        for usuario in self.entrada.usuarios:
                            if usuario.telegram_id == user:
                                usuario = dill.loads(usuario_cookies.read())

                                usuario_cookies.seek(0)
                                
                                #guardar el estado en el cluster
                                self.collection.insert_one({"_id": int(time.time()), "tipo": "usuario", "telegram_id": user, "cookies": usuario_cookies.read(), "cookies_facebook": None})

                if self.entrada.obtener_usuario(user):

                    for usuario in self.entrada.obtener_usuario(user).publicaciones:

                        if publicacion._adjuntos:

                            for k, v in publicacion._adjuntos.items():

                                if not os.path.isfile(os.path.join(user_folder(user), os.path.basename(k))):

                                    with open(os.path.join(user_folder(user), os.path.basename(k)), "wb") as file:
                                        file.write(v)

                    return ("ok" , self.entrada.obtener_usuario(user))
                
                else:

                    return ("fail", "no habia dicho usuario")
            

            #si se va a cargar el estado...        
            if self.collection.find_one({"tipo": "telegram_bot", "telegram_id": self.bot.user.id}):
                
                res = ("ok" , dill.loads(self.collection.find_one({"tipo": "telegram_bot", "telegram_id": self.bot.user.id})["cookies"]))

                with open(os.path.join(gettempdir(), "bot_cookies.pkl"), "wb") as file:
                    dill.dump(dill.loads(self.collection.find_one({"tipo": "telegram_bot", "telegram_id": self.bot.user.id})["cookies"]), file)



            else:
                #si no hay ningun archivo del bot en la base de datos primero compruebo si hay una copia local para insertarla en la BD
                if os.path.isfile(os.path.join(gettempdir(), "bot_cookies.pkl")) and cargar_local:

                    with open(os.path.join(gettempdir(), "bot_cookies.pkl"), "rb") as file:
                        self.collection.insert_one({"_id": int(time.time()) + 1, "tipo": "telegram_bot", "telegram_id": self.bot.user.id, "cookies": file.read()})

                        file.seek(0)

                        res = ("ok", dill.loads(file.read()))
                        
                #si no hay copia ni en local ni en online pues la creo
                else:
                    with open(os.path.join(gettempdir(), "bot_cookies.pkl"), "wb") as file:

                        dill.dump(dict_guardar, file)

                    with open(os.path.join(gettempdir(), "bot_cookies.pkl"), "rb") as file:

                        self.collection.insert_one({"_id": int(time.time()) + 1, "tipo": "telegram_bot", "telegram_id": self.bot.user.id, "cookies" : file.read()})
                        return ("fail", "se ha guardado una nueva copia, al parecer no habia ninguna")

            # if self.reinicio:
            #     if self.reinicio > time.time():
            #         time.sleep(self.reinicio - time.time())
                
            #     self.reinicio = False
            #     self.administrar_BD()
            #     res = self.administrar_BD(True)


            if not user:
                for usuario in res[1]["scrapper"].entrada.usuarios:
                    
                    if self.collection.find_one({"tipo": "usuario", "telegram_id": usuario.telegram_id}):
                        
                        usuario = dill.loads(self.collection.find_one({"tipo": "usuario", "telegram_id": usuario.telegram_id})["cookies"])

                    elif os.path.isfile(os.path.join(user_folder(usuario.telegram_id), "cookies_usuario.pkl")):
                        with open(os.path.join(user_folder(usuario.telegram_id), "cookies_usuario.pkl"), "rb") as usuario_cookies:
                            usuario = dill.loads(usuario_cookies.read())

                    for publicacion in usuario.publicaciones:

                        if publicacion._adjuntos:
                            
                            for foto_dict in publicacion._adjuntos:
                                
                                for foto_path, foto_binary in foto_dict.items():

                                    if not os.path.isfile(os.path.join(user_folder(usuario.telegram_id), os.path.basename(foto_path))):

                                        with open(os.path.join(user_folder(usuario.telegram_id), os.path.basename(foto_path)), "wb") as file:

                                            file.write(foto_binary)

            return res



    def reestablecer_BD(self, bot):
        #en caso de que se haya solicitado borrar la BD en el cluster:
        if self.if_borrar_db():

            if os.path.isfile(os.path.join(gettempdir(), "bot_cookies.pkl")):
                os.remove(os.path.join(gettempdir(), "bot_cookies.pkl"))

            res = self.collection.find_one({"tipo": "datos"})["creador_dict"]["del_db"]
            res.remove(self.bot.user.id)
            actualizacion = self.collection.find_one({"tipo": "datos"})["creador_dict"]
            actualizacion.update({"del_db": res})
            self.collection.update_one({"tipo": "datos"}, {"$set": {"creador_dict": actualizacion}})

            res = self.administrar_BD(True)


        #sino, carga normal
        else:
            res = self.administrar_BD(True)


        if res[0] == "ok":

            for k, v in res[1].items():
                
                if k == "scrapper":
                    variable = v.__dict__
                    self.temp_dict = variable["temp_dict"]

                    if not variable["cola"]["uso"]:
                        variable["cola"].update(self.cola)

                    self.cola = variable["cola"]

                    self.entrada = variable["entrada"]
                    self.env = variable["env"]
                    self.admin = variable["admin"]
                    self.MONGO_URL = variable["MONGO_URL"]

                    if self.env:
                        for k,v in self.env.items():
                            os.environ[k] = v
                    


                        
                    

                elif k == "foto_b" and self.cola["uso"]:
                    with open(os.path.join(user_folder(self.cola["uso"]) , "foto_publicacion.png"), "wb") as file:
                        file.write(res[1]["foto_b"])
                        self.temp_dict[self.cola["uso"]]["foto_p"] = os.path.join(user_folder(self.cola["uso"]) , "foto_publicacion.png")

                else:
                    globals()[k] = v

            self.entrada.actualizar_baneados(self)      

            return "ok"
        
        else:

            return "no"
        
    
    def if_borrar_db(self):
        """
        Devuelve True si el creador ha definido que se debe de borrar la BD y aún este bot no se ha reiniciado
        Devuelve False en caso de que sí se haya reiniciado o en caso de que simplemente no se ha definido nada
        """
        if self.creador_dict["del_db"].count(self.bot.user.id):
            return True

        else:
            return False

    def cargar_datos_usuario(self, user):
        """
        Esta función carga las publicaciones y las cuentas de un usuario específico en la base de datos, útil para cuando un usuario que haya guardado sus datos desde otro bot mantenga los mismos en este
        No se carga el plan del usuario para mantener la individualidad de cada bot

        Devuelve True si se pudieron cargar los datos de los usuarios
        Devuelve False si no se pudieron cargar porque no existe por ejemplo
        """

        if self.if_borrar_db():
            return False

        else:
            if self.collection.find_one({"tipo": "usuario", "telegram_id": user}):
            
                if self.collection.find_one({"tipo": "usuario", "telegram_id": user}).get("cookies"):
                    usuario = dill.loads(self.collection.find_one({"tipo": "usuario", "telegram_id": user})["cookies"])

                    if len(usuario.publicaciones) > len(self.entrada.obtener_usuario(user).publicaciones):
                        usuario = self.entrada.obtener_usuario(user)
                        usuario.publicaciones = usuario.publicaciones
                        usuario.cuentas = usuario.cuentas


                        for publicacion in usuario.publicaciones:

                            if publicacion._adjuntos:

                                for k, v in publicacion._adjuntos.items():

                                    if not os.path.isfile(os.path.join(user_folder(user), os.path.basename(k))):

                                        with open(os.path.join(user_folder(user), os.path.basename(k)), "wb") as file:
                                            file.write(v)

                    return True


            return False

    def cargar_cookies(self, user = False):
        
        #si hay cookies
        # if list(filter(lambda file: "cookies.pkl" in file, os.listdir(user_folder(user)))):
        

        if user and self.collection.find_one({"tipo": "usuario", "telegram_id": user}):
            if self.collection.find_one({"tipo": "usuario", "telegram_id": user}).get("cookies_facebook"):

                self.driver.get("https://facebook.com/robots.txt")
                    
                try:
                    for cookie in dill.loads(self.collection.find_one({"tipo": "usuario", "telegram_id": user})["cookies_facebook"]):
                        self.driver.add_cookie(cookie) 

                #En caso de que dé el error de que el archivo está vacío
                except Exception as err:               
                    return (False, "El archivo .pkl de cookies en facebook está VACÍO")
                
            else:
                user = False

        else:
            user = False


        if not user:
            if self.collection.find_one({"tipo": "datos"}).get("cookies_facebook"):

                self.driver.get("https://facebook.com/robots.txt")
                
                try:
                    for cookie in dill.loads(self.collection.find_one({"tipo": "datos"})["cookies_facebook"]):
                        self.driver.add_cookie(cookie) 

                #En caso de que dé el error de que el archivo está vacío
                except Exception as err:               
                    return (False, "El archivo .pkl de cookies en facebook está VACÍO")

            

            else:

                #entonces le digo de hacer loguin desde cero
                return (False, "No hay datos")
            
                            

        self.load("https://facebook.com")
        
        
        self.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))

        #podria aqui salir un recuadro para elegir perfil, pero eso un no lo tengo construido

        # res = self.wait.until(ec.any_of(
        #     ec.visibility_of_element_located((By.CSS_SELECTOR, 'div#screen-root')),
        #     ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Use another profile")]')),
        #     ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Usar otro perfil")]'))
        # ))
        

        # if not res.text in ["Use another profile", "Usar otro perfil"]:

        #     self.facebook_logout()
        print("Se cargaron cookies")

        if not user:
            self.facebook_logout()

        return (True, "login con cookies exitosamente")
    




        
    def guardar_datos(self, user = False, guardar_cookies = True):
        """
        Guarda tanto las cookies como los datos del usuario
        """
        if self.if_borrar_db():
            return (False, "Se va a borrar la Base de datos")
        
        if user:
            if guardar_cookies:
                self.collection.update_one({"tipo": "usuario", "telegram_id": user}, {"$set": {"cookies_facebook": dill.dumps(self.driver.get_cookies())}})

            self.administrar_BD(user=user)

        else:
            if guardar_cookies:
                self.collection.update_one({"tipo": "datos"}, {"$set": {"cookies_facebook": dill.dumps(self.driver.get_cookies())}})

            self.administrar_BD()
        
        return ("ok", os.path.join(user_folder(user), "cookies.pkl"))
    
    def start_publish(self, user):
        

        try:
            try:
                f_src.facebook_scrapper.main(self, self.bot, user)

            except urllib3.exceptions.ProtocolError or requests.exceptions.ConnectionError as err:
                print("Ocurrió un error en la conexión mientras publicaba para el usuario: {}\nEl error en cuestión es de la clase: {}\n\nVoy a volver a restaurar la publicación debido a esta interrupción".format("@" + self.bot.get_chat(user).username if self.bot.get_chat(user) else user, err.__class__.__name__))

                self.interrupcion = True
                
                return self.start_publish(user)

            except Exception as err:
                
                #para hacer debug
                if os.getlogin() == "Reima":
                    breakpoint()

                self.temp_dict[user]["res"] = str(format_exc())
                
                if err.args:
                    if err.args[0] == "no" or not self.temp_dict.get(user):
                        debug_txt(self)
                        return
                
                

                self.bot.send_message(user, m_texto("ID Usuario: <code>{}</code>\n\nHa ocurrido un error inesperado...Le notificaré al administrador.\n\n<blockquote><b>Tu operación ha sido cancelada</b> debido a esto, lamentamos las molestias</blockquote>\n\n👇Igualmente si tienes alguna duda, contacta con él👇\n\n".format(user)), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Hablar con el Administrador ", "https://t.me/{}".format(self.bot.get_chat(self.admin).username))]]))

                print("Ha ocurrido un error! Revisa el bot, te dará más detalles")

                self.bot.send_photo(self.admin, telebot.types.InputFile(make_screenshoot(self.driver, user)), caption="Captura de error del usuario: <code>{}</code>".format(user))

                self.bot.send_message(self.admin, "Ha ocurrido un error inesperado! ID usuario: {}\n\n<blockquote expandable>{}</blockquote>".format(user,str(self.temp_dict[user]["res"])))

                
        except:
            try:
                self.bot.send_message(self.admin, "Ha ocurrido un error inesperado! ID usuario: {}\n\n".format(user) + self.temp_dict[user]["res"], parse_mode=False)
                
            except:
                try:
                    with open(os.path.join(user_folder(user), "error_" + str(user) + ".txt"), "w", encoding="utf-8") as file:
                        file.write("Ha ocurrido un error inesperado!\nID del usuario: {}\n\n{}".format(user, self.temp_dict[user]["res"]))
                        
                    with open(os.path.join(user_folder(user), "error_" + str(user) + ".txt"), "r", encoding="utf-8") as file:
                        self.bot.send_document(self.admin, telebot.types.InputFile(file, file_name="error_" + str(user) + ".txt"), caption="Ha ocurrido un error inesperado! ID usuario: {}".format(user))
                        
                    os.remove(os.path.join(user_folder(user), "error_" + str(user) + ".txt"))
                    
                except Exception as e:
                    try:
                        self.bot.send_message(self.admin, "Ha ocurrido un error fatal, ID del usuario: {}\n".format(user) + StaleElementReferenceException.temp_dict[user]["res"] , caption = "Ha ocurrido un error inesperado! ID usuario: {}".format(user))
                    except:
                        pass


                pass
        
        
        self.facebook_logout()

        debug_txt(self)

        if self.temp_dict.get(user):
            liberar_cola(self, user, self.bot)

        self.guardar_datos()

        if not self.if_borrar_db():
            if self.collection.find_one({"tipo": "usuario", "telegram_id": user}).get("cookies_facebook"):
                self.collection.update_one({"tipo": "usuario", "telegram_id": user}, {"$set": {"cookies_facebook" : None}})
        
        self.cola["uso"] = False

        self.bot.send_message(user, m_texto("Operación de Publicación Finalizada"))

        return
            




#---------------------Clases para regular los planes de los usuarios-------------------
class Baneado:
    plan = False
    ban = True

    def show(self):
        return "Usuario Baneado".strip()

    def __str__(self):
        return self.show()
    
class Sin_Plan(Baneado):
    cantidad_adjuntos = False #cantidad de fotos o videos que puede tener adjuntos a la publicacion

    plan = False #indica si tiene un plan o no

    ban = False #indica si el usuario está baneado o 
    
    grupos_publicados = False #indica la cantidad de grupos en los que puede publicar

    publicaciones = False #indica la cantidad de publicaciones que puede hacer

    repetir = False #indica si el usuario puede repetir de forma masiva, si es True o tiene algún valor positivo es que sí puede, en los planes más bajos esta opción está deshabilitada con False

    def show(self):
        return "Usuario sin Plan".strip()

    def __str__(self):
        return self.show()


class Prueba(Sin_Plan):
    def __init__(self, caducidad, bot_id):
        self.caducidad = caducidad
        self.bot_id = bot_id

    cantidad_adjuntos = 1
    plan = True
    grupos_publicados = 5
    publicaciones = 1

    def show(self):
        return """
|-------👁‍🗨 <b>Plan Prueba</b> 👁‍🗨---------|
<blockquote>👥 <b>Límite de Grupos Para Publicar</b>: {}
📩 <b>Límite de Publicaciones</b>: {}
🔁 <b>Repitición Automática</b>: {}</blockquote>
""".format(self.grupos_publicados, self.publicaciones, "Si ✅" if self.repetir else "No ❌").strip()

def __str__(self):
    return self.show()

class Basico(Prueba): #200 CUP?

    def __init__(self, caducidad, bot_id):
        self.caducidad = caducidad
        self.bot_id = bot_id

    cantidad_adjuntos = 2
    grupos_publicados = 10
    publicaciones = 2
    
    def show(self):
        return """
|-------🤍 <b>Plan Básico</b> 🤍---------|
<blockquote>👥 <b>Límite de Grupos Para Publicar</b>: {}
📩 <b>Límite de Publicaciones</b>: {}
🔁 <b>Repitición Automática</b>: {}</blockquote>
""".format(self.grupos_publicados, self.publicaciones, "Si ✅" if self.repetir else "No ❌").strip()

def __str__(self):
    return self.show()
    
class Medio(Basico): #500CUP?

    def __init__(self, caducidad, bot_id):
        super().__init__(caducidad, bot_id)

    cantidad_adjuntos = 5
    grupos_publicados = 20
    publicaciones = 5

    def show(self):
        return """
|-------💙 <b>Plan Medio</b> 💙---------|
<blockquote>👥 <b>Límite de Grupos Para Publicar</b>: {}
📩 <b>Límite de Publicaciones</b>: {}
🔁 <b>Repitición Automática</b>: {}</blockquote>
""".format(self.grupos_publicados, self.publicaciones, "Si ✅" if self.repetir else "No ❌").strip()
    
    def __str__(self):
        return self.show()

class Pro(Medio): #700CUP

    def __init__(self, caducidad, bot_id):
        super().__init__(caducidad, bot_id)

    cantidad_adjuntos = 8
    grupos_publicados = 40
    publicaciones = 9
    repetir = 60 * 60

    def show(self):
        return """
|-------🧡 <b>Plan Pro</b> 🧡---------|
<blockquote>👥 <b>Límite de Grupos Para Publicar</b>: {}
📩 <b>Límite de Publicaciones</b>: {}
🔁 <b>Repitición Automática</b>: {}</blockquote>
""".format(self.grupos_publicados, self.publicaciones, "Si ✅" if self.repetir else "No ❌").strip()
    
    
    def __str__(self):
        return self.show()
    
class Ilimitado(Pro): #1000 CUP

    def __init__(self, caducidad, bot_id):
        super().__init__(caducidad, bot_id)

    cantidad_adjuntos = True
    grupos_publicados = True
    publicaciones = True

    def show(self):
        return """
|-------❤ <b>Plan Ilimitado</b> ❤---------|
<blockquote>👥 <b>Límite de Grupos Para Publicar</b>: No hay límite
📩 <b>Límite de Publicaciones</b>: No hay límite
🔁 <b>Repitición Automática</b>: Si ✅</blockquote>
""".strip()

    
    def __str__(self):
        return self.show()
    

class Administrador: #SOLO PARA ADMINS

    cantidad_adjuntos = True
    caducidad = False
    grupos_publicados = True
    publicaciones = True
    repetir = 60 * 60
    plan = True
    ban = False

    def show(self):
        return """
|-------❤ <b>Plan Administrador </b> ❤---------|
<blockquote>👥 <b>Límite de Grupos Para Publicar</b>: No hay límite
📩 <b>Límite de Publicaciones</b>: No hay límite
🔁 <b>Repitición Automática</b>: Si ✅</blockquote>
""".strip()

    
    def __str__(self):
        return self.show()


class Planes_para_comprar:
    """
    Clase que engloba todos los planes que puede adquirir el usuario
    """
    lista_planes = [Basico(False, 12345678), Medio(False, 12345678), Pro(False, 12345678), Ilimitado(False, 12345678)]


    def show(self, lista = False):
        """
        Devuelve un string (plan.__str__) de cada plan con sus caracteristicas
        """
        texto = "<b>Lista de planes disponibles</b>:\n\n<blockquote>"

        if lista:
            lista = []
            for plan in self.lista_planes:
                if len(texto + plan.show() + "\n\n") >= 4088:
                    lista.append(texto + "</blockquote>")
                    texto = ""

                texto += plan.show() + "\n\n"

            lista.append(texto + "</blockquote>")

            return lista


        else:
            for plan in self.lista_planes:
                texto += plan.show() + "\n\n"
            
            texto += "</blockquote>"

            return texto

        

    


class Cuenta:
    def __init__(self, perfil_principal, usuario, contrasena, perfiles = []):
        self.perfil_principal = perfil_principal
        self.perfiles = perfiles
        self.usuario = usuario
        self.contrasena = contrasena

class Usuario:
    def __init__(self, telegram_id : int, plan : Baneado):
        self.telegram_id = telegram_id
        self.cuentas = [] #instancias de la clase Cuenta
        self.publicaciones = [] #instancias de la clase Publicacion
        self.plan = plan #instancia de la clase Planes o sus hijos

    def __str__(self):
        return int(self.telegram_id)

    def obtener_perfiles(self):
        lista = []
        if self.cuentas:
            for cuenta in self.cuentas:
                for perfil in cuenta.perfiles:
                    lista.append(perfil)

                lista.append(cuenta.perfil_principal)

            return lista

        else:
            return None


    def eliminar_publicacion(self, publicacion_eliminar):

        if isinstance(publicacion_eliminar, Publicacion):

            publicacion_eliminar = list(filter(lambda publicacion: publicacion == publicacion_eliminar, self.publicaciones))[0]

            if publicacion_eliminar.adjuntos:
                for foto in publicacion_eliminar.adjuntos:
                    if os.path.isfile(foto):
                        os.remove(foto)

            self.publicaciones.remove(publicacion_eliminar)

        elif isinstance(publicacion_eliminar, int):
            
            # try:
            #     publicacion_eliminar = list(filter(lambda publicacion: publicacion == publicacion_eliminar, self.publicaciones))[0]
            # except:
            publicacion_eliminar = self.publicaciones[publicacion_eliminar]

            if publicacion_eliminar.adjuntos:
                for foto in publicacion_eliminar.adjuntos:
                    if os.path.isfile(foto):
                        os.remove(foto)

            
            self.publicaciones.remove(publicacion_eliminar)


        return

    def eliminar_publicaciones(self):
        for publicacion in self.publicaciones:
            self.eliminar_publicacion(publicacion)


    def obtener_perfiles(self) -> list[str]:
        """
        Devuelve todos los perfiles de todas las cuentas del usuario almacenadas en el bot en una lista
        """
        lista = []
        for cuenta in self.cuentas:
            lista.extend(cuenta.perfiles)
        
        return lista

    def obtener_cuenta(self, perfil : str) -> Cuenta:
        """
        Obtiene el nombre del perfil principal de la cuenta (con el que se identifica) solamente con ingresar el nombre EXACTO de alguno de sus perfiles secundarios
        """

        for cuenta in self.cuentas:

            if perfil in cuenta.perfiles:
                return cuenta

    
class Publicacion:
    def __init__(self, titulo: str, texto: str , usuario_id: int , adjuntos: list):
        self.titulo = titulo
        self._adjuntos = []

        if adjuntos:
            for e, adjunto in enumerate(adjuntos):
                with open(adjunto, "rb") as file:
                    self._adjuntos.append({adjunto: file.read()})

        else:
            self._adjuntos = False

        self.texto = texto
        #-----------implementar para futuro------------
        self.grupos_excluidos = False
        self.grupos_publicar = False
        self.perfil_publicacion = [] #Define en que perfiles se publicará
        #----------------------------------------------


    @property
    def adjuntos(self):
        return self._adjuntos
    
    @adjuntos.getter
    def adjuntos(self):
        if self._adjuntos:
            lista = []
            for lista_publicaciones in self._adjuntos:
                for k in lista_publicaciones.keys():
                    lista.append(k)

            return lista
        
        else:
            return False
    

    @adjuntos.setter
    def adjuntos(self, value):
        self._adjuntos = value
        return self._adjuntos



    def enviar(self, scrapper: scrapping, chat_destino, **kwargs):
        
        TEXTO = """
<b><u>Título Publicación</u></b> (NO se mostrará en <b>Facebook</b>): 
<blockquote>{}</blockquote> 

<b><u>Texto Publicación</u></b> (SÍ se mostrará en <b>Facebook</b>):
<blockquote expandable>{}</blockquote> 
""".format(self.titulo, self.texto).strip()

        if not self.adjuntos:
            msg = scrapper.bot.send_message(chat_destino, TEXTO)

        elif len(self.adjuntos) > 1:
            for adjunto in self.adjuntos:

                kwargs["lista_grupos"] = []

                if mimetypes.guess_type(adjunto)[0].startswith("image"):
                    kwargs["lista_grupos"].append(InputMediaPhoto(InputFile(adjunto)))

                elif mimetypes.guess_type(adjunto)[0].startswith("video"):
                    kwargs["lista_grupos"].append(InputMediaVideo(InputFile(adjunto)))

                msg = scrapper.bot.send_media_group(chat_destino, kwargs["lista_grupos"])

        elif len(self.adjuntos) == 1:
            if mimetypes.guess_type(self.adjuntos[0])[0].startswith("image"):
                msg = scrapper.bot.send_photo(chat_destino, InputFile(self.adjuntos[0]), caption=TEXTO)

            elif mimetypes.guess_type(self.adjuntos[0])[0].startswith("video"):
                msg = scrapper.bot.send_video(chat_destino, InputFile(self.adjuntos[0]), caption=TEXTO)


        return msg


#---------------------Clases para regular los planes de los usuarios END-------------------
class Entrada():
    def __init__(self):
        """
        Clase para administrar el metodo de entrada al bot
        Manipula la cantidad de usuarios permitidos por el bot, las contraseñas, la caducidad de las mismas.
        Cada bot tiene un objeto de Entrada() diferente

        Si self.contrasena = False entonces todo el mundo podrá acceder al bot
        Si self.contrasena = True entonces NADIE podria acceder excepto los que estan en self.usuarios_permitidos: list
        """
        self.usuarios = []
        self.pasar = True
        



    def __str__(self):
        texto = "Clase |Entrada| variables:\n\n"
        for k, v in self.__dict__.items():
            texto += "Entrada.{}  =>  {}\n".format(k, v)

        return texto

    def actualizar_baneados(self, scrapper: scrapping):
        """
        Esta funcion comprobará si los usuarios baneados tanto de la BD local como del cluster son los mismos, normalmente el del cluster siempre estará mas actualizado que el local así que esto actualiza los usuarios baneados local
        """
        baneados_local = self.obtener_usuarios_baneados()
        baneados_cluster = scrapper.collection.find_one({"tipo": "datos"})["usuarios_baneados"]
        actualizar = False

        if baneados_cluster != baneados_local:
            
            #para comprobar si hay un nuevo usuario BANEADO globalmente pero no local
            for usuario_baneado_cluster in baneados_cluster:

                if not usuario_baneado_cluster in baneados_local:
                    actualizar = True

                    if usuario_baneado_cluster in self.obtener_usuarios():
                        self.obtener_usuario(usuario_baneado_cluster).plan = Baneado()

                    else:
                        self.usuarios.append(Usuario(usuario_baneado_cluster, Baneado()))


            #para comprobar si hay un nuevo usuario DESBANEADO globalmente pero no local
            for usuario_baneado_local in baneados_local:
                
                if not usuario_baneado_local in baneados_cluster:
                    actualizar = True
                    
                    self.obtener_usuario(usuario_baneado_local).plan = Sin_Plan()
        

        if actualizar:
            scrapper.administrar_BD()

        return


    def show(self):
        texto = "Clase |Entrada| variables:\n\n"
        for k, v in self.__dict__.items():
            texto += "Entrada.<b>{}</b>  =>  {}\n".format(k, v)

        return texto
    
    # def obtener_usuarios_baneados(self):
    #     if self.usuarios:
    #         lista = []
    #         for i in self.usuarios:
    #             if i.plan.baneado == True:
    #                 lista.append(i.telegram_id)

    #         return lista

    #     else:
    #         return None

    def obtener_usuario(self, user_id) -> Usuario:
        try:
            return list(filter(lambda u: u.telegram_id == user_id, self.usuarios))[0]
        
        except IndexError:
            return None


    def obtener_usuarios(self, id=True):
        """Devuelve TODOS los usuarios que tienen algún plan en el bot (a excepción de los baneados, para esos está la funcion 'obtener_usuarios_baneados()')"""
        if self.usuarios:
            lista = []

            for usuario in self.usuarios:
                
                if usuario.plan.__class__.__name__ != "Administrador":
                    continue

                elif not usuario.plan.ban == True:

                    if id:
                        lista.append(int(usuario.telegram_id))

                    else:
                        lista.append(usuario)

            return lista

        else:
            return None

    def obtener_usuarios_baneados(self, id=True):
        lista_baneados = []
        for usuario in self.usuarios:
            if usuario.plan.ban == True:
                if id:
                    lista_baneados.append(usuario.telegram_id)
                else:
                    lista_baneados.append(usuario)

        return lista_baneados


    def prohibir_pasar(self, scrapper, bot, prohibir_pasar=True , excepciones=[]):

        if prohibir_pasar == True:
            self.pasar = False

            for i in self.usuarios:
                if not i.telegram_id in excepciones:

                    if not scrapper.cola["uso"] == i.telegram_id or not i.plan.baneado == True:
                        
                        try:
                            bot.send_message(i.telegram_id, m_texto("Mi administrador ha bloqueado el acceso, no podrás usarme más hasta nuevo aviso...\n\nContacta con él si tienes alguna queja"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👮‍♂️ Contacta con el admin", url="https://t.me/{}".format(bot.get_chat(int(os.environ["admin"])).username))]]))
                        except:
                            pass

        
        elif prohibir_pasar == False:
            self.pasar = True

            for i in self.usuarios:
                if not i.telegram_id in excepciones:

                    if not scrapper.cola["uso"] == i.telegram_id or not i.plan.baneado == True:
                        
                        try:
                            bot.send_message(i.telegram_id, m_texto("Mi administrador ha bloqueado el acceso, no podrás usarme más hasta nuevo aviso...\n\nContacta con él si tienes alguna queja"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👮‍♂️ Contacta con el admin", url="https://t.me/{}".format(bot.get_chat(int(os.environ["admin"])).username))]]))
                        except:
                            pass

        return
    
    def get_caducidad(self, usuario:int , scrapper : scrapping, confirmar = False):
        """
        
        Devuelve True si ya no le queda tiempo al usuario y lo elimina de los usuarios que pueden usar el bot
        Devuelve False si no tiene caducidad el plan de este usuario (Ya sea porque es administrador o mi creador)

        Si aun queda tiempo para el usuario:
        Devuelve un string con el formato: <dias> Días, <horas> Horas y <minutos> Minutos
        """

        #para comprobar si siquiera el usuario existe
        if not list(filter(lambda objeto_usuario: objeto_usuario.telegram_id == usuario, scrapper.entrada.usuarios)):
            return True
        
        elif usuario in [scrapper.admin, scrapper.creador] or self.obtener_usuario(usuario).plan.caducidad == False:
            return False

        elif "Sin_Plan" == self.obtener_usuario(usuario).plan.__class__.__name__ or self.obtener_usuario(usuario).plan.plan == False:
            return True
        
        elif "Baneado" == self.obtener_usuario(usuario).plan.__class__.__name__:
            return True


        elif time.time() >= self.obtener_usuario(usuario).plan.caducidad:
            if scrapper.cola["uso"] == usuario:
                try:
                    scrapper.bot.send_message(usuario, "Al parecer, tu tiempo de contratación de mi servicio expiró,\nEl proceso actual de publicación ha sido cancelado...\n\n 👇 Contacta con mi administrador para renovar tu plan 👇 ", reply_markup=scrapper.admin_markup)

                except:
                    pass
                

                liberar_cola(scrapper, usuario, scrapper.bot)

            else:
                try:
                    scrapper.bot.send_message(usuario, "Al parecer, tu tiempo de contratación de mi servicio expiró,\n\n👇 Contacta con mi administrador para renovar tu plan 👇", reply_markup=scrapper.admin_markup)

                except:
                    pass


            self.obtener_usuario(usuario).plan = Sin_Plan()


            scrapper.entrada.obtener_usuario(usuario).eliminar_publicaciones()

            self.scrapper.guardar_datos(usuario, False)

            return True
        
        else:
            if not confirmar:

                tiempo_restante = self.obtener_usuario(usuario).plan.caducidad - time.time()

                return obtener_tiempo(tiempo_restante)


            else:
                return False
            
            
    
    def set_caducidad(self, usuario: int, scrapper: scrapping , fecha_local_limite: float):

        self.obtener_usuario(usuario).plan.caducidad = time.time() + fecha_local_limite

        if self.obtener_usuario(usuario).plan.caducidad - time.time() > 86400:
            return "{} Días, {} Horas y {} Minutos".format(int((self.obtener_usuario(usuario).plan.caducidad - time.time()) / 86400) , int((self.obtener_usuario(usuario).plan.caducidad - time.time()) % 86400  / 60 / 60), int((self.obtener_usuario(usuario).plan.caducidad - time.time()) % 86400  / 60 ))
        
        else:
            return "{} Horas y {} Minutos".format(int((self.obtener_usuario(usuario).plan.caducidad - time.time()) % 86400  / 60 / 60), int((self.obtener_usuario(usuario).plan.caducidad - time.time()) % 86400  / 60 ))

    
    

    
    

class MediaGroupCollector:

    def __init__(self, user_id, telegram_id):
        self.user_id = user_id
        self.telegram_id = telegram_id
        self.timer = None
        self.fotos = []
        self.TIMEOUT = 8

