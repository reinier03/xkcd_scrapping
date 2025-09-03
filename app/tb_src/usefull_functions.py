import time
import sys
import os
import selenium.webdriver
import selenium.webdriver.remote
import selenium.webdriver.remote.webelement
from seleniumbase.undetected import WebElement
import telebot
from telebot.types import *
import re
from traceback import format_exc
import selenium
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import Chrome
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.common.exceptions import *
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from tempfile import gettempdir, tempdir
import requests
import json
import dill

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from tb_src import bot_handlers

# import cv2
# import numpy
# import pyautogui
def borrar_elemento(scrapper , elemento):

    if isinstance(elemento, str):
        try:
            scrapper.driver.execute_script('document.querySelectorAll({}).forEach(e => e.remove());'.format(elemento))
            return "ok"

        except:
            return "fail"

    elif isinstance(elemento, WebElement):
        try:
            scrapper.driver.execute_script('document.querySelectorAll(arguments[0]).forEach(e => e.remove());', elemento)
            return "ok"

        except:
            return "fail"

    elif isinstance(elemento, list):

        for e in elemento:
            try:
                scrapper.driver.execute_script('document.querySelectorAll(arguments[0]).forEach(e => e.remove());', e)
            

            except:
                pass

    return 


def elemento_click(scrapper, elemento : tuple, intentos = 3):

    for i in range(intentos):
        
        try:
            scrapper.wait_s.until(ec.element_to_be_clickable(elemento))
            scrapper.find_element(elemento[0], elemento[1]).click()

        except:
            if i >= intentos -1:
                raise Exception("No he podido darle click al elemento: {}".format(elemento))

            time.sleep(2)
                


def facebook_popup(scrapper, user):
    """
    Muchas veces aparece un popup sobre que facebook es mejor en la aplicacion y nos recomienda instalarla, pero esto perturba el scrapping, en esta funcion compruebo si existe y me deshago de él
    """
    try:
        scrapper.wait_s.until(ec.any_of(
            ec.visibility_of_element_located((By.XPATH, '//*[contains(texto(), "Facebook is better on the app")]')),
            
            ))

    except:
        return "no"

    scrapper.temp_dict[user]["res"] = scrapper.driver.find_element(By.XPATH, '//*[contains(texto(), "Not now")]')

    for i in range(5):
        try:
            scrapper.temp_dict[user]["res"].click()
            break
        except:
            if i >= 4:
                raise Exception("No pude sacar el popup de Facebook")

            scrapper.temp_dict[user]["res"] = scrapper.temp_dict[user]["res"].find_element(By.XPATH, '..')

    return "ok"

    

def get_time_debug(scrapper, user, info="descripción de operación"):
    
    if not scrapper.temp_dict[user].get("tiempo_debug_c"):
        scrapper.temp_dict[user]["tiempo_debug_c"] = time.time()
        return "None"

    else:
        scrapper.temp_dict[user]["tiempo_debug_c"] = time.time() - scrapper.temp_dict[user]["tiempo_debug_c"]

        res = "{}:{}".format(int(scrapper.temp_dict[user]["tiempo_debug_c"] / 60), int(scrapper.temp_dict[user]["tiempo_debug_c"] % 60))

        del scrapper.temp_dict[user]["tiempo_debug_c"]

        return "tiempo: {}, operación: {}".format(str(res).zfill(2), str(info).zfill(2))




