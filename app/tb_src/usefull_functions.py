import threading
import time
import sys
import os
import selenium.webdriver
import selenium.webdriver.remote
import selenium.webdriver.remote.webelement
from selenium.webdriver.remote.webelement import WebElement
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
import telebot.types
import tb_src
import tb_src.main_classes

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from tb_src import bot_handlers

# import cv2
# import numpy
# import pyautogui





def puede_continuar(scrapper, user, comprobacion = True):
    """
    Verifica si el plan que contrató el usuario le permite continuar para hacer algo especificado en <comprobacion>

    Devuelve True si puede continuar
    Devuelve False si no puede hacerlo
    """
    
    if scrapper.entrada.get_caducidad(user, scrapper) == True:
        return True


    if comprobacion == "publicacion":
        usuario = scrapper.entrada.obtener_usuario(user)
        if not usuario.plan.grupos_publicados == True:
            if usuario.plan.grupos_publicados - 1 <= scrapper.temp_dict[user]["contador"]:
                return False
            else:
                return True
        else: 
            return True


def mostrar_info_usuario(chat_destino, usuario_evaluar, bot: telebot.TeleBot):
    if not bot.get_chat(usuario_evaluar):
        bot.send_message(chat_destino, "Ese usuario ni siquiera existe!")
        return

    with open(bot.get_chat(usuario_evaluar).first_name + ".jpg" if bot.get_chat(usuario_evaluar).first_name else usuario_evaluar + ".jpg", "wb") as file:
        nombre_archivo = file.name
        file.write(bot.download_file(bot.get_file(bot.get_chat(usuario_evaluar).photo.small_file_id).file_path))
        bot.send_document(chat_destino, telebot.types.InputFile(file.name), caption=
"""
<b>ID</b>: <code>{}</code>
<b>Nombre</b>: {}
<b>Alias (username)</b>: {}
""".strip().format(usuario_evaluar, bot.get_chat(usuario_evaluar).first_name, "@" + bot.get_chat(usuario_evaluar).username if  bot.get_chat(usuario_evaluar).username else str("No tiene")))
        
    os.remove(nombre_archivo)

    return

def debug_txt(scrapper=False):
    if scrapper:
        if scrapper.temp_dict.get(scrapper.admin):

            if scrapper.temp_dict[scrapper.admin].get("mostrar_tiempo_debug") and scrapper.temp_dict[scrapper.admin].get("tiempo_debug"):
                
                scrapper.temp_dict[scrapper.admin]["res"] = "\n".join(scrapper.temp_dict[scrapper.admin]["tiempo_debug"])

                with open(os.path.join(user_folder(scrapper.admin), "tiempo_publicacion_" + str(scrapper.admin) + ".txt"), "w", encoding="utf-8") as file:
                    file.write("Log de publicación\nID del usuario: {}\n\n{}".format(scrapper.admin, scrapper.temp_dict[scrapper.admin]["res"]))
                    
                with open(os.path.join(user_folder(scrapper.admin), "tiempo_publicacion_" + str(scrapper.admin) + ".txt"), "r", encoding="utf-8") as file:
                    scrapper.bot.send_document(scrapper.admin, telebot.types.InputFile(file, file_name="tiempo_publicacion_" + str(scrapper.admin) + ".txt"), caption = "Ha ocurrido un error inesperado! ID usuario: {}".format(scrapper.admin))
            
                os.remove(os.path.join(user_folder(scrapper.admin), "tiempo_publicacion_" + str(scrapper.admin) + ".txt"))
                del scrapper.temp_dict[scrapper.admin]["mostrar_tiempo_debug"]
                del scrapper.temp_dict[scrapper.admin]["tiempo_debug"]


    return


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