def get_time(scrapper, user , tz_country = "America/Havana"):
    if not scrapper.temp_dict[user].get("horario"):
        # scrapper.temp_dict[user]["horario"] = time.mktime(time.gmtime(json.loads(requests.get("http://api.timezonedb.com/v2.1/get-time-zone", params={"key": "68TYQMUQ25P6", "by": "zone", "format": "json" , "zone" : tz_country}).content)["timestamp"]))

        # scrapper.temp_dict[user]["diferencia"] = time.mktime(time.gmtime()) - scrapper.temp_dict[user]["horario"]



        scrapper.temp_dict[user]["horario"] = time.time()

        return "{}:{}".format(str(int((time.time() - scrapper.temp_dict[user]["demora"]) // 60)).zfill(2), str(int((time.time() - scrapper.temp_dict[user]["demora"]) % 60)).zfill(2))
    
    else:

        horario = float(scrapper.temp_dict[user]["horario"])
        
        scrapper.temp_dict[user]["horario"] = time.time()
        
        return "{}:{}".format(str(int((time.time() - horario) // 60)).zfill(2), str(int((time.time() - horario) % 60)).zfill(2))  

    



def liberar_cola(scrapper, user, bot):

    if scrapper.temp_dict[user].get("cancelar"):
        bot.send_message(user, m_texto("Operación cancelada :("))

    elif scrapper.temp_dict[user].get("cancelar_forzoso"):

        bot.send_message(int(user), m_texto("El administrador ha finalizado tu proceso\n\nSi tienes alguna queja comunícate con él"), reply_markup=InlineKeyboardMarkup([

            [InlineKeyboardButton("👮‍♂️ Contacta con el admin", url="https://t.me/{}".format(bot.get_chat(scrapper.admin).username))]

        ]))

    scrapper.cola["uso"] = False

    for i in scrapper.cola["cola_usuarios"]:
        try:
            bot.send_message(i, m_texto("Ya estoy disponible para Publicar :D\n\nÚsame antes de que alguien más me ocupe"))
        except:
            pass
    
    if scrapper.interrupcion:
        scrapper.interrupcion = False
        
    del scrapper.temp_dict[user]
    administrar_BD(scrapper, bot)
    return

def obtener_grupos(scrapper, user, all: bool = False):
    

    try:
        #elemento de los grupos
        scrapper.wait.until(ec.visibility_of_element_located((By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[5]')))
    
    except:
        #en caso de que no esté mostrada la pagina de grupos esto fallará así que la cargo
        load(scrapper, "https://m.facebook.com/groups/")
        scrapper.temp_dict[user]["e"] = scrapper.wait.until(ec.visibility_of_element_located((By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[5]')))

    if all:
        
        while True:
            scrapper.temp_dict[user]["res"] = obtener_grupos(scrapper, user)

            hacer_scroll(scrapper, user, scrapper.temp_dict[user]["res"][-1], len(scrapper.temp_dict[user]["res"]) // 4 , len(scrapper.temp_dict[user]["res"]) - 1)

            time.sleep(1)
            
            scrapper.temp_dict[user]["a"].scroll_from_origin(ScrollOrigin.from_element(scrapper.temp_dict[user]["res"][-1]), 0 , int(scrapper.temp_dict[user]["res"][-1].size["height"]) * 3).perform()
            
            try:
                
                scrapper.wait_s.until(ec.any_of(lambda driver, scrapper=scrapper, user=user: len(scrapper.temp_dict[user]["res"]) < len(obtener_grupos(scrapper, user))))
                
                
            except:
                pass
            

            if len(scrapper.temp_dict[user]["res"]) == len(obtener_grupos(scrapper, user)):
                scrapper.temp_dict[user]["res"] = obtener_grupos(scrapper, user)
                break

            else:
                pass




    scrapper.temp_dict[user]["res"] = scrapper.driver.find_element(By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[5]').find_elements(By.CSS_SELECTOR, 'div[data-mcomponent="MContainer"][data-focusable="true"][data-type="container"]')
    
    #le quito 2 porque ese elemento es el de "create a group" y "Sort" que pone de primero facebook
    for i in range(2):                
        scrapper.temp_dict[user]["res"].remove(scrapper.temp_dict[user]["res"][0])

    return scrapper.temp_dict[user]["res"]

# def if_cambio(scrapper, user):
    
    
#     for i in range(10):
#         scrapper.temp_dict[user]["captura"] = numpy.array(pyautogui.screenshot(os.path.join(str(user_folder(user)), "prueba.png")))

#         if numpy.sum(cv2.absdiff(scrapper.temp_dict["original"] , scrapper.temp_dict[user]["captura"])) > scrapper.temp_dict["original"].shape[1] * scrapper.temp_dict["original"].shape[0] * 3 * 255 * 0.15:
#             os.remove(os.path.join(str(user_folder(user)), "prueba.png"))
#             os.remove(os.path.join(str(user_folder(user)), "original.png"))
#             del scrapper.temp_dict[user]["captura"]
#             del scrapper.temp_dict["original"]
#             return True
        
#         else:
#             time.sleep(5)



#     raise Exception("No se encontraron cambios en la GUI para que apareciera la ventana de la selección de fotos")


# def envia_fotos_gui(scrapper, user, photo_path):
#     scrapper.wait.until(ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "hotos")]')))

#     if os.path.isfile(os.path.join(str(user_folder(user)), "original.png")):
#         os.remove(os.path.join(str(user_folder(user)), "original.png"))

#     scrapper.temp_dict["original"] = numpy.array(pyautogui.screenshot(os.path.join(str(user_folder(user)), "original.png")))

    
#     scrapper.driver.find_element(By.XPATH, '//*[contains(@aria-label, "hotos")]').click()

    
    
#     if if_cambio(scrapper, user) == True:
#         if os.name != "nt":
#             pyautogui.write(photo_path).replace("\\", "/")

#         else:
#             pyautogui.write(photo_path).replace("/", "\\")

#         pyautogui.press("tab")
#         pyautogui.press("tab")
#         pyautogui.press("enter")


#         time.sleep(2)

def envia_fotos_input(scrapper, user, photo_path):
    

    try:
        scrapper.wait_s.until(ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "otos")]')))
        scrapper.driver.find_elements(By.XPATH, '//*[contains(text(), "otos")]')[-1].click()
    except:
        scrapper.wait_s.until(ec.visibility_of_element_located((By.XPATH, '//*[@id="screen-root"]/div/div[2]/div[7]')))
        scrapper.driver.find_element(By.XPATH, '//*[@id="screen-root"]/div/div[2]/div[7]').click()
        

    scrapper.driver.find_element(By.XPATH, '//input').send_keys(photo_path)

    # scrapper.temp_dict[user]["a"].send_keys_to_element(scrapper.driver.find_element(By.XPATH, '//input'), photo_path)
    
    return True
    
    try:
        scrapper.driver.execute_script('arguments[0].removeAttribute("data-client-focused-component")', scrapper.driver.find_element(By.XPATH, '//*[contains(@data-client-focused-component, "true")]'))
    except:
        pass

    scrapper.driver.execute_script('arguments[0].setAttribute("accept", "image/jpeg"); arguments[0].setAttribute("multiple", "true")', scrapper.driver.find_element(By.XPATH, '//input'))


    scrapper.driver.execute_script('arguments[0].setAttribute("data-client-focused-component", "true")', scrapper.driver.find_element(By.XPATH, '//*[contains(@aria-label, "hotos")]'))


    scrapper.driver.execute_script('arguments[0].setAttribute("width", "50px")', scrapper.driver.find_element(By.XPATH, '//input'))

    scrapper.driver.execute_script('arguments[0].setAttribute("height", "50px")', scrapper.driver.find_element(By.XPATH, '//input'))
    
    scrapper.driver.execute_script('arguments[0].setAttribute("display", "block")', scrapper.driver.find_element(By.XPATH, '//input'))

    scrapper.driver.execute_script('arguments[0].setAttribute("style", "display: block; width: 100px; height: 100px; text: Hola")', scrapper.driver.find_element(By.XPATH, '//input'))

    scrapper.driver.find_element(By.XPATH, '//input').text

    scrapper.driver.find_element(By.CSS_SELECTOR, 'h2').click()

    time.sleep(1)

    scrapper.temp_dict[user]["a"].send_keys_to_element(scrapper.driver.find_element(By.XPATH, '//input'), photo_path).perform()
    scrapper.driver.find_element(By.XPATH, '//input').send_keys(photo_path)
    
    

def load(scrapper, url):

        
    if os.name == "nt":
        try:
            scrapper.driver.get(url)
        except:
            pass
        
        
        while True:
            try:
                WebDriverWait(scrapper.driver, 500).until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))
                break
            except:
                pass
            
    else:
        scrapper.driver.get(url)
            
    
    
    return 
        

def if_cancelar(scrapper, user, bot):

    if scrapper.entrada.caducidad:
        if time.time() >= scrapper.entrada.caducidad:
            scrapper.entrada.limpiar_usuarios(scrapper, bot)
            if scrapper.cola["uso"]:
                scrapper.temp_dict[scrapper.cola["uso"]]["cancelar_forzoso"] = True

                liberar_cola(scrapper, user, bot)

    
            bot.send_message(scrapper.admin, m_texto("El tiempo de vigencia de la contraseña ha caducado"))


    if scrapper.temp_dict[user].get("cancelar") or scrapper.temp_dict[user].get("cancelar_forzoso"):
        
        liberar_cola(scrapper, user, bot)

    return "ok"

def obtener_diferencia_scroll(scrapper, user):
    if not scrapper.driver.current_url.endswith("groups/"):
        load(scrapper ,"https://m.facebook.com/groups/")
    
    try:
        return scrapper.temp_dict[user]["publicacion"]["lista_grupos"][0].location["y"]
    
    except StaleElementReferenceException or ElementNotVisibleException or NoSuchElementException:
        try:
            scrapper.temp_dict[user]["publicacion"]["lista_grupos"] = obtener_grupos(scrapper, user)
            return scrapper.temp_dict[user]["publicacion"]["lista_grupos"][0].location["y"]

        except:

            scrapper.temp_dict[user]["scroll_position"] = scrapper.driver.execute_script("return window.pageYOffset;")


            hacer_scroll(scrapper, user, - scrapper.temp_dict[user]["scroll_position"], scrapper.temp_dict[user]["scroll_position"] // 100)

            try:
                scrapper.temp_dict[user]["publicacion"]["lista_grupos"][0].is_displayed()
            except:
                scrapper.temp_dict[user]["publicacion"]["lista_grupos"] = obtener_grupos(scrapper, user)
                
            hacer_scroll(scrapper, user, scrapper.temp_dict[user]["scroll_position"], scrapper.temp_dict[user]["scroll_position"] // 100)

            del scrapper.temp_dict[user]["scroll_position"]

            return scrapper.temp_dict[user]["publicacion"]["lista_grupos"][0].location["y"]

def hacer_scroll(scrapper , user: int, elemento, pasos: int, contador: int = True, esperar = 1.3):
    
    if contador:
        #a partir de los ultimos 11 elementos el scroll es inútil
        if len(scrapper.temp_dict[user]["publicacion"]["lista_grupos"]) <= 11:
            return "ok"

    if pasos == 0:
        return "ok"
        
    if isinstance(elemento, selenium.webdriver.remote.webelement.WebElement):
        scrapper.temp_dict[user]["y_scroll"] = elemento.location["y"] - (elemento.rect["height"] * 2)
        scrapper.temp_dict[user]["y_scroll"] = scrapper.temp_dict[user]["y_scroll"] // pasos

    elif isinstance(elemento, int):
        scrapper.temp_dict[user]["y_scroll"] = elemento // pasos

    if not isinstance(scrapper.temp_dict[user]["y_scroll"], int):
        scrapper.temp_dict[user]["y_scroll"] = int(scrapper.temp_dict[user]["y_scroll"])
    

    for i in range(int(pasos)):

        try:
            scrapper.temp_dict[user]["a"].scroll_by_amount(0, scrapper.temp_dict[user]["y_scroll"]).perform()
            
        except StaleElementReferenceException or NoSuchElementException or ElementNotInteractableException:
            if contador:
                try:
                    elemento = obtener_grupos(scrapper, user)[contador]
                except IndexError:
                    elemento = obtener_grupos(scrapper, user, True)[contador]

                i -= 1

                continue

            else:
                raise Exception("No encuentro el elemento para hacer el scroll...")

        if esperar:
            time.sleep(esperar)


    del scrapper.temp_dict[user]["y_scroll"]

    return "ok"

def give_error(bot, driver, user, texto, foto=True):
    if foto:
        bot.send_photo(user, telebot.types.InputFile(make_screenshoot(driver, user)), "Captura del Error")

    raise Exception(texto)

def limpiar(driver: Chrome):
    a = ActionChains(driver, 0)
    """Limpia el cache periódicamente"""
    driver.switch_to.new_window()
    driver.get('chrome://settings/clearBrowserData')
    ActionChains(driver, 0).send_keys(Keys.TAB, Keys.ENTER).perform()
    time.sleep(2)  # Espera a que limpie
    
    driver.close()
    
    if len(driver.window_handles) > 1:
        for tab in driver.window_handles:
            if tab == driver.window_handles[0]:
                continue
                
            driver.switch_to.window(tab)
            driver.close()
    
    driver.switch_to.window(driver.window_handles[0])
    return "ok"


def clear_doom(driver: Chrome, hacer_limpieza=True):
    #https://stackoverflow.com/questions/73604732/selenium-webdriverexception-unknown-error-session-deleted-because-of-page-cras
    
    # driver.execute_script('document.body.innerHTML = ";"')
    
    #
    try:
        driver.execute_script('document.querySelectorAll("div.x78zum5.xdt5ytf.x1n2onr6.xat3117.xxzkxad").forEach(e => e.remove());',)
        
    except:
        pass
    
    try:
        driver.execute_script('document.querySelectorAll("div[role=main]").forEach(e => e.remove());')
    except:
        pass
    
    if hacer_limpieza:
        limpiar(driver)
    
    return "ok"


def leer_BD(scrapper = False):
    if scrapper:
        res = dill.loads(scrapper.collection.find_one({"_id": "telegram_bot"})["cookies"])["scrapper"]
        print(res)
    else:
        with open(os.path.join(tempdir, "bot_cookies.pkl"), "rb") as file:
            file.seek(0)
            res = dill.loads(file.read())["scrapper"]
            print(res)

    return res


def administrar_BD(scrapper, bot, cargar_cookies=False, user=False, **kwargs):
    """
    El parametro 'guardar' si es True, guardará el estado actual del bot, Si es False lo cargará
    """

    dict_guardar = {"scrapper": scrapper}
    for k, v in kwargs.items():
        if not user:
            dict_guardar.update({k: v})

        if user:
            dict_guardar["scrapper"].temp_dict[user].update({k: v})

    
    #GUARDAR
    if cargar_cookies == False:
        #si va a guardarse el estado...

        

        with open(os.path.join(gettempdir(), "bot_cookies.pkl"), "wb") as file:

            dill.dump(dict_guardar, file)

        with open(os.path.join(gettempdir(), "bot_cookies.pkl"), "rb") as file:

            if scrapper.collection.find_one({"_id": "telegram_bot", "telegram_id": bot.user.id}):
                
                scrapper.collection.update_one({"_id": "telegram_bot", "telegram_id": bot.user.id}, {"$set": {"cookies" : file.read()}})

            else:
                scrapper.collection.insert_one({"_id": "telegram_bot", "telegram_id": bot.user.id, "cookies" : file.read()})

        return "ok"

    #CARGAR
    elif cargar_cookies == True:
        #si se va a cargar el estado...        
        if scrapper.collection.find_one({"_id": "telegram_bot", "telegram_id": bot.user.id}):
            
            res = ("ok" , dill.loads(scrapper.collection.find_one({"_id": "telegram_bot", "telegram_id": bot.user.id})["cookies"]))

            with open(os.path.join(gettempdir(), "bot_cookies.pkl"), "wb") as file:
                dill.dump(dill.loads(scrapper.collection.find_one({"_id": "telegram_bot", "telegram_id": bot.user.id})["cookies"]), file)


        else:
            #si no hay ningun archivo del bot en la base de datos primero compruebo si hay una copia local para insertarla en la BD
            if os.path.isfile(os.path.join(gettempdir(), "bot_cookies.pkl")):

                with open(os.path.join(gettempdir(), "bot_cookies.pkl"), "rb") as file:
                    scrapper.collection.insert_one({"_id": "telegram_bot", "telegram_id": bot.user.id, "cookies": file.read()})

                    file.seek(0)

                    res = ("ok" , dill.load(file))
                    
            #si no hay copia ni en local ni en online pues la creo
            else:
                with open(os.path.join(gettempdir(), "bot_cookies.pkl"), "wb") as file:

                    dill.dump(dict_guardar, file)

                with open(os.path.join(gettempdir(), "bot_cookies.pkl"), "rb") as file:

                    scrapper.collection.insert_one({"_id": "telegram_bot", "telegram_id": bot.user.id, "cookies" : file.read()})
                    res = ("fail", "se ha guardado una nueva copia, al parecer no habia ninguna")

        return res

        


                


    

def comprobar_BD(collection):
    try:
        collection.count_documents({})
        return "ok"
    
    except Exception as e:
        try:
            if re.search('error=.*timeout', e.args[0]).group().split('(')[1]:
                raise Exception("No hay conexión con la base de datos!" + "\n\nDescripción\n" + re.search('error=.*timeout', e.args[0]).group().split('(')[1])
        except:
            pass
        
        raise Exception("Conecta la Base de Datos!\n\nDescripción del error:\n" + format_exc())

def m_texto(texto, solicitud=False):
    if solicitud:
        return "❗ <u><b>Solicitud de Información</b></u> ❗\n\n" + texto
    else:
        return "🆕 <u><b>Mensaje de Información</b></u>\n\n<blockquote>" + texto + "</blockquote>"

def info_message(texto, bot:telebot.TeleBot, temp_dict, user, mensaje_obj=False , markup = False):
    if mensaje_obj:
        if not markup:
            temp_dict[user]["info"] = bot.edit_message_text("🆕 Mensaje de Información\n\n" + texto, chat_id=user, message_id=temp_dict[user]["info"].message_id)
        
        else:
            temp_dict[user]["info"] = bot.edit_message_text("🆕 Mensaje de Información\n\n" + texto, chat_id=user, message_id=temp_dict[user]["info"].message_id, reply_markup=markup)
    
    else:
        if not markup:
            temp_dict[user]["info"] = bot.send_message(user, "🆕 Mensaje de Información\n\n" + texto)
        
        else:
            temp_dict[user]["info"] = bot.send_message(user, "🆕 Mensaje de Información\n\n" + texto, reply_markup=markup)
            
    return temp_dict[user]["info"]

def main_folder():
    if os.name != "nt":
        if not os.path.dirname(os.path.abspath(__file__)).endswith("app"):
            
            return os.path.dirname(os.path.abspath(__file__)).split("app")[0] + "app"
        
        else:
            return os.path.dirname(os.path.abspath(__file__))
        
    else:
        return os.path.dirname(sys.argv[0])
            


def user_folder(user):
    user = str(user)
    carpeta_destino = gettempdir()
    # carpeta_destino = main_folder()
    
    if not "user_archive" in os.listdir(carpeta_destino):
        os.mkdir(os.path.join(carpeta_destino, "user_archive"))
        os.mkdir(os.path.join(carpeta_destino, "user_archive", user))
        
    if not list(filter(lambda file: file.startswith(user), os.listdir(os.path.join(carpeta_destino, "user_archive")))):
        os.mkdir(os.path.join(carpeta_destino, "user_archive",  user))
        
    return os.path.join(carpeta_destino, "user_archive",  user)
    
def make_screenshoot(driver, user, element=False, bot=False):
    user = str(user)
    if element:
        element.screenshot(os.path.join(user_folder(user) , str(user) + "_error_facebook.png"))
    else:
        driver.save_screenshot(os.path.join(user_folder(user) , str(user) + "_error_facebook.png"))
    
    if not bot:
        return os.path.join(user_folder(user) , str(user) + "_error_facebook.png")
    
    else:
        bot.send_photo(user, telebot.types.InputFile(os.path.join(user_folder(user) , str(user) + "_error_facebook.png")), "Captura")

        return os.path.join(user_folder(user) , str(user) + "_error_facebook.png")
    
def make_captcha_screenshoot(captcha_element, user):
    user = str(user)
    captcha_element.screenshot(os.path.join(user_folder(user), str(user) + "_captcha.png"))
    
    return os.path.join(user_folder(user), str(user) + "_captcha.png")


def handlers(bot, user , msg ,info, diccionario: dict , **kwargs):    

    temp_dict = diccionario.copy()
    msg = m_texto(msg, True)

    if kwargs.get("file"):
        if kwargs.get("markup"):
            temp_dict[user]["msg"] = bot.send_photo(user, kwargs.get("file"), caption=msg, reply_markup=kwargs.get("markup"))
            
        else:
            temp_dict[user]["msg"] = bot.send_photo(user, kwargs.get("file"), caption=msg)
        
    else:
        if kwargs.get("markup"):
            temp_dict[user]["msg"] = bot.send_message(user, msg, reply_markup=kwargs.get("markup"))
        
        else:
            temp_dict[user]["msg"] = bot.send_message(user, msg)
    

    temp_dict[user]["completed"] = False   

    match info:
        
        case "user":
        
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.get_user, bot,user, info, temp_dict, diccionario=temp_dict)
            
        case "password":
            
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.get_user, bot,user, info, temp_dict, diccionario=temp_dict)
            
        case "perfil_elegir":
            
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.choose_perfil, bot,user, info, temp_dict)
            
        case "codigo_respaldo":
            
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.get_codigo, bot,user, info, temp_dict)
            
        case "perfil_pregunta":
            
            
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.perfil_pregunta, bot,user, info, temp_dict)
            
        case "captcha":
            
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.captcha_getter, bot,user, info, temp_dict, kwargs.get("file"))
            
        case "perfil_seleccion":
            
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.perfil_seleccion, bot,user, info, temp_dict, kwargs.get("markup"))

        case "correo_o_numero":

            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.correo_o_numero, bot,user, info, temp_dict)


        case "correo_o_numero_verificacion":
            
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.correo_o_numero_verificacion, bot,user, info, temp_dict)

        case "email_verification":
            

            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.email_verification, bot,user, info, temp_dict)
            

        case "bucle_publicacion":

            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.repetir_bucle, bot,user, info, temp_dict)
            
            
    while True:
        diccionario[user]["if_cancelar"]()

        if not temp_dict[user]["completed"]:
            time.sleep(2)
            
        else:
            break
    
    del temp_dict[user]["completed"], temp_dict[user]["msg"]
    
    diccionario[user].update(temp_dict[user])
    
    return temp_dict[user]["res"]