def liberar_cola(scrapper, user, bot, mensaje_notificar = True ,notificar_usuarios=True):

    if not user in list(scrapper.temp_dict):
        return

    if scrapper.temp_dict[user].get("cancelar") and mensaje_notificar:
        bot.send_message(user, m_texto("Operación cancelada :("), reply_markup=ReplyKeyboardRemove())

    elif scrapper.temp_dict[user].get("cancelar_forzoso"):

        bot.send_message(int(user), m_texto("ATENCIÓN‼\nEl administrador ha finalizado TU proceso\n\n👇Si tienes alguna queja comunícate con él👇\n{}".format(str("@" + bot.get_chat(scrapper.admin).username) if bot.get_chat(scrapper.admin).username else str(" "))), reply_markup=ReplyKeyboardRemove())

    
    
    if not scrapper.temp_dict[user].get("if_cancelar"):
        scrapper.cola["uso"] = False

    if notificar_usuarios:

        for i in scrapper.cola["cola_usuarios"]:
            try:
                bot.send_message(i, m_texto("Ya estoy disponible para Publicar :D\n\nÚsame antes de que alguien más me ocupe"))
            except:
                pass
    
    if scrapper.interrupcion:
        scrapper.interrupcion = False
    
    try:
        del scrapper.temp_dict[user]
    except:
        pass

    scrapper.guardar_datos(user, False)

    return

def obtener_grupos(scrapper, user, all: bool = False):
    

    try:
        #elemento de los grupos
        scrapper.wait.until(ec.visibility_of_element_located((By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[5]')))
    
    except:
        #en caso de que no esté mostrada la pagina de grupos esto fallará así que la cargo
        scrapper.load("https://m.facebook.com/groups/")
        scrapper.temp_dict[user]["e"] = scrapper.wait.until(ec.visibility_of_element_located((By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[5]')))

    try:
        #eliminar el elemento "open app" o "abrir app" si se encuentra
        scrapper.driver.execute_script('document.querySelectorAll("div.m.fixed-container.bottom").forEach(e => e.remove());')
    except:
        pass
    
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



    scrapper.wait.until(ec.visibility_of_element_located((By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[5]')))

    scrapper.temp_dict[user]["res"] = scrapper.find_element(By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[5]').find_elements(By.CSS_SELECTOR, 'div[data-mcomponent="MContainer"][data-focusable="true"][data-type="container"]')
    
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

    
#     scrapper.find_element(By.XPATH, '//*[contains(@aria-label, "hotos")]').click()

    
    
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
    

    scrapper.temp_dict[user]["res"] = scrapper.wait.until(ec.any_of(
        lambda driver: driver.find_elements(By.CSS_SELECTOR, "span.f1")[3],
        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Photos")]')),
        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Fotos")]')),
        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "otos")]')),
        ec.visibility_of_element_located((By.XPATH, '//*[@id="screen-root"]/div/div[2]/div[7]')),
    ))


    try:
        scrapper.temp_dict[user]["res"].click()
    
    except:
        ActionChains(scrapper.driver).click(scrapper.temp_dict[user]["res"]).perform()
        

    scrapper.find_element(By.XPATH, '//input').send_keys(photo_path)

    # scrapper.temp_dict[user]["a"].send_keys_to_element(scrapper.find_element(By.XPATH, '//input'), photo_path)
    
    return True
    
    try:
        scrapper.driver.execute_script('arguments[0].removeAttribute("data-client-focused-component")', scrapper.find_element(By.XPATH, '//*[contains(@data-client-focused-component, "true")]'))
    except:
        pass

    scrapper.driver.execute_script('arguments[0].setAttribute("accept", "image/jpeg"); arguments[0].setAttribute("multiple", "true")', scrapper.find_element(By.XPATH, '//input'))


    scrapper.driver.execute_script('arguments[0].setAttribute("data-client-focused-component", "true")', scrapper.find_element(By.XPATH, '//*[contains(@aria-label, "hotos")]'))


    scrapper.driver.execute_script('arguments[0].setAttribute("width", "50px")', scrapper.find_element(By.XPATH, '//input'))

    scrapper.driver.execute_script('arguments[0].setAttribute("height", "50px")', scrapper.find_element(By.XPATH, '//input'))
    
    scrapper.driver.execute_script('arguments[0].setAttribute("display", "block")', scrapper.find_element(By.XPATH, '//input'))

    scrapper.driver.execute_script('arguments[0].setAttribute("style", "display: block; width: 100px; height: 100px; text: Hola")', scrapper.find_element(By.XPATH, '//input'))

    scrapper.find_element(By.XPATH, '//input').text

    scrapper.find_element(By.CSS_SELECTOR, 'h2').click()

    time.sleep(1)

    scrapper.temp_dict[user]["a"].send_keys_to_element(scrapper.find_element(By.XPATH, '//input'), photo_path).perform()
    scrapper.find_element(By.XPATH, '//input').send_keys(photo_path)
    
    


        

def if_cancelar(scrapper, user, bot):

    if scrapper.entrada.get_caducidad(user,scrapper) == True:
        return


    if scrapper.temp_dict[user].get("cancelar") or scrapper.temp_dict[user].get("cancelar_forzoso"):
        
        liberar_cola(scrapper, user, bot)

    return "ok"

def obtener_diferencia_scroll(scrapper, user):
    if not scrapper.driver.current_url.endswith("groups/"):
        scrapper.load("https://m.facebook.com/groups/")
    
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

            scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'body')))

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
            #aparece un "cargando..." cuando hay mas grupos en el scroll
            try:
                WebDriverWait(scrapper.driver, esperar).until(ec.any_of(
                    ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Loading")]')),
                    ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Cargando")]'))
                ))

                scrapper.wait.until(ec.any_of(
                    ec.invisibility_of_element_located((By.XPATH, '//*[contains(text(), "Loading")]')),
                    ec.invisibility_of_element_located((By.XPATH, '//*[contains(text(), "Cargando")]'))
                ))

                time.sleep(esperar)
            except:
                pass


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
        res = dill.loads(scrapper.collection.find_one({"tipo": "telegram_bot", "telegram_id": scrapper.bot.user.id})["cookies"])["scrapper"]
        print(res)
    else:
        with open(os.path.join(tempdir, "bot_cookies.pkl"), "rb") as file:
            file.seek(0)
            res = dill.loads(file.read())["scrapper"]
            print(res)

    return res


def obtener_tiempo(tiempo: float):
    """Devuelve el tiempo dado en segundos en un mejor formato"""

    #cuando hay más de un día
    if tiempo > 86400:
        return "{} Día(s), {} Hora(s) y {} Minuto(s)".format(int(tiempo / 86400) , int(tiempo % 86400  / 60 / 60), int(tiempo % 86400  / 60 % 60))

    #cuando hay más de 1 hora
    elif tiempo > 3600:
        return "{} Hora(s) y {} Minuto(s)".format(int(tiempo / 60 / 60), int(tiempo / 60 % 60))

    #cuando hay más de 1 minuto
    elif tiempo > 60:
        return "{} Minuto(s)".format(int(tiempo / 60 ))
    
    #cuando SOLO es segundos
    else:
        return "{} Segundo(s)".format(int(tiempo))

    

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
        
        if re.search("ERROR", texto):
            texto = texto.replace(re.search(r"\s*ERROR\s*", texto).group(), "")
            return "<b>❌ ¡Error! ❌</b>\n¡La información ingresada es incorrecta!\n\n" + texto
        else:
            return "🆕 <u><b>Mensaje de Información</b></u>\n\n" + texto

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
    

def ver_publicacion(c: telebot.types.CallbackQuery, scrapper, bot: telebot.TeleBot, indice: int, usuario_info=False, cantidad_publicaciones_mostrar = 6):
    #usuario_info es el usuario del cual esta publicación es

    if usuario_info == False:
        usuario_info = c.from_user.id

    if scrapper.cola["uso"] == c.from_user.id:
        p_markup=InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("↩ Volver Atrás", callback_data="p/wl/a/{}".format(indice if indice % cantidad_publicaciones_mostrar == 0 else indice - indice % cantidad_publicaciones_mostrar))],
        ]
    )

    else:
        p_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🗑 Eliminar Publicación", callback_data="p/del/conf/{}".format(indice))],
                [InlineKeyboardButton("↩ Volver Atrás", callback_data="p/wl/a/{}".format(indice if indice % cantidad_publicaciones_mostrar == 0 else indice - indice % cantidad_publicaciones_mostrar))],
            ]
        )
    
    for usuario in scrapper.entrada.obtener_usuarios(False):
        res = usuario.publicaciones[indice].enviar(scrapper, c.message.chat.id)

        if isinstance(res, list):
            #puede ser que sea una galeria de fotos...
            bot.edit_message_reply_markup(c.message.chat.id, res[-1].message_id, reply_markup=p_markup)

        else:
            
            bot.edit_message_reply_markup(c.message.chat.id, res.message_id, reply_markup=p_markup)




    

def ver_lista_publicaciones(m, scrapper, bot: telebot.TeleBot, indice = 0, usuario_info=False, cantidad_publicaciones_mostrar = 6, elegir=False):

    
    if not usuario_info:
        usuario_info = m.from_user.id

    if isinstance(m, telebot.types.CallbackQuery):
        m = m.message

    
    
    #para asegurarme de que el índice a la siguiente lista exista...
    if indice + cantidad_publicaciones_mostrar > len(scrapper.entrada.obtener_usuario(usuario_info).publicaciones):
        cantidad_publicaciones_mostrar = len(scrapper.entrada.obtener_usuario(usuario_info).publicaciones)


    if elegir:
        TEXTO = "👇 Elige las publicaciones que serán compartidas en Facebook 👇\n\n"
    else:
        if scrapper.cola["uso"] == m.from_user.id:

           TEXTO = "👇 Lista de Publicaciones Creadas 👇\n\nToca en alguna para ver más información de ella\n\n<b>Nota IMPORTANTE</b>:\nActualmente estoy PUBLICANDO, no puedes ni agregar ni ELIMINAR publicaciones hasta que no termine o hasta que canceles la operación (para cancelar envíame /cancelar)" 

        else:

            TEXTO = "👇 Lista de Publicaciones Creadas 👇\n\nToca en alguna para ver más información de ella / eliminarla"


    markup = InlineKeyboardMarkup(row_width=1)

    for publicacion in scrapper.entrada.obtener_usuario(usuario_info).publicaciones[indice : indice + cantidad_publicaciones_mostrar]:
        
        if elegir:
            markup.add(InlineKeyboardButton("✅ " + publicacion.titulo if publicacion in scrapper.temp_dict[usuario_info]["obj_publicacion"] else publicacion.titulo, callback_data="publicar/elegir/{}".format(scrapper.entrada.obtener_usuario(usuario_info).publicaciones.index(publicacion))))

        else:
            markup.add(InlineKeyboardButton(publicacion.titulo, callback_data="p/w/{}".format(scrapper.entrada.obtener_usuario(usuario_info).publicaciones.index(publicacion))))

    markup.row_width = 1
    

    markup.row(InlineKeyboardButton("◀", callback_data="p/wl/{}".format(0 if indice - cantidad_publicaciones_mostrar < 0 else indice - cantidad_publicaciones_mostrar)), InlineKeyboardButton("▶", callback_data= "p/wl/{}".format(indice + cantidad_publicaciones_mostrar)))

    if elegir:
        if scrapper.temp_dict[usuario_info]["obj_publicacion"]:
            markup.row(InlineKeyboardButton("✅ Publicar Seleccionados", callback_data="publicar/elegir/publicar"))
        
        markup.row(InlineKeyboardButton("🔙 Volver atrás", callback_data="publicar/elegir/b"))

    else:
        markup.row(InlineKeyboardButton("🔙 Volver atrás", callback_data="p/wl/b"))


    try:
        if m.caption:
            bot.edit_message_caption(TEXTO, m.chat.id, m.message_id, reply_markup=markup)

        else:
            bot.edit_message_text(TEXTO, m.chat.id, m.message_id, reply_markup=markup)

    except:
        bot.send_message(m.chat.id, TEXTO, reply_markup=markup)

        

    return

def user_folder(user, comprobar=False):
    user = str(user)
    carpeta_destino = gettempdir()
    # carpeta_destino = main_folder()
    
    if not "user_archive" in os.listdir(carpeta_destino):

        if comprobar:
            return False

        os.mkdir(os.path.join(carpeta_destino, "user_archive"))
        os.mkdir(os.path.join(carpeta_destino, "user_archive", user))
        
    if not list(filter(lambda file: file.startswith(user), os.listdir(os.path.join(carpeta_destino, "user_archive")))):

        if comprobar:
            return False

        os.mkdir(os.path.join(carpeta_destino, "user_archive",  user))

    else:
        
        if comprobar:
            return True
        
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


def handlers(bot, user , msg , info, scrapper : dict , **kwargs):    
    temp_dict = scrapper.temp_dict.copy()
    msg = m_texto(msg, True)

    if kwargs.get("file"):
        if kwargs.get("markup"):
            try:
                temp_dict[user]["msg"] = bot.send_photo(user, kwargs.get("file"), caption=msg, reply_markup=kwargs.get("markup"))

            except:
                temp_dict[user]["msg"] = bot.send_photo(user, kwargs.get("file"), caption=msg, reply_markup=kwargs.get("markup"), parse_mode=False)
            
        else:
            try:
                temp_dict[user]["msg"] = bot.send_photo(user, kwargs.get("file"), caption=msg)
            except:
                temp_dict[user]["msg"] = bot.send_photo(user, kwargs.get("file"), caption=msg, parse_mode = False)
        
    else:
        if kwargs.get("markup"):
            try:
                temp_dict[user]["msg"] = bot.send_message(user, msg, reply_markup=kwargs.get("markup"))

            except:
                temp_dict[user]["msg"] = bot.send_message(user, msg, reply_markup=kwargs.get("markup"), parse_mode = False)
        
        else:
            try: 
                temp_dict[user]["msg"] = bot.send_message(user, msg)
            except:
                temp_dict[user]["msg"] = bot.send_message(user, msg, parse_mode = False)
    

    temp_dict[user]["completed"] = False   

    match info:

        case "set_env_vars":
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.set_env_vars, bot, msg, scrapper)
        
        case "user":
        
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.get_user, bot,user, info, temp_dict, diccionario=temp_dict, mensaje_editar=temp_dict[user]["msg"])
            
        case "password":
            
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.get_user, bot,user, info, temp_dict, diccionario=temp_dict, mensaje_editar=temp_dict[user]["msg"])
            
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

        case "whats_verificacion":

            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.whats_verificacion, bot,user, info, temp_dict)

        case "correo_o_numero_verificacion":
            
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.correo_o_numero_verificacion, bot,user, info, temp_dict)

        case "email_verification":
            
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.email_verification,bot,user, info, temp_dict)
            

        case "bucle_publicacion":
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.repetir_bucle, bot,user, info, temp_dict)

    

            
            
    while True:
        
        if info == "set_env_vars":

            if scrapper.env:
                break
            
            else:
                time.sleep(2)

        else:
            if temp_dict[user]["completed"]:
                break

            else:
                scrapper.temp_dict[user]["if_cancelar"]()
                time.sleep(2)

        

    
    del temp_dict[user]["completed"], temp_dict[user]["msg"]
    
    scrapper.temp_dict[user].update(temp_dict[user])

    if temp_dict[user]["res"] == "/cancelar":
        liberar_cola(scrapper, user, scrapper.bot)
        return
    
    return temp_dict[user]["res"]