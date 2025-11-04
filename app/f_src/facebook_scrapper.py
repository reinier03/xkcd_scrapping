import time 
from traceback import format_exc
import os
import dill
import random
import re
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, InvalidSelectorException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from pymongo import MongoClient
import tempfile
import shutil
import sys
import json
import requests
import traceback
import urllib3

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from tb_src.main_classes import scrapping as scrapping
from tb_src.main_classes import *
from tb_src.usefull_functions import *
from f_src.chrome_driver import *
import f_src
from tb_src.usefull_functions import *



    
def esperar(scrapper: scrapping, etiqueta, elementos, selector="css", intentos=2):
    '''
    Esta funcion se asegura de que los elementos están disponibles en el DOM
    si no se cumplen las condiciones, se espera 5 segundos y se vuelve a intentar
    '''
    contador = 1
    

    while True:
        try:
            match selector.lower():
                case "css":
                    e = scrapper.wait.until(ec.any_of(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, etiqueta)) >= elementos + 1))

                case "xpath":
                    e = scrapper.wait.until(ec.any_of(lambda driver: len(driver.find_elements(By.XPATH, etiqueta)) >= elementos + 1))

        except IndexError:
            if contador >= intentos:
                raise Exception("Ingresaste un índice no válido")
            pass
        
        except:
            pass
            
        finally:
            try:
                if e == True:
                    return ("ok", scrapper.find_elements(By.CSS_SELECTOR, etiqueta)[elementos])
            
            except:
                pass
            
            if contador >= intentos:
                raise Exception("no se han obtenido la etiqueta: " + str(etiqueta))

            else:
                contador += 1
                time.sleep(5)

def configurar_idioma(scrapper: scrapping, user: int):
    scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'body')))

    try:
        scrapper.wait_s.until(ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "English")]')))

    except:
        #clickear en el elemento del idioma
        try:
            scrapper.wait_s.until(ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "{}")]'.format(re.search(r"\w+ [(]\D+[)]", scrapper.find_element(By.CSS_SELECTOR, "body").text).group().split("\n")[0]))))

            scrapper.find_element(By.XPATH, '//*[contains(text(), "{}")]'.format(re.search(r"\w+ [(]\D+[)]", scrapper.click(scrapper.find_element(By.CSS_SELECTOR, "body").text).group().split("\n")[0])))


        except:
            return False

        scrapper.wait.until(ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "English (US)")]')))
        scrapper.click(scrapper.find_element(By.XPATH, '//*[contains(text(), "English (US)")]/..'))

        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'body')))

        try:
            scrapper.temp_dict[user]["res"] = scrapper.wait.until(ec.any_of(
                ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Usar otro perfil")]')),
                ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Use another profile")]')),
                ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "I already have an account")]')),
                ec.visibility_of_element_located((By.CSS_SELECTOR, "input#m_login_email"))
            ))

            if scrapper.temp_dict[user]["res"].text in ["I already have an account"]:
                scrapper.click(scrapper.temp_dict[user]["res"])

        except:
            pass

    return True

def entrar_facebook(scrapper: scrapping, user, cargar_loguin = False):
    """
    Carga la página de Facebook y quita la presentacion
    """
    


    if not "login" in scrapper.driver.current_url or cargar_loguin:
        scrapper.load("https://m.facebook.com/login/")
    
    # if load_url:

    #     load(scrapper, "https://m.facebook.com/login/")
                
    # else:
    #     load(scrapper, "https://facebook.com")
    
    scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))
    
    scrapper.temp_dict[user]["res"] = scrapper.wait.until(ec.any_of(
        ec.visibility_of_element_located((By.CSS_SELECTOR, "input#m_login_email")),
        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "I already have an account")]')),
        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Ya tengo una cuenta")]')),
        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Usar otro perfil")]')),
        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Use another profile")]'))
    ))

    if scrapper.temp_dict[user]["res"].text in ["I already have an account", "Ya tengo una cuenta"]:
    
        #A veces aparecerá una presentacion de unirse a facebook, le daré a que ya tengo una cuenta...
        configurar_idioma(scrapper, user)

        scrapper.temp_dict[user]["res"] = scrapper.wait_s.until(ec.any_of(
            ec.visibility_of_element_located((By.CSS_SELECTOR, "input#m_login_email")),
            ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "I already have an account")]')),
            ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Ya tengo una cuenta")]'))
        ))

        if scrapper.temp_dict[user]["res"].get_attribute("id"):
            if scrapper.temp_dict[user]["res"].get_attribute("id") == "m_login_email":
                return True

        scrapper.click(scrapper.temp_dict[user]["res"])
        return entrar_facebook(scrapper, user, cargar_loguin)



    elif scrapper.temp_dict[user]["res"].text.strip() in ["Usar otro perfil", "Use another profile"]:
        if not scrapper.temp_dict[user].get("perfil_seleccionado"):
            scrapper.click(scrapper.temp_dict[user]["res"])
            scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'input#m_login_email')))


    return True
    
def loguin(scrapper: scrapping, user, bot, **kwargs):

    """
    Si no se proporciona un user_id, se creará uno nuevo
    
    Hace loguin en Facebook, determinará si hacer loguin desde cero o no si se le proporciona un user y si hay algún archivo de ese usuario en la BD
    """

    
    #en caso de que hayan cookies y haya un perfil seleccionado para publicar pero no estemos en la ventana de login
    if scrapper.temp_dict[user].get("perfil_seleccionado"):    

        
        scrapper.temp_dict[user]["res"] = seleccionar_perfil(scrapper, user)

        if not scrapper.temp_dict[user]["res"][0] and scrapper.temp_dict[user]["res"][1] == "contrasena incorrecta":

            return loguin_cero(scrapper, user, bot)
        

        elif not scrapper.temp_dict[user]["res"][0] and isinstance(scrapper.temp_dict[user]["res"][1], WebElement):
            
            scrapper.temp_dict[user]["user"] = scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user].get("perfil_seleccionado")).usuario
            scrapper.temp_dict[user]["password"] = scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user].get("perfil_seleccionado")).contrasena
            
            return loguin_cero(scrapper, user, bot)

        else:        
            return ("ok", "loguin satisfecho")


    else:
        return loguin_cero(scrapper, user, bot)

    # elif scrapper.driver.get_cookies() and not scrapper.temp_dict[user].get("perfil_seleccionado"):

    #     scrapper.wait.until(ec.any_of(
    #         ec.visibility_of_element_located((By.CSS_SELECTOR, 'input#m_login_email')),
    #         ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Usar otro perfil")]')),
    #         ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Use another profile")]'))
    #     )).click()

    #     return loguin_cero(scrapper, user, bot)     
    

    # else:
    #     entrar_facebook(scrapper, user)

    #     return loguin_cero(scrapper, user, bot)        
                

def loguin_cero(scrapper: scrapping, user, bot : telebot.TeleBot, **kwargs):

    if not scrapper.find_element(By.CSS_SELECTOR, "input#m_login_email", True):
        entrar_facebook(scrapper, user, True)

    else:
        entrar_facebook(scrapper, user)

    configurar_idioma(scrapper, user)

    scrapper.temp_dict[user]["res"] = scrapper.wait.until(ec.any_of(
        ec.visibility_of_element_located((By.CSS_SELECTOR, 'input#m_login_email')),
        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Usar otro perfil")]')),
        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Use another profile")]'))
    ))

    scrapper.click(scrapper.temp_dict[user]["res"])

    scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "input#m_login_email")))

    scrapper.click(scrapper.find_elements(By.CSS_SELECTOR, "input")[0])

    if re.search(r"\w+", scrapper.find_elements(By.CSS_SELECTOR, "input")[0].get_attribute("value")):
        scrapper.click(scrapper.find_elements(By.CSS_SELECTOR, "input")[0])
        scrapper.click(scrapper.find_element(By.CSS_SELECTOR, 'div[aria-label="Clear Mobile number or email text"]'))
        scrapper.click(scrapper.find_elements(By.CSS_SELECTOR, "input")[0])
    
    if not scrapper.temp_dict[user].get("user"):
        handlers(bot, user, "Introduce a continuación tu <b>Correo</b> o <b>Número de Teléfono</b> (agregando el código de tu país por delante ej: +53, +01, +52, etc) con el que te autenticas en Facebook: ", "user", scrapper)

        ActionChains(scrapper.driver).send_keys_to_element(scrapper.find_elements(By.CSS_SELECTOR, "input")[0], scrapper.temp_dict[user]["user"]).perform()

        for i in range(3):

            try:
                scrapper.wait_s.until(ec.any_of(
                    lambda driver, scrapper=scrapper: scrapper.find_elements(By.CSS_SELECTOR, "input")[0].get_attribute("value") == scrapper.temp_dict[user]["user"],
                    lambda driver, scrapper=scrapper: scrapper.find_element(By.CSS_SELECTOR, "input#m_login_email").get_attribute("value") == scrapper.temp_dict[user]["user"],
                ))

                break

            except:
                if i >= 2:
                    raise Exception("No se pudo introducir el usuario")

                elif i % 2:
                    scrapper.find_elements(By.CSS_SELECTOR, "input")[0].send_keys(scrapper.temp_dict[user]["user"])

                else:
                    ActionChains(scrapper.driver).send_keys_to_element(scrapper.find_element(By.CSS_SELECTOR, "input#m_login_email"), scrapper.temp_dict[user]["user"]).perform()
            


    # scrapper.temp_dict[user]["e"].send_keys(scrapper.temp_dict[user]["user"])
    
    
    #-----------------obtener password para loguin---------------
    # scrapper.temp_dict[user]["e"] = driver.find_element(By.ID, "m_login_password")
    
    if not scrapper.temp_dict[user].get("password"):
        handlers(bot, user, "Introduce a continuación la contraseña", "password", scrapper)
        
        ActionChains(scrapper.driver).send_keys_to_element(scrapper.find_elements(By.CSS_SELECTOR, "input")[1], scrapper.temp_dict[user]["password"]).perform()

        for i in range(3):

            try:
                scrapper.wait_s.until(ec.any_of(
                    lambda driver, scrapper=scrapper: scrapper.find_elements(By.CSS_SELECTOR, "input")[1].get_attribute("value") == scrapper.temp_dict[user]["password"],
                    lambda driver, scrapper=scrapper: scrapper.find_element(By.CSS_SELECTOR, "input#m_login_password").get_attribute("value") == scrapper.temp_dict[user]["password"],
                ))

                break

            except:
                if i >= 2:
                    raise Exception("No se pudo introducir el usuario")

                elif i % 2:
                    scrapper.find_elements(By.CSS_SELECTOR, "input")[1].send_keys(scrapper.temp_dict[user]["password"])

                else:
                    ActionChains(scrapper.driver).send_keys_to_element(scrapper.find_element(By.CSS_SELECTOR, "input#m_login_password"), scrapper.temp_dict[user]["password"]).perform()


        bot.send_message(user, m_texto("Muy bien, a continuación comprobaré si los datos son correctos\n\n<b>Por favor, espera un momento...</b>"))


    scrapper.temp_dict[user]["url_actual"] = scrapper.driver.current_url

    
    
    # scrapper.temp_dict[user]["e"].send_keys(scrapper.temp_dict[user]["password"])
    
    scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-anchor-id="replay"]')))

    # scrapper.find_element(By.CSS_SELECTOR, 'div[data-anchor-id="replay"]').click()
    

    try:
        scrapper.temp_dict[user]["res"] = scrapper.wait_s.until(ec.any_of(
            ec.element_to_be_clickable((By.XPATH, '//span[contains(text(), "Log in")]')),
            ec.element_to_be_clickable((By.XPATH, '//span[contains(text(), "Iniciar")]')),
        ))

        scrapper.click(scrapper.temp_dict[user]["res"])

    except:
        scrapper.click(scrapper.find_elements(By.CSS_SELECTOR, 'div[role="button"]')[2])
        

    try:
        scrapper.wait.until(ec.url_changes(scrapper.temp_dict[user]["url_actual"]))
        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'body')))
    except:
        pass
    
    

    try:
        #cuando no introduces bien ninguno de tus datos:
        if scrapper.wait_s.until(ec.any_of(
            ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Wrong")]')),
            ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[class="wbloks_73"]')),
            ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Invalid username or password")]')),
            ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "incorrect")]'))
        )):
            
            if scrapper.temp_dict[user].get("perfil_seleccionado"):
                scrapper.bot.send_message(user, m_texto("ERROR Los datos que tenía de esta cuenta no funcionan...,cambiaste algo?\nLos datos son los siguiente:\n\nUsuario: <code>{}</code>\nContraseña <code>{}</code>\n\nA continuación haré un loguin desde cero, introduce nuevos datos o los datos de dicha cuenta actualizados").format(scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user].get("perfil_seleccionado")).usuario ,scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user].get("perfil_seleccionado")).contrasena))

                del scrapper.temp_dict[user]["password"]
                del scrapper.temp_dict[user]["user"]
                return loguin_cero(scrapper, user, bot)

            else:
                bot.send_photo(user, telebot.types.InputFile(make_screenshoot(scrapper.driver, user)), "Al parecer los datos que me has enviado son incorrectos\nTe he enviado una captura de lo que me muestra Facebook\n\nPor favor ingrese <b>correctamente</b> sus datos otra vez...")
                del scrapper.temp_dict[user]["password"]
                del scrapper.temp_dict[user]["user"]
                return loguin_cero(scrapper, user, bot)
            
    except:
        pass
    

    doble_auth(scrapper, user, bot)
    # if "No se ha podido dar click en el botón de doble autenticación" in scrapper.temp_di

    try:
        #error de loguin validacion
        if scrapper.wait.until(ec.any_of(lambda driver: driver.find_elements(By.CSS_SELECTOR, 'div#screen-root') and not "save-device" in driver.current_url)):

            # scrapper.temp_dict[user]["credenciales"] = {"user": scrapper.temp_dict[user]["user"], "password": scrapper.temp_dict[user]["password"]}

            scrapper.guardar_datos(user)

            
            
            return ("ok", "loguin desde cero satisfactorio :)")

        
    except:
        
        bot.send_photo(user, telebot.types.InputFile(make_screenshoot(scrapper.driver, user)) , m_texto("No has introducido tus datos correctamente, vuelve a intentarlo"))

        del scrapper.temp_dict[user]["password"]
        del scrapper.temp_dict[user]["user"]

        return loguin_cero(scrapper, user, bot)
    



def seleccionar_perfil(scrapper : scrapping, user):
    """
    Devuelve una tupla con True de primer valor si se ha seleccionado la cuenta exitosamente
    Devuelve una tupla con False de primer valor si la cuenta seleccionada no se encuentra por alguna razón y devuelve el WebElement() de el input para el username
    """
    

    scrapper.facebook_logout()
    
    entrar_facebook(scrapper, user)

    scrapper.temp_dict[user]["res"] = scrapper.wait.until(ec.any_of(
        ec.visibility_of_element_located((By.CSS_SELECTOR, 'input#m_login_email')),
        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Usar otro perfil")]')),
        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Use another profile")]'))
    ))

    if scrapper.temp_dict[user]["res"].text in ["Usar otro perfil", "Use another profile"]:

        if scrapper.temp_dict[user].get("perfil_seleccionado"):
            scrapper.temp_dict[user]["url_actual"] = scrapper.driver.current_url

            try:
                scrapper.click(scrapper.find_element(By.XPATH, '//*[contains(text(), "{}")]'.format(scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user].get("perfil_seleccionado")).perfil_principal)))

            except:
                #cuando la cuenta no se encuentre (por alguna razón)
                return (False, scrapper.temp_dict[user]["res"])

            
            try:
                #en caso de que haya solamente 1 perfil logueado
                scrapper.temp_dict[user]["res"] = WebDriverWait(scrapper.driver, 3).until(ec.any_of(
                    ec.visibility_of_element_located(((By.XPATH, '//*[contains(text(), "Continuar")]'))),
                    ec.visibility_of_element_located(((By.XPATH, '//*[contains(text(), "Continue")]')))
                ))

                scrapper.click(scrapper.temp_dict[user]["res"])

            except:
                pass
            
            #en caso de que me pida nuevamente la constraseña de la cuenta:
            try:
                scrapper.temp_dict[user]["res"] = scrapper.wait_s.until(ec.any_of(
                    ec.visibility_of_element_located((By.XPATH, '//*[contains(@aria-label , "Contraseña")]')),
                    ec.visibility_of_element_located((By.XPATH, '//*[contains(@aria-label , "Password")]'))
                ))

            except:
                pass

            else:
                scrapper.click(scrapper.temp_dict[user]["res"])

                scrapper.temp_dict[user]["res"].send_keys(scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user].get("perfil_seleccionado")).contrasena)

                WebDriverWait(scrapper.driver)
                scrapper.temp_dict[user]["res"] = scrapper.wait.until(ec.any_of(
                    ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Iniciar")]')),
                    ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Log")]'))
                ))

                scrapper.click(scrapper.temp_dict[user]["res"])
                
                #si la contraseña es incorrecta:
                try:
                    scrapper.temp_dict[user]["res"] = scrapper.wait_s.until(ec.any_of(
                        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "incorrecta")]')),
                        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Wrong password")]'))
                    ))

                    scrapper.bot.send_message(user, m_texto("ERROR La contraseña que tengo de esta cuenta al parecer ya no funciona, la cambiaste?\nLa contraseña que tengo es esta: <code>{}</code>\n\nA continuación haré un loguin desde cero, introduce nuevos datos o los datos de dicha cuenta actualizados").format(scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user].get("perfil_seleccionado")).contrasena))
                    
                    del scrapper.temp_dict[user]["perfil_seleccionado"]
                    return (False, "contrasena incorrecta")

                except:
                    pass

            
                #Mirar si me pide doble autenticación
            try:
                scrapper.wait_s.until(ec.any_of(
                    ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Try another way")]')),
                    ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Usar otro")]')),
                    ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Consulta tus notificaciones")]')),
                    ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Check your notifications")]')),
                    ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "email")]')),
                    lambda driver: driver.current_url.endswith("#")
                ))

                
                doble_auth(scrapper, user, scrapper.bot)

            except:
                pass


            scrapper.wait.until(ec.all_of(
                lambda driver: not re.search("save-device", driver.current_url),
                ec.visibility_of_element_located((By.CSS_SELECTOR, 'div#screen-root')),
            ))
                    


            return (True, "cuenta seleccionada correctamente")
        

        else:
            return (False, scrapper.temp_dict[user]["res"])


    else:
        return (False, scrapper.temp_dict[user]["res"])

def doble_auth(scrapper: scrapping , user, bot: telebot.TeleBot):

    def doble_whatsapp(scrapper: scrapping, user, bot: telebot.TeleBot):
        print("ahora toca una verificación por whatsapp")

        handlers(bot, user, "Facebook ha enviado un código de confirmación al WhatsApp del número perteneciente a esta cuenta\n(El número en cuestión es: <b>{}</b>)\n\nVe al WhatsApp de este número, copia el código y pégalo aquí...".format(re.search(r"[*].*", scrapper.temp_dict[user]["e"]).group()), "whats_verificacion", scrapper)
        
        while True:
            #el código siempre posee 6 dígitos
            if len(scrapper.temp_dict[user]["res"]) == 6:

                scrapper.find_element(By.CSS_SELECTOR, "input")
                scrapper.find_element(By.CSS_SELECTOR, "input").send_keys(scrapper.temp_dict[user]["res"])
                scrapper.temp_dict[user]["res"] = scrapper.wait.until(ec.any_of(
                    ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Continue")]')),
                    ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Continuar")]'))
                ))

                scrapper.click(scrapper.temp_dict[user]["res"])

                try:

                    scrapper.temp_dict[user]["res"] = scrapper.wait_s.until(ec.any_of(
                        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "correct or try a new one")]')),
                        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Forgot")]')),
                        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "forgot")]')),
                        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "correcto o prueba con otro")]')),
                        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Wrong")]')),
                        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "wrong")]')),
                        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "incorrectas")]')),
                        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Incorrectas")]'))
                    ))

                    if list(filter(lambda palabra, scrapper=scrapper, user=user: re.search(palabra , scrapper.temp_dict[user]["res"].text.lower()), ["wrong", "incorrectas", "forgot", "try", "try a new one", "prueba con otro"])):

                        bot.send_photo(user, telebot.types.InputFile(make_screenshoot(scrapper.driver, user)) , m_texto("No has introducido tus datos correctamente, vuelve a intentarlo"))

                        del scrapper.temp_dict[user]["user"]
                        del scrapper.temp_dict[user]["password"]

                        return loguin_cero(scrapper, user, bot)


                    for i in range(3):
                        scrapper.click(scrapper.find_element(By.CSS_SELECTOR, 'input'))
                        scrapper.click(scrapper.find_elements(By.CSS_SELECTOR, 'img[data-bloks-name="bk.components.Image"][class="wbloks_1"]')[2])

                        if scrapper.find_element(By.CSS_SELECTOR, 'input').get_attribute("value") == "":
                            break

                        elif not i >= 2:
                            scrapper.temp_dict[user]["res"] = Exception("No se pudo vaciar el campo de texto del codigo de whatsapp")

                except:
                    if isinstance(scrapper.temp_dict[user]["res"], Exception):
                        raise scrapper.temp_dict[user]["res"]
                    
                    return ("ok", "loguin satisfactorio")


            handlers(bot, user, "❌El código que enviaste es incorrecto ¡Prueba de nuevo!❌\n\nFacebook ha enviado un código de confirmación al WhatsApp del número perteneciente a esta cuenta\n(El número en cuestión es: <b>{}</b>)\n\nVe al WhatsApp de este número, copia el código y pégalo aquí...".format(re.search(r"[*].*", scrapper.temp_dict[user]["e"]).group()), "whats_verificacion", scrapper)

            continue
                # return loguin(scrapper, user, bot)


    def doble_auth_codigo(scrapper: scrapping , user, bot: telebot.TeleBot):
    # e = scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))

        
        
        
        scrapper.wait.until(ec.any_of(lambda driver: driver.find_element(By.XPATH, '//*[contains(text(), "Backup code")]')))

        #aqui le doy click a el metodo de auth que en este caso sería por codigo de respaldo

        scrapper.click(scrapper.find_element(By.XPATH, '//*[contains(text(), "Backup code")]'))

        #le doy click a continuar
        scrapper.click(scrapper.find_element(By.XPATH, '//*[contains(text(), "Continue")]'))
        # scrapper.find_elements(By.CSS_SELECTOR, 'div[data-bloks-name="bk.components.Flexbox"][role="button"][tabindex="0"]')[1].click()

        #el siguiente elemento es el input en el que va el código
        scrapper.wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, 'input[inputmode="numeric"]')))
        
        scrapper.temp_dict[user]["e"] = scrapper.find_element(By.CSS_SELECTOR, 'input[inputmode="numeric"]')
        
        
        handlers(bot, user, "A continuación, introduce uno de los códigos de respaldo de Facebook\n\n(Estos códigos son de 8 dígitos numéricos y puedes obtenerlos en el centro de cuentas en los ajustes de tu cuenta de Facebook)" , "codigo_respaldo", scrapper, markup=ForceReply())
        
        #para borrar los espacios en el codigo de respaldo
        if re.search(r"\D", scrapper.temp_dict[user]["res"].text):
            scrapper.temp_dict[user]["res"].text = scrapper.temp_dict[user]["res"].text.replace(re.search(r"\D+", scrapper.temp_dict[user]["res"].text).group(), "").strip()

        for i in scrapper.temp_dict[user]["res"].text:
            scrapper.temp_dict[user]["e"].send_keys(i)
            time.sleep(0.5)
        
        
        scrapper.temp_dict[user]["url_actual"] = scrapper.driver.current_url
        

        #click en el boton de continuar
        scrapper.click(scrapper.find_element(By.XPATH, '//*[contains(text(), "Continue")]'))
        
        

        # try:
        #     #este mensaje se muestra cuando el código es incorrecto
        #     if scrapper.wait_s.until(ec.any_of(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, 'span[data-bloks-name="bk.components.TextSpan"]')) > 8)):
                
        #         bot.send_message(user, "🆕 Mensaje de Información\n\nHas Introducido un código incorrecto!\n\nEspera un momento para volver a intentarlo...")
                
        #         return loguin_cero(scrapper, user, bot)
                
        # except:
        #     pass
        
        # #esperar a que no esté el botón
        # scrapper.wait.until(ec.invisibility_of_element_located((By.CSS_SELECTOR, 'div[class="xod5an3 xg87l8a"]')))
        
        
        
        
        return "ok"
    

    def doble_auth_email_verification(scrapper: scrapping, user, bot):
        
        
        scrapper.temp_dict[user]["url_actual"] = scrapper.driver.current_url
                
        # scrapper.find_element(By.XPATH, '//*[contains(text(), "Get a new code")]').click()

        # scrapper.temp_dict[user]["email"] = scrapper.find_element(By.XPATH, '//*[contains(text(), "code we sent")]').text.split("to")[-1].strip()

        # 

        handlers(bot, user, "A continuación, ingresa el código númerico que ha sido enviado al email vinculado a esta cuenta para finalizar el loguin...","email_verification", scrapper)

        scrapper.find_element(By.CSS_SELECTOR, 'input').send_keys(scrapper.temp_dict[user]["res"].strip())

        scrapper.temp_dict[user]["res"] = scrapper.wait.until(ec.any_of(
            ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Continue")]')),
            ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Continuar")]')),
        ))
        
        scrapper.click(scrapper.temp_dict[user]["res"])
        

        return "ok"

    
    try:

        scrapper.wait_s.until(ec.any_of(
            ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Try another way")]')),
            ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Usar otro")]')),
            ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Consulta tus notificaciones")]')),
            ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Check your notifications")]')),
            ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "email")]')),
            lambda driver: driver.current_url.endswith("#")
        ))

    except:
        pass

    else:

        scrapper.temp_dict[user]["res"] = scrapper.wait_s.until(ec.any_of(
            ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Try another way")]')),
            ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Usar otro")]')),
            ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "email")]'))
        ))



        if scrapper.temp_dict[user]["res"].text in "Try another way" or "Usar otro" in scrapper.temp_dict[user]["res"].text:
            try:
                #Si este elemento no está es que aún está en el loguin debido a que los datos introducidos fueron incorrectos (es el mismo de arriba)
                scrapper.click(scrapper.find_element(By.XPATH, '//*[contains(text(), "{}")]'.format(scrapper.temp_dict[user]["res"].text)))
                
                scrapper.wait_s.until(ec.any_of(
                    ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Choose a way to confirm")]')),
                    ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Elige un método para confirmar tu identidad")]')),
                    
                ))

                scrapper.temp_dict[user]["res"] = scrapper.wait_s.until(ec.any_of(
                    ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "WhatsApp")]')),
                    ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "email")]')),
                    ))


                if scrapper.temp_dict[user]["res"].text == "WhatsApp":

                    scrapper.click(scrapper.temp_dict[user]["res"])
                    scrapper.temp_dict[user]["e"] = scrapper.wait.until(ec.any_of(
                        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "send a code to")]')),
                        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Enviaremos un código")]'))
                    )).text
                    
                    scrapper.temp_dict[user]["res"] = scrapper.wait.until(ec.any_of(
                        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Continue")]')),
                        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Continuar")]')),
                    ))

                    scrapper.click(scrapper.temp_dict[user]["res"])
                    

                    scrapper.wait.until(ec.any_of(
                        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Check your WhatsApp messages")]')),
                        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Revisa tus mensajes de WhatsApp")]'))
                    ))

                    doble_whatsapp(scrapper, user, bot)
                    

                else:
                    try:
                        scrapper.click(scrapper.find_element(By.XPATH, '//*[contains(text(), "Email")]'))
                        scrapper.temp_dict[user]["res"] = scrapper.wait.until(ec.any_of(
                            ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Continue")]')),
                            ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Continuar")]'))
                        ))

                        scrapper.click(scrapper.temp_dict[user]["res"])

                        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'body')))

                        print("Haremos la doble autenticación enviando el código al correo")
                        doble_auth_email_verification(scrapper, user, bot)   
                    except:
                        print("Haremos la doble autenticación con los códigos de recuperación")
                        doble_auth_codigo(scrapper, user, bot)

                    scrapper.temp_dict[user]["url_actual"] = scrapper.driver.current_url
            except Exception as err:

                if scrapper.temp_dict[user].get("password"):
                    del scrapper.temp_dict[user]["user"]
                    del scrapper.temp_dict[user]["password"]

                    bot.send_photo(user, telebot.types.InputFile(make_screenshoot(scrapper.driver, user)) ,"❌ERROR❌\n\nHas introducido tus datos de loguin incorrectamente...\nPor favor, vuelve a intentarlo luego del próximo mensaje")

                    return loguin_cero(scrapper, user, bot)


                else:
                    raise err
            
                
                
        
                
        

        #hay veces que solamente te da como ÚNICA opción el email para poder verificar tu autenticidad
        elif "email" in scrapper.temp_dict[user]["res"].text:
            if scrapper.find_element(By.XPATH, '//*[contains(text(), "email")]'):
                print("Haremos la doble autenticación enviando el código al correo")
                doble_auth_email_verification(scrapper, user, bot)            
        

        
        
        try:
            
            scrapper.wait.until(ec.url_changes(scrapper.temp_dict[user]["url_actual"]))
            

        except:
            pass


    scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'body')))
                        
    #save-device = sustituto de remember_browser
    scrapper.temp_dict[user]["res"] = scrapper.wait.until(ec.any_of(
        ec.visibility_of_element_located((By.CSS_SELECTOR, 'div#screen-root')),
        lambda driver: "save-device" in driver.current_url,
    ))

    if not isinstance(scrapper.temp_dict[user]["res"], bool):
        
        if "screen-root" in scrapper.temp_dict[user]["res"].get_attribute("id").lower():
            
            if scrapper.temp_dict[user].get("perfil_seleccionado"):
                bot.send_message(user, m_texto("Ok, el codigo introducido es correcto\n\nEmpezaré a publicar lo antes posible, espera un momento..."), reply_markup=telebot.types.ReplyKeyboardRemove())

            else:
                bot.send_message(user, m_texto("Ok, el codigo introducido es correcto\n\nVoy a entrar a Facebook, espera un momento..."), reply_markup=telebot.types.ReplyKeyboardRemove())

            return ("ok", "se ha dado click en confiar dispositivo")
    


    if not "save-device" in scrapper.driver.current_url:
        
        
        bot.send_message(user, m_texto("Has Introducido un código incorrecto! Espera un momento para volverlo a intentar..."), reply_markup=telebot.types.ReplyKeyboardRemove())
        
        if not scrapper.temp_dict[user].get("perfil_seleccionado"):
            return loguin_cero(scrapper, user, bot)
    
        else:
            scrapper.driver.refresh()
            return seleccionar_perfil(scrapper, user)
    
    elif "save-device" in scrapper.driver.current_url:
        pass
    
    else:
        raise Exception("No se ha encontrado la pagina de confiar en este dispositivo?")
        
    

    #click en confiar en este dispositivo
    scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="button"]')))
    scrapper.click(scrapper.find_element(By.CSS_SELECTOR, 'div[role="button"]'))

    # scrapper.temp_dict[user]["info"] = bot.edit_message_text(text="🆕 Mensaje de Información\n\nOk, el codigo introducido es correcto", chat_id=user, message_id=scrapper.temp_dict[user]["info"].message_id)     
    
    if scrapper.temp_dict[user].get("perfil_seleccionado"):
        bot.send_message(user, m_texto("Ok, el codigo introducido es correcto\n\nEmpezaré a publicar lo antes posible, espera un momento..."), reply_markup=telebot.types.ReplyKeyboardRemove())

    else:
        bot.send_message(user, m_texto("Ok, el codigo introducido es correcto\n\nVoy a entrar a Facebook, espera un momento..."), reply_markup=telebot.types.ReplyKeyboardRemove())

    scrapper.wait.until(ec.any_of(lambda driver: driver.find_elements(By.CSS_SELECTOR, 'body')))

    try:
        scrapper.wait.until(ec.all_of(
            lambda driver: not "save-device" in driver.current_url,
            ec.visibility_of_element_located((By.CSS_SELECTOR, 'div#screen-root'))
        ))


    except:
        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-bloks-name="bk.components.Flexbox"][role="button"]')))

        scrapper.click(scrapper.find_element(By.CSS_SELECTOR, 'div[data-bloks-name="bk.components.Flexbox"][role="button"]'))

        scrapper.wait.until(ec.invisibility_of_element_located((By.CSS_SELECTOR, 'div[data-bloks-name="bk.components.Flexbox"][role="button"]')))

        scrapper.wait.until(ec.all_of(
            lambda driver: not "save-device" in driver.current_url,
            ec.visibility_of_element_located((By.CSS_SELECTOR, 'div#screen-root'))
        ))


    return ("ok", "se ha dado click en confiar dispositivo")





        

def obtener_texto(scrapper, user, contador, error: bool, aprobar=False):
    
    #---------------------------------------------cambiar para futuro-------------------------------------
    # try:
    #     scrapper.temp_dict[user]["publicacion"]["info"] = bot.edit_message_text("✅Se ha publicado en: " + str(len(scrapper.temp_dict[user]["publicacion"]["publicados"])) + " grupo(s)" + "\n⛔Han quedado incompletas en: " + str(len(scrapper.temp_dict[user]["publicacion"]["incompletas"])) + " grupo(s)" + "\n❌Se han producido errores en: " + str(len(scrapper.temp_dict[user]["publicacion"]["error"])) + " grupo(s)", user , scrapper.temp_dict[user]["publicacion"]["info"].message_id)
    # except:
    #     scrapper.temp_dict[user]["publicacion"]["info"] = bot.send_message(user, "✅Se ha publicado en: " + str(len(scrapper.temp_dict[user]["publicacion"]["publicados"])) + " grupo(s)" + "\n⛔Han quedado incompletas en: " + str(len(scrapper.temp_dict[user]["publicacion"]["incompletas"])) + " grupo(s)" + "\n❌Se han producido errores en: " + str(len(scrapper.temp_dict[user]["publicacion"]["error"])) + " grupo(s)")

    #     bot.pin_chat_message(scrapper.temp_dict[user]["publicacion"]["info"].chat.id , scrapper.temp_dict[user]["publicacion"]["info"].message_id, True)
    #---------------------------------------------cambiar para futuro-------------------------------------
        
    
    #4000 caracteres es el limite de telegram para los mensajes, si sobrepasa la cantidad tengo que enviar otro mensaje            



    if len(scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] + "❌ " + scrapper.temp_dict[user]["publicacion"]["nombre"] + "\n") >= 4000:
        
        
        if error == True:
            scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] = str(contador + 1).zfill(3) + "=> ❌ <code>" + scrapper.temp_dict[user]["publicacion"]["nombre"] + "</code> " 
        else:
            if aprobar:
                scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] = str(contador + 1).zfill(3) + "=> ⛔ <code>" + scrapper.temp_dict[user]["publicacion"]["nombre"] + "</code> " 
            else:
                scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] = str(contador + 1).zfill(3) + "=> ✅ <code>" + scrapper.temp_dict[user]["publicacion"]["nombre"] + "</code> "
            
        
        
        #para asegurarme de que hay que enviar un nuevo mensaje retorno "nuevo" y si es admin va a devolver el tiempo de demora
        if user == scrapper.admin:
            scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] = scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] + get_time(scrapper, user) + "\n"
            return ("nuevo", scrapper.temp_dict[user]["publicacion"]["texto_publicacion"])
        
        else:
            scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] = scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] + "\n"
            return ("nuevo", scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] + "\n")
            
    else:
        
        if error == True:
            scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] += str(contador + 1).zfill(3) + "=> ❌ <code>" + scrapper.temp_dict[user]["publicacion"]["nombre"] + "</code> "
            
        else:
            if aprobar:
                scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] += str(contador + 1).zfill(3) + "=> ⛔ <code>" + scrapper.temp_dict[user]["publicacion"]["nombre"] + "</code> "
            else:
                scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] += str(contador + 1).zfill(3) + "=> ✅ <code>" + scrapper.temp_dict[user]["publicacion"]["nombre"] + "</code> "

        
        if user == scrapper.admin:
            scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] = scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] + get_time(scrapper, user) + "\n"

            return ("no", scrapper.temp_dict[user]["publicacion"]["texto_publicacion"])
        
        else:
            scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] = scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] + "\n"

            return ("no", scrapper.temp_dict[user]["publicacion"]["texto_publicacion"])

    
def enviar_grupos(scrapper, user, bot: telebot.TeleBot, contador, resultantes_publicados: list):
    

    # if scrapper.temp_dict[user]["publicacion"]["nombre"] in scrapper.temp_dict[user]["publicacion"]["publicados"]:
    #     print(str((contador + 1)).zfill(3) + "=> ✅ " + str(scrapper.temp_dict[user]["publicacion"]["nombre"]))
    #     scrapper.temp_dict[user]["res"] = obtener_texto(False)

    # elif scrapper.temp_dict[user]["publicacion"]["nombre"] in scrapper.temp_dict[user]["publicacion"]["incompletas"]:
    #     print(str((contador + 1)).zfill(3) + "=> ⛔️ " + str(scrapper.temp_dict[user]["publicacion"]["nombre"]))
    #     scrapper.temp_dict[user]["res"] = obtener_texto(True, True)

    # elif scrapper.temp_dict[user]["publicacion"]["nombre"] in scrapper.temp_dict[user]["publicacion"]["error"]:
    #     print(str((contador + 1)).zfill(3) + "=> ❌ " + scrapper.temp_dict[user]["publicacion"]["nombre"])
    #     scrapper.temp_dict[user]["res"] = obtener_texto(True)

    if len(re.findall("True", str(resultantes_publicados))) == len(scrapper.temp_dict[user]["obj_publicacion"]):

        scrapper.temp_dict[user]["publicacion"]["publicados"].append(scrapper.temp_dict[user]["publicacion"]["nombre"])

        print(str((contador + 1)).zfill(3) + "=> ✅ " + str(scrapper.temp_dict[user]["publicacion"]["nombre"]))
        scrapper.temp_dict[user]["res"] = obtener_texto(scrapper , user, contador, False)

    elif len(re.findall("False", str(resultantes_publicados))) == len(scrapper.temp_dict[user]["obj_publicacion"]):
        
        scrapper.temp_dict[user]["publicacion"]["error"].append(scrapper.temp_dict[user]["publicacion"]["nombre"])

        print(str((contador + 1)).zfill(3) + "=> ❌ " + scrapper.temp_dict[user]["publicacion"]["nombre"])
        scrapper.temp_dict[user]["res"] = obtener_texto(scrapper , user, contador, True)

    else:
        scrapper.temp_dict[user]["publicacion"]["incompletas"].append(scrapper.temp_dict[user]["publicacion"]["nombre"])

        print(str((contador + 1)).zfill(3) + "=> ⛔️ " + str(scrapper.temp_dict[user]["publicacion"]["nombre"]))
        scrapper.temp_dict[user]["res"] = obtener_texto(scrapper , user, contador, True, True)


    if scrapper.temp_dict[user]["res"][0] == "nuevo":
        scrapper.temp_dict[user]["publicacion"]["msg_publicacion"] = bot.send_message(user, scrapper.temp_dict[user]["res"][1])

        bot.unpin_all_chat_messages(user)
        bot.pin_chat_message(user , scrapper.temp_dict[user]["publicacion"]["msg_publicacion"].message_id, True)

    else:

        if scrapper.temp_dict[user]["publicacion"].get("msg_publicacion"):
            try:
                scrapper.temp_dict[user]["publicacion"]["msg_publicacion"] = bot.edit_message_text(scrapper.temp_dict[user]["res"][1] , user, scrapper.temp_dict[user]["publicacion"]["msg_publicacion"].message_id)

            except Exception as e:
                if "specified new message content and reply markup are exactly the same as a current content and reply markup of the message" in str(e.args):
                    pass

        else:

            scrapper.temp_dict[user]["publicacion"]["msg_publicacion"] = bot.send_message(user, scrapper.temp_dict[user]["res"][1])

            bot.pin_chat_message(user , scrapper.temp_dict[user]["publicacion"]["msg_publicacion"].message_id, True)

    return

def publicacion(scrapper: scrapping, bot:telebot.TeleBot, user, load_url=True, contador = 0, **kwargs):


    # if "bookmarks" in scrapper.driver.current_url:
    #     scrapper.find_element(By.CSS_SELECTOR, 'div[role="button"]').click()

    scrapper.temp_dict[user]["if_cancelar"]()

    if scrapper.temp_dict[user].get("contador"):
        contador = scrapper.temp_dict[user]["contador"]

    if kwargs.get("diccionario"):
        scrapper.temp_dict = kwargs["diccionario"]

    if scrapper.entrada.obtener_usuario(user).plan.repetir and not scrapper.interrupcion and not scrapper.temp_dict[user]["c_r"] == 1:
        try:
            bot.edit_message_text(m_texto("A continuación, comenzaré a publicar en breve...\n\nEsta será la vez #<b>{}</b> que publicaré por todos los grupos disponibles". format(scrapper.temp_dict[user]["c_r"])), scrapper.temp_dict[user]["msg"].chat.id, scrapper.temp_dict[user]["msg"].message_id)

        except:
            bot.send_message(user, m_texto("A continuación, comenzaré a publicar en breve...\n\nEsta será la vez #<b>{}</b> que publicaré por todos los grupos disponibles". format(scrapper.temp_dict[user]["c_r"])))


    scrapper.temp_dict[user]["a"] = ActionChains(scrapper.driver, duration=0)

    scrapper.temp_dict[user]["tiempo_debug"] = []
    
    if not scrapper.temp_dict[user].get("publicacion"):
        scrapper.temp_dict[user]["publicacion"] = {"publicados" : [], "error" : [], "incompletas": [], "lista_grupos": [] ,"texto_publicacion": "Lista de Grupos en los que se ha Publicado:\n\n", "resultados_publicaciones": [], "msg_publicacion": None}
        
    scrapper.temp_dict[user]["publicacion"]["lista_grupos"] = []

    if scrapper.driver.current_url != "https://m.facebook.com/groups/":
        scrapper.load("https://m.facebook.com/groups/")

    #------------------obtener información para el scrolling--------------------------
    get_time_debug(scrapper, user)

    scrapper.temp_dict[user]["publicacion"]["lista_grupos"] = obtener_grupos(scrapper, user)

    if not scrapper.temp_dict[user]["publicacion"]["lista_grupos"]:

        scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "¡¡No había ningún grupo en la cuenta!! linea {}".format(traceback.extract_stack()[-1].lineno)))
            
        raise Exception("¡No hay ningún grupo al que publicar!\n\nDescripcion del error:\n" + str(format_exc()))


    scrapper.temp_dict[user]["top"] = obtener_diferencia_scroll(scrapper, user)        

    scrapper.temp_dict[user]["altura_elemento_grupos"] = scrapper.temp_dict[user]["publicacion"]["lista_grupos"][0].size["height"]

    scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "obtener diferencia de scroll y la altura de los elementos de grupos (Proceso de única vez) linea {}".format(traceback.extract_stack()[-1].lineno)))

    #------------------obtener información para el scrolling--------------------------
    
    
    #bucle para publicar por los grupos
    while True:


        if not scrapper.temp_dict[user].get("contador"):
            scrapper.temp_dict[user]["contador"] = contador

        scrapper.administrar_BD(user=user, publicacion=scrapper.temp_dict[user]["publicacion"])

        scrapper.temp_dict[user]["if_cancelar"]()

        
        if puede_continuar(scrapper, user, "publicacion") == False:
            bot.send_message(user, "Se ha publicado exitosamente en " + str(len(scrapper.temp_dict[user]["publicacion"]["publicados"])) + " grupo(s)")
            return ("ok", "Se ha publicado exitosamente en " + str(len(scrapper.temp_dict[user]["publicacion"]["publicados"]))+ " grupo(s)")
            


        if contador % 10 == 0 and contador != 0:
            try:
                scrapper.driver.refresh()
            except:
                pass

            scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))

        #Esta variable es para poder luego guardarla en la BD de MongoDB
        
        
        scrapper.temp_dict[user]["demora"] = time.time()
        scrapper.temp_dict[user]["tiempo_debug"].append("\n---------------------------------")
        scrapper.temp_dict[user]["tiempo_debug"].append("--------- contador: {}  ----------".format(contador))

        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div#screen-root')))

        get_time_debug(scrapper, user)

        scrapper.temp_dict[user]["publicacion"]["lista_grupos"] = obtener_grupos(scrapper, user)

        scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "obtener grupos linea {}".format(traceback.extract_stack()[-1].lineno)))

        get_time_debug(scrapper, user)

        scrapper.temp_dict[user]["top"] = obtener_diferencia_scroll(scrapper, user)

        scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "obtener diferencia de scroll linea {}".format(traceback.extract_stack()[-1].lineno)))
        
    
        
        
        
        #si ya recorrimos todos los elementos de la lista de grupos el contador tendrá un valor mayor a la cantidad de grupos de la lista ya que en cada vuelta de bucle aumenta (le sumo 1 porque el índice de los grupos comienza en 0)

        
        while len(scrapper.temp_dict[user]["publicacion"]["lista_grupos"]) < (contador + 1):

            
            get_time_debug(scrapper, user)


            scrapper.temp_dict[user]["e"] = obtener_grupos(scrapper, user, True)

            scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "obtener grupos luego de que el contador fuera mayor linea {}".format(traceback.extract_stack()[-1].lineno)))
                        

            if len(scrapper.temp_dict[user]["e"]) == len(scrapper.temp_dict[user]["publicacion"]["lista_grupos"]):

                bot.unpin_all_chat_messages(user)
                
                if isinstance(scrapper.entrada.obtener_usuario(user).plan.repetir, bool) or not scrapper.entrada.obtener_usuario(user).plan.repetir:

                    scrapper.temp_dict[user]["msg"] = bot.send_message(user, "Se ha publicado exitosamente en " + str(len(scrapper.temp_dict[user]["publicacion"]["publicados"]) + len(scrapper.temp_dict[user]["publicacion"]["incompletas"])) + " grupo(s)")

                    return ("ok", "Se ha publicado exitosamente en " + str(len(scrapper.temp_dict[user]["publicacion"]["publicados"]) + len(scrapper.temp_dict[user]["publicacion"]["incompletas"])) + " grupo(s)")
                
                elif isinstance(scrapper.entrada.obtener_usuario(user).plan.repetir, (int, float)):
                    
                    scrapper.temp_dict[user]["msg"] = bot.send_message(user, m_texto("Publiqué en " + str(len(scrapper.temp_dict[user]["publicacion"]["publicados"]) + len(scrapper.temp_dict[user]["publicacion"]["incompletas"])) + " grupos satisfactoriamente\nAhora esperaré {} hora(s) y {} minuto(s) antes de volver a publicar masivamente\n\nCuando quieras cancelar envíame /cancelar".format(int(scrapper.entrada.obtener_usuario(user).plan.repetir / 60 / 60), int(scrapper.entrada.obtener_usuario(user).plan.repetir / 60 % 60))))
                    
                    return ("repetir", scrapper.temp_dict[user]["c_r"])

                    

            
            else:                
                scrapper.temp_dict[user]["publicacion"]["lista_grupos"] = scrapper.temp_dict[user]["e"].copy()

                del scrapper.temp_dict[user]["e"]

        

        
        try:
            #eliminar el elemento "open app" o "abrir app" si se encuentra
            scrapper.driver.execute_script('document.querySelectorAll("div.m.fixed-container.bottom").forEach(e => e.remove());')
        except:
            pass
        
        get_time_debug(scrapper, user)

        def click_grupo():

            scrapper.temp_dict[user]["res"] = scrapper.driver.execute_script("return window.pageYOffset;")

            

            hacer_scroll(scrapper, user,
                        #la última resta es para dejar el scroll un poco antes y asegurarme de que el elemento aparezca
                        scrapper.temp_dict[user]["altura_elemento_grupos"] * contador + scrapper.temp_dict[user]["top"] - scrapper.temp_dict[user]["res"] - scrapper.temp_dict[user]["altura_elemento_grupos"],

                        (scrapper.temp_dict[user]["altura_elemento_grupos"] * contador + scrapper.temp_dict[user]["top"] - scrapper.temp_dict[user]["res"]) // (scrapper.temp_dict[user]["altura_elemento_grupos"] * 8 + scrapper.temp_dict[user]["top"]))

            # hacer_scroll(scrapper, user, scrapper.temp_dict[user]["publicacion"]["lista_grupos"][contador], (contador + 1) // 4, contador)

            for i in range(3):
                try:
                    scrapper.click(scrapper.temp_dict[user]["publicacion"]["lista_grupos"][contador])
                    break

                except Exception as e:
                    if i >= 2:
                        if scrapper.temp_dict[user]["publicacion"].get("nombre"):
                            raise Exception("No se pudo clickear en el grupo: " + scrapper.temp_dict[user]["publicacion"]["nombre"])
                        
                        else:
                            raise Exception("No se pudo clickear en un grupo")

                    if isinstance(e, IndexError):
                        scrapper.temp_dict[user]["publicacion"]["lista_grupos"] = obtener_grupos(scrapper, user, True)

                    try:
                        ActionChains(scrapper.driver, 0).scroll_to_element(scrapper.temp_dict[user]["publicacion"]["lista_grupos"][contador]).perform()

                        ActionChains(scrapper.driver, 0).scroll_by_amount(0, -scrapper.temp_dict[user]["altura_elemento_grupos"] * 2)

                    except:
                        scrapper.temp_dict[user]["publicacion"]["lista_grupos"] = obtener_grupos(scrapper, user)

                    time.sleep(2)

        click_grupo()

        scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "hacer scroll y darle click al grupo #{} linea {}".format(contador + 1, traceback.extract_stack()[-1].lineno)))
        
        #Guardar el nombre del grupo....
        get_time_debug(scrapper, user)

        scrapper.wait.until(ec.invisibility_of_element_located(scrapper.temp_dict[user]["publicacion"]["lista_grupos"][contador]))
        scrapper.wait.until(ec.any_of(lambda driver: driver.find_elements(By.CSS_SELECTOR, 'h1')[1].text))

        scrapper.temp_dict[user]["publicacion"]["nombre"] = scrapper.find_elements(By.CSS_SELECTOR, 'h1')[-1].text.split(">")[0].strip().replace("\n", " ")

        scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "obtener el nombre del grupo #{} linea {}".format(contador + 1, traceback.extract_stack()[-1].lineno)))

        
        for e, publicacion in enumerate(scrapper.temp_dict[user]["obj_publicacion"][len(scrapper.temp_dict[user]["publicacion"]["resultados_publicaciones"]):], 1):
            
            try:
                scrapper.temp_dict[user]["publicacion"]["resultados_publicaciones"].append(hacer_publicacion(scrapper, bot, user, publicacion, contador))
            
            except:
                scrapper.temp_dict[user]["publicacion"]["resultados_publicaciones"].append(False)

                if not e >= len(scrapper.temp_dict[user]["obj_publicacion"]):

                    if not scrapper.driver.current_url.endswith("groups/"):
                        scrapper.load("https://m.facebook.com/groups/")

                    scrapper.temp_dict[user]["publicacion"]["lista_grupos"] = obtener_grupos(scrapper, user)

                    click_grupo()

                    continue
                
                if not scrapper.driver.current_url.endswith("groups/"):
                    scrapper.load("https://m.facebook.com/groups/")
            
        enviar_grupos(scrapper, user, bot, contador, scrapper.temp_dict[user]["publicacion"]["resultados_publicaciones"])
        
        scrapper.temp_dict[user]["publicacion"]["resultados_publicaciones"].clear()

        contador += 1
        scrapper.temp_dict[user]["contador"] = contador

        #el boton para ir atrás, a los grupos
        try:
            scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="button"]')))
            scrapper.click(scrapper.find_element(By.CSS_SELECTOR, 'div[role="button"]'))

        except:
            scrapper.load("https://m.facebook.com/groups/")
            scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'body')))

        scrapper.temp_dict[user]["demora"] = time.time() - scrapper.temp_dict[user]["demora"]
        scrapper.temp_dict[user]["tiempo_debug"].append("=> " + "{}:{}".format(int(scrapper.temp_dict[user]["demora"] / 60), int(scrapper.temp_dict[user]["demora"] % 60)) + " minutos <= tiempo para publicar en el grupo")


        scrapper.temp_dict[user]["timeout"] = time.time() + scrapper.delay

        while time.time() < scrapper.temp_dict[user]["timeout"]:
            scrapper.temp_dict[user]["if_cancelar"]()
            time.sleep(5)

        

def hacer_publicacion(scrapper: scrapping, bot : telebot.TeleBot, user: int, publicacion : Publicacion, contador: int):

    
    get_time_debug(scrapper, user)
    try:
        #esperar a "Write something..." o "What are you selling?"
        scrapper.temp_dict[user]["e"] = scrapper.wait.until(ec.any_of(
            ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Write something")]/../../..')),
            ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Escribe algo")]/../../..'))
        ))

        try:
            #eliminar el elemento "open app" o "abrir app" si se encuentra
            scrapper.driver.execute_script('document.querySelectorAll("div.m.fixed-container.bottom").forEach(e => e.remove());')
        except:
            pass


        for i in range(3):
            try:

                scrapper.click(scrapper.temp_dict[user]["e"])

                break

            except:

                if i >= 2:
                    raise Exception("No está el elemento para ir al formulario de la publicación")
                
                else:
                    scrapper.temp_dict[user]["e"] = scrapper.wait.until(ec.any_of(
                        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Write something")]/../../..')),
                        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Escribe algo")]/../../..'))
                    ))

                    time.sleep(2)

    except:
        #Maximo de peticiones:
        #Puede darse el caso de que el grupo donde se planea publicar las publicaciones tengan que ser aprobadas por los administradores y ya se ha sobrepasado la cantidad de publicaciones que el usuario puede pedir que se aprueben, entonces tampoco aparezca el botón 
        # O eso de arriba, o simplemente ocurrió un error

        scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "-------[Publicación: {}]-----\nEspera del elemento 'Write something' pero ERROR al INTENTAR hacer scroll y darle click al elemento para entrar en el formulario de publicacion del grupo #{}, creo que he hecho muchas peticiones de publicación, linea {}".format(publicacion.titulo , contador + 1, traceback.extract_stack()[-1].lineno)))

        # scrapper.temp_dict[user]["publicacion"]["error"].append(scrapper.temp_dict[user]["publicacion"]["nombre"])



        # contador += 1

        #el boton para ir atrás, a los grupos
        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="button"]')))
        scrapper.click(scrapper.find_element(By.CSS_SELECTOR, 'div[role="button"]'))

        # scrapper.temp_dict[user]["demora"] = time.time() - scrapper.temp_dict[user]["demora"]
        # scrapper.temp_dict[user]["tiempo_debug"].append("=> " + "{}:{}".format(int(scrapper.temp_dict[user]["demora"] / 60), int(scrapper.temp_dict[user]["demora"] % 60)) + " minutos <= tiempo para publicar la Publicación: ".format(publicacion.titulo))

        return False

        
    
    
    

    scrapper.wait.until(ec.invisibility_of_element_located((By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[6]/div[2]/div')))

    scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "-------[Publicación: {}]-----\nEspera del elemento 'Write something' hacer scroll y darle click al elemento para entrar en el formulario de publicacion del grupo #{}, linea {}".format(publicacion.titulo, contador + 1, traceback.extract_stack()[-1].lineno)))

    ##### 
    

    #-------------aqui estoy dentro del formulario de la publicación---------------------

    
    get_time_debug(scrapper, user)

    try:
        #eliminar el elemento "open app" o "abrir app" si se encuentra
        scrapper.driver.execute_script('document.querySelectorAll("div.m.fixed-container.bottom").forEach(e => e.remove());')
    except:
        pass

    if not publicacion.adjuntos:
        # desde: //*[@id="screen-root"]/div/div[2]/div[6]/div[1] 
        # hasta: //*[@id="screen-root"]/div/div[2]/div[6]/div[10]

        scrapper.wait.until(ec.visibility_of_element_located((By.XPATH, '//*[@id="screen-root"]/div/div[2]/div[6]/div[10]')))

        scrapper.click(scrapper.find_element(By.XPATH, '//*[@id="screen-root"]/div/div[2]/div[6]/div[{}]'.format(random.randint(1, 10))))


    scrapper.temp_dict[user]["e"] = scrapper.wait.until(ec.any_of(
        lambda driver: driver.find_element(By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[3]/div[16]').find_element(By.CSS_SELECTOR, 'span[role="link"]'),
        ec.visibility_of_element_located((By.XPATH, '//*[@id="screen-root"]/div/div[2]/div[5]/div/div')),
        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Write something")]/../../..')),
        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Escribe algo")]/../../..')),
        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Post something")]/../../..')),
        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Crea una publicación pública")]/../../..')),
        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "public post")]/../../..')),
        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Submit")]/../../..')),
    ))


    if not list(filter(lambda texto_label, scrapper=scrapper, user=user: re.search(texto_label, scrapper.temp_dict[user]["e"].text), ["Write something", "Post something", "Escribe algo", "publicación pública", "public post"])):
        #Si este elemento se encuentra es que el grupo es de venta , los que dicen "selling" son son grupos atípicos y normalmente no dejan publicar tan facilmente, asi que los omito

        

        scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "-------[Publicación: {}]-----\nEspera del elemento que me indica si el grupo #{} es de ventas, SI ES DE VENTAS ERROR, linea {}".format(publicacion.titulo, contador + 1, traceback.extract_stack()[-1].lineno)))

        # scrapper.temp_dict[user]["publicacion"]["error"].append(scrapper.temp_dict[user]["publicacion"]["nombre"])
        
        

        # contador += 1

        for i in range(2):
            #el boton para ir atrás, a los grupos
            scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="button"]')))
            scrapper.click(scrapper.find_element(By.CSS_SELECTOR, 'div[role="button"]'))

        
        # scrapper.temp_dict[user]["demora"] = time.time() - scrapper.temp_dict[user]["demora"]
        # scrapper.temp_dict[user]["tiempo_debug"].append("=> " + "{}:{}".format(int(scrapper.temp_dict[user]["demora"] / 60), int(scrapper.temp_dict[user]["demora"] % 60)) + " minutos <= tiempo para publicar en el grupo")

        
        return False



    try:
        
         for i in range(3):
            try:

                # scrapper.find_element(By.XPATH, '//*[@id="screen-root"]/div/div[2]/div[5]/div/div').click()
                scrapper.click(scrapper.temp_dict[user]["e"])

                break

            except:

                try:
                    ActionChains(scrapper.driver, 0).click(scrapper.temp_dict[user]["e"]).perform()
                    break
                except:
                    pass

                if i >= 2:
                    raise Exception("No está el elemento para ir al formulario de la publicación")
                
                else:

                    scrapper.temp_dict[user]["e"] = scrapper.wait.until(ec.any_of(
                        lambda driver: driver.find_element(By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[3]/div[16]').find_element(By.CSS_SELECTOR, 'span[role="link"]'),
                        ec.visibility_of_element_located((By.XPATH, '//*[@id="screen-root"]/div/div[2]/div[5]/div/div')),
                        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Write something")]/../../..')),
                        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Escribe algo")]/../../..')),
                        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Post something")]/../../..')),
                        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Crea una publicación pública")]/../../..')),
                        
                    ))


                    time.sleep(2)
       


    except Exception as e:
        #Los que dicen "selling" son grupos atípicos y normalmente no dejan publicar tan facilmente, asi que los omito

        scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "-------[Publicación: {}]-----\ndarle click al cajón de texto dentro del formulario de publicación en el grupo #{} HA HABIDO UN ERROR, el elemento no está, muy posiblemente sea un grupo de venta, linea {}".format(publicacion.titulo,contador + 1, traceback.extract_stack()[-1].lineno)))
        # scrapper.temp_dict[user]["publicacion"]["error"].append(scrapper.temp_dict[user]["publicacion"]["nombre"]


        #el boton para ir atrás, a los grupos
        for i in range(2):
            scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="button"]')))
            scrapper.click(scrapper.find_element(By.CSS_SELECTOR, 'div[role="button"]'))


        
        return False


    #//*[@id="screen-root"]/div/div[2]/div[5]/div/div
    scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "-------[Publicación: {}]-----\ndarle click al cajón de texto dentro del formulario de publicación en el grupo #{} linea {}".format(publicacion.titulo, contador + 1, traceback.extract_stack()[-1].lineno)))

    get_time_debug(scrapper, user)

    for i in range(10):
        try:
            scrapper.temp_dict[user]["res"] = scrapper.wait_s.until(ec.any_of(
                lambda driver: driver.find_element(By.XPATH, '//*[contains(text(), "Write something")]/../../..'),
                lambda driver: driver.find_element(By.XPATH, '//*[contains(text(), "Escribe algo")]/../../..'),
                lambda driver: driver.find_element(By.XPATH, '//*[contains(text(), "Create a public post")]'),
                lambda driver: driver.find_element(By.XPATH, '//*[contains(text(), "Crea una publicación pública")]'),
                ec.visibility_of_element_located((By.XPATH, '//*[@id="screen-root"]/div/div[2]/div[5]/div/div')
            )))
                

            scrapper.temp_dict[user]["a"].send_keys_to_element(scrapper.temp_dict[user]["res"], publicacion.texto).perform()

            break

        except:
            if i >= 9:
                Exception("NO se econtró el cuadro de texto del formulario de la publicación")

            else:
                time.sleep(2)
    
    #comprobar que el texto se insertó adecuadamente
    # scrapper.wait.until(ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "{}")]'.format(scrapper.temp_dict[user]["texto_p"].splitlines()[-1]))))

    scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "-------[Publicación: {}]-----\nintroducir el texto dentro del formulario de publicación en el grupo #{} linea {}".format(publicacion.titulo, contador + 1, traceback.extract_stack()[-1].lineno)))


    if publicacion.adjuntos:
        for foto in publicacion.adjuntos:
            get_time_debug(scrapper, user)

            envia_fotos_input(scrapper, user, foto)

            scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "-------[Publicación: {}]-----\nintroducir la foto dentro del formulario de publicación en el grupo #{} linea {}".format(publicacion.titulo, contador + 1, traceback.extract_stack()[-1].lineno)))

    


    get_time_debug(scrapper, user)


    scrapper.temp_dict[user]["res"] = scrapper.wait.until(ec.any_of(
        lambda driver: driver.find_elements(By.XPATH, '//*[@id="screen-root"]/div/div[2]/*[@data-mcomponent="MContainer"]')[-1],
        lambda driver: driver.find_elements(By.XPATH, '//*[contains(text(), "POST")]/../../..')[-1],
        lambda driver: driver.find_elements(By.XPATH, '//*[contains(text(), "PUBLICAR")]/../../..')[-1]
    ))
    
    for i in range(5):
        try:
            scrapper.click(scrapper.temp_dict[user]["res"])
            # ActionChains(scrapper.driver).click(scrapper.temp_dict[user]["e"]).perform()
            break

        except Exception as err:
            if i >= 4:
                raise err
            
            try:
                ActionChains(scrapper.driver, 0).click(scrapper.temp_dict[user]["res"]).perform()
                break
            except:
                pass
            
            time.sleep(2)

    #esperar a regresar..
    scrapper.wait.until(ec.any_of(
        ec.visibility_of_all_elements_located((By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[6]/div[2]/div')),
        ec.visibility_of_all_elements_located((By.XPATH, '//*[contains(text(), "Write something")]')),
        ec.visibility_of_all_elements_located((By.XPATH, '//*[contains(text(), "Escribe algo")]')),
    ))

    scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "click en el botón de publicar en el formulario del grupo #{} linea {}".format(contador + 1, traceback.extract_stack()[-1].lineno)))

    #----------------------------Formulario END---------------------------------
            
    
    
    
    # if not scrapper.temp_dict[user]["publicacion"].get("msg_publicacion"):
        
        
    #     scrapper.temp_dict[user]["info"] = bot.send_message(user, "✅Se ha publicado en: " + str(len(scrapper.temp_dict[user]["publicacion"]["publicados"])) + " grupo(s)" + "\n⛔Han quedado incompletas en: " + str(len(scrapper.temp_dict[user]["publicacion"]["incompletas"])) + " grupo(s)" + "\n❌Se han producido errores en: " + str(len(scrapper.temp_dict[user]["publicacion"]["error"])) + " grupo(s)")
        
        
    
    
    get_time_debug(scrapper, user)

    



    scrapper.wait.until(ec.visibility_of_all_elements_located((By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[6]/div[2]/div')))

    # scrapper.temp_dict[user]["a"].scroll_by_amount(0 , scrapper.find_element(By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[6]/div[2]/div').location["y"] + scrapper.find_element(By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[6]/div[2]/div').size["height"]).perform()

    # scrapper.temp_dict[user]["publicacion"]["publicados"].append(scrapper.temp_dict[user]["publicacion"]["nombre"])
    #-------------------------------------------------cambiar a futuro-----------------------------------------
    # for iteracion_buscar in range(3):



    #     def comprobar_p(scrapper, espera: int = 8):
    #         """
    #         True si encuentra la publicacion en el grupo
    #         False si no la encuentra
    #         "pendiente" si está pendiente
    #         """

    #         try:                             
    #             #este revisa la primera publicación del grupo
    #             WebDriverWait(scrapper.driver, espera).until(ec.all_of(lambda driver, scrapper=scrapper, user=user: driver.find_element(By.XPATH, '//*[contains(text(), "{}")]'.format(str(scrapper.temp_dict[user]["perfil_seleccionado"]).strip())), lambda driver, scrapper=scrapper, user=user: driver.find_element(By.XPATH, '//*[contains(text(), "{}")]'.format(scrapper.temp_dict[user]["texto_r"]))))

    #             scrapper.temp_dict[user]["publicacion"]["publicados"].append(scrapper.temp_dict[user]["publicacion"]["nombre"])

    #             return True
            
    #         except:
    #             pass
                
                
    #         try:


    #             if WebDriverWait(scrapper.driver, espera).until(ec.any_of(ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "pendiente")]')), ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Your post is pending")]')))):

    #                 scrapper.temp_dict[user]["publicacion"]["incompletas"].append(scrapper.temp_dict[user]["publicacion"]["nombre"])
                        
    #                 return "pendiente"
            
    #         except:
    #             pass

                
            
            
    #         return False
            

    #     match comprobar_p(scrapper):
            
    #         case True:

    #             break

    #         case "pendiente":


    #             break

    #         case False:

    #             if not iteracion_buscar >= 2:

    #                 if iteracion_buscar == 0:
    #                     scrapper.driver.refresh()

    #                 try:
    #                     for i in range(iteracion_buscar + 1):
    #                         scrapper.find_element(By.CSS_SELECTOR, "body").send_keys(Keys.END)
    #                 except:
    #                     pass

    #                 time.sleep(2)
    #             #----------------------------------------------------------------------------------

    #             else:
    #                 scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "comprobar que la publicación se hizo en el grupo pero se obtuvo UN ERROR en el grupo #{} linea {}".format(contador + 1, traceback.extract_stack()[-1].lineno)))

    #                 print("❌ {}".format(scrapper.temp_dict[user]["publicacion"]["nombre"]))
    #                 scrapper.temp_dict[user]["publicacion"]["error"].append(scrapper.temp_dict[user]["publicacion"]["nombre"])


    #                 #el boton para ir atrás, a los grupos
    #                 scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="button"]')))
    #                 scrapper.find_element(By.CSS_SELECTOR, 'div[role="button"]').click()

    #                 enviar_grupos()
    #                 contador += 1

    #                 scrapper.temp_dict[user]["demora"] = time.time() - scrapper.temp_dict[user]["demora"]
    #                 scrapper.temp_dict[user]["tiempo_debug"].append("=> " + "{}:{}".format(int(scrapper.temp_dict[user]["demora"] / 60), int(scrapper.temp_dict[user]["demora"] % 60)) + " minutos <= tiempo para publicar en el grupo")

                    
    #                 continue

    #-------------------------------------------------cambiar a futuro-----------------------------------------

    scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "-------[Publicación: {}]-----\ncomprobar que la publicación se hizo en el grupo #{}, SI SE HIZO, linea {}".format(publicacion.titulo, contador + 1, traceback.extract_stack()[-1].lineno)))
    
    return True
                
def elegir_cuenta(scrapper: scrapping, user, bot: telebot.TeleBot , ver_actual=False, perfil_actual=False):


    scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'body')))
    scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div#screen-root')))
    
    try:
        #si ya el menú de cuentas está desplegado... hay que omitir cosas
        scrapper.temp_dict[user]["e"] = scrapper.wait_s.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="list"]')))

        scrapper.temp_dict[user]["e"] = True
        
    except Exception as err: 

        if scrapper.facebook_popup():
            scrapper.temp_dict[user]["e"] = scrapper.wait_s.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="list"]')))

            scrapper.temp_dict[user]["e"] = True
        
        scrapper.temp_dict[user]["e"] = False


    #el menu no está desplegado    
    if not scrapper.temp_dict[user]["e"]:  
        # scrapper.driver.get(scrapper.driver.current_url + "/bookmarks/")

        #este elemento es el de los ajustes del perfil (las 3 rayas de la derecha superior)
        scrapper.wait.until(ec.any_of(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, 'div[role="button"]')) > 3))

        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="button"]')))
        #//*[contains(text(), "Your Pages and profiles")]/../../../..
        #//div[contains(@role,"button")][contains(@aria-label, "Switch Profile")]
        scrapper.temp_dict[user]["url_actual"] = scrapper.driver.current_url
        
        if not scrapper.temp_dict[user]["e"]:
            scrapper.click(scrapper.find_elements(By.CSS_SELECTOR, 'div[role="button"]')[2])
            # scrapper.find_elements(By.CSS_SELECTOR, 'div[data-tti-phase="-1"][role="button"][tabindex="0"][data-focusable="true"][data-mcomponent="MContainer"][data-type="container"]')[2].click()

            scrapper.wait_s.until(ec.url_changes(scrapper.temp_dict[user]["url_actual"]))

            if not scrapper.driver.current_url.endswith("bookmarks/"):
                scrapper.load("https://m.facebook.com/bookmarks/")

            # #Elemento de Configuracion de cuenta
            scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="list"]')))



            #Flecha para ver otros perfiles/cambiar
            
            scrapper.wait.until(ec.visibility_of_all_elements_located((By.CSS_SELECTOR, 'div[tabindex="0"][role="button"][data-focusable="true"][data-tti-phase="-1"][data-mcomponent="MContainer"][data-type="container"][class="m"]')))


            if len(scrapper.find_elements(By.CSS_SELECTOR, 'div[tabindex="0"][role="button"][data-focusable="true"][data-tti-phase="-1"][data-mcomponent="MContainer"][data-type="container"][class="m"]')) >= 4:

                scrapper.click(scrapper.find_elements(By.CSS_SELECTOR, 'div[tabindex="0"][role="button"][data-focusable="true"][data-tti-phase="-1"][data-mcomponent="MContainer"][data-type="container"][class="m"]')[-1])

                # try:
                #     scrapper.find_elements(By.CSS_SELECTOR, 'div[role="button"]')[4].find_element(By.CSS_SELECTOR, 'img')

                #     scrapper.find_elements(By.CSS_SELECTOR, 'div[role="button"]')[5].click()
                
                # except:
                #     if not "\n" in scrapper.find_elements(By.CSS_SELECTOR, 'div[role="button"]')[4].text:

                #         scrapper.find_elements(By.CSS_SELECTOR, 'div[role="button"]')[4].click()

                #     elif not "\n" in scrapper.find_elements(By.CSS_SELECTOR, 'div[role="button"]')[3].text:

                #         scrapper.find_elements(By.CSS_SELECTOR, 'div[role="button"]')[3].click()

                scrapper.temp_dict[user]["res"] = ("ok", "han salido")


            else:
                #si tiene solamente 1 perfil en la cuenta no aparecerá el botón
                scrapper.temp_dict[user]["res"] = scrapper.find_elements(By.CSS_SELECTOR, 'div[tabindex="0"][role="button"][data-focusable="true"][data-tti-phase="-1"][data-mcomponent="MContainer"][data-type="container"][class="m"]')[2]

                scrapper.temp_dict[user]["perfil_seleccionado"] = scrapper.temp_dict[user]["res"].text.split("\n")[0].strip()

                #guardar la informacion de la cuenta en la clase Cuenta
                if not scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user]["perfil_seleccionado"]):
                    usuario = scrapper.entrada.obtener_usuario(user)
                    usuario.cuentas.append(Cuenta(scrapper.temp_dict[user]["perfil_seleccionado"], scrapper.temp_dict[user]["user"], scrapper.temp_dict[user]["password"], scrapper.temp_dict[user]["perfil_seleccionado"]))

                    scrapper.administrar_BD(user=user)

                if scrapper.temp_dict[user].get("user") and scrapper.temp_dict[user].get("perfil_seleccionado"):
                    if scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user]["perfil_seleccionado"]).contrasena != scrapper.temp_dict[user]["password"] or scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user]["perfil_seleccionado"]).usuario != scrapper.temp_dict[user]["user"]:

                        instancia_cuenta = scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user]["perfil_seleccionado"])

                        instancia_cuenta.contrasena = scrapper.temp_dict[user]["password"]
                        instancia_cuenta.usuario = scrapper.temp_dict[user]["user"]

                        scrapper.administrar_BD(user=user)


                    
                    
                return ("ok", scrapper.temp_dict[user]["perfil_seleccionado"], "uno")


        
            

   
        

    #esperar a que salgan las cuentas
    # padre => "div.x1gslohp"


    #este elemento es el padre de las cuentas, concretamente el 2do elemento en el html
    scrapper.wait.until(ec.visibility_of_all_elements_located((By.CSS_SELECTOR, 'div[data-action-id="99"][data-mcomponent="MContainer"][data-type="container"][tabindex="0"][data-tti-phase="-1"][data-focusable="true"]')))

    scrapper.wait.until(ec.any_of(lambda driver : len(driver.find_elements(By.CSS_SELECTOR, 'div[data-action-id="99"][data-mcomponent="MContainer"][data-type="container"][tabindex="0"][data-tti-phase="-1"][data-focusable="true"]')) >= 2))

    scrapper.wait.until(ec.element_to_be_clickable(scrapper.find_elements(By.CSS_SELECTOR, 'div[data-action-id="99"][data-mcomponent="MContainer"][data-type="container"][tabindex="0"][data-tti-phase="-1"][data-focusable="true"]')[1].find_element(By.CSS_SELECTOR, 'div[role="button"][tabindex="0"][data-focusable="true"][data-tti-phase="-1"][data-type="container"][data-mcomponent="MContainer"]')))


    scrapper.temp_dict[user]["cuentas"] = scrapper.find_elements(By.CSS_SELECTOR, 'div[data-action-id="99"][data-mcomponent="MContainer"][data-type="container"][tabindex="0"][data-tti-phase="-1"][data-focusable="true"]')[1].find_elements(By.CSS_SELECTOR, 'div[role="button"][tabindex="0"][data-focusable="true"][data-tti-phase="-1"][data-type="container"][data-mcomponent="MContainer"]')

    scrapper.temp_dict[user]["cuentas"].remove(scrapper.temp_dict[user]["cuentas"][0])
    
    #ahora quitaré el elemento que dice "Crear Perfil"
    for e, i in enumerate(scrapper.temp_dict[user]["cuentas"]):

        try:
            if i.find_element(By.CSS_SELECTOR, 'img'):
                continue

        except:
            scrapper.temp_dict[user]["cuentas"].remove(scrapper.temp_dict[user]["cuentas"][e])
    
    if len(scrapper.temp_dict[user]["cuentas"]) == 1:
        scrapper.temp_dict[user]["perfil_seleccionado"] = scrapper.temp_dict[user]["cuentas"][0].text.split("\n")[0]

        if not scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user]["perfil_seleccionado"]):
            usuario = scrapper.entrada.obtener_usuario(user)
            usuario.cuentas.append(Cuenta(scrapper.temp_dict[user]["perfil_seleccionado"], scrapper.temp_dict[user]["user"], scrapper.temp_dict[user]["password"], scrapper.temp_dict[user]["perfil_seleccionado"]))

            scrapper.administrar_BD(user=user)

        if scrapper.temp_dict[user].get("user") and scrapper.temp_dict[user].get("perfil_seleccionado"):
            if scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user]["perfil_seleccionado"]).contrasena != scrapper.temp_dict[user]["password"] or scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user]["perfil_seleccionado"]).usuario != scrapper.temp_dict[user]["user"]:

                instancia_cuenta = scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user]["perfil_seleccionado"])

                instancia_cuenta.contrasena = scrapper.temp_dict[user]["password"]
                instancia_cuenta.usuario = scrapper.temp_dict[user]["user"]

                scrapper.administrar_BD(user=user)

        return ("ok", scrapper.temp_dict[user]["perfil_seleccionado"], "uno")

    
    
    if not ver_actual:
        
        scrapper.temp_dict[user]["teclado"] = ReplyKeyboardMarkup(True, True, input_field_placeholder="Elige un perfil")
        scrapper.temp_dict[user]["perfiles"] = []
    
        for e,cuenta in enumerate(scrapper.temp_dict[user]["cuentas"], 1):     
            
            scrapper.temp_dict[user]["perfiles"].append(cuenta.text.split("\n")[0].strip())
            
            scrapper.temp_dict[user]["teclado"].add(cuenta.text.split("\n")[0].strip())               
            

        if perfil_actual:
            scrapper.temp_dict[user]["res"] = scrapper.temp_dict[user]["perfiles"].index(scrapper.temp_dict[user]["perfil_seleccionado"])

        else:
            handlers(bot, user, "Cual de los perfiles de esta cuenta quieres usar?", "perfil_elegir", scrapper, markup=scrapper.temp_dict[user]["teclado"])

        scrapper.temp_dict[user]["e"] = scrapper.temp_dict[user]["cuentas"][scrapper.temp_dict[user]["res"]]


        borrar_elemento(scrapper, 'div[role="presentation"]')
        
        for i in range(5):
            try:
                scrapper.wait_s.until(ec.element_to_be_clickable(scrapper.temp_dict[user]["e"]))
                # scrapper.temp_dict[user]["cuentas"][scrapper.temp_dict[user]["res"]].click()
                # scrapper.temp_dict[user]["e"].find_element(By.CSS_SELECTOR, "img").click()
                scrapper.click(scrapper.temp_dict[user]["e"].find_element(By.CSS_SELECTOR, "img"))
                break 
        
            except:
                if i >=4:
                    raise Exception("No puedo encontrar el elemento para cambiar de perfil")

                else:
                    scrapper.temp_dict[user]["e"] = scrapper.temp_dict[user]["e"].find_element(By.XPATH, '..')

        try:
            scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "div#screen-root")))
        except:
            pass

        

        scrapper.guardar_datos(user)
        
        scrapper.temp_dict[user]["perfil_seleccionado"] = scrapper.temp_dict[user]["perfiles"][scrapper.temp_dict[user]["res"]]

        if not scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user]["perfil_seleccionado"]):
            usuario = scrapper.entrada.obtener_usuario(user)
            usuario.cuentas.append(Cuenta(scrapper.temp_dict[user]["perfiles"][0], scrapper.temp_dict[user]["user"], scrapper.temp_dict[user]["password"], scrapper.temp_dict[user]["perfiles"]))

            scrapper.administrar_BD(user=user)

        if scrapper.temp_dict[user].get("user") and scrapper.temp_dict[user].get("perfil_seleccionado"):
            if scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user]["perfil_seleccionado"]).contrasena != scrapper.temp_dict[user]["password"] or scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user]["perfil_seleccionado"]).usuario != scrapper.temp_dict[user]["user"]:

                instancia_cuenta = scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user]["perfil_seleccionado"])

                instancia_cuenta.contrasena = scrapper.temp_dict[user]["password"]
                instancia_cuenta.usuario = scrapper.temp_dict[user]["user"]

                scrapper.administrar_BD(user=user)

        return ("ok", scrapper.temp_dict[user]["perfil_seleccionado"])
        
    else:

        if not scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user]["cuentas"][0].text.split("\n")[0]):

            scrapper.temp_dict[user]["perfiles"] = []

            for e,cuenta in enumerate([cuenta.text.split("\n")[0].strip() for cuenta in scrapper.temp_dict[user]["cuentas"]], 1):     
                
                scrapper.temp_dict[user]["perfiles"].append(cuenta)

                usuario = scrapper.entrada.obtener_usuario(user)

            usuario.cuentas.append(Cuenta(scrapper.temp_dict[user]["cuentas"][0].text.split("\n")[0], scrapper.temp_dict[user]["user"], scrapper.temp_dict[user]["password"], scrapper.temp_dict[user]["perfiles"])) 

            scrapper.administrar_BD(user=user)

        if scrapper.temp_dict[user].get("user") and scrapper.temp_dict[user].get("perfil_seleccionado"):
            if scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user]["perfil_seleccionado"]).contrasena != scrapper.temp_dict[user]["password"] or scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user]["perfil_seleccionado"]).usuario != scrapper.temp_dict[user]["user"]:

                instancia_cuenta = scrapper.entrada.obtener_usuario(user).obtener_cuenta(scrapper.temp_dict[user]["perfil_seleccionado"])

                instancia_cuenta.contrasena = scrapper.temp_dict[user]["password"]
                instancia_cuenta.usuario = scrapper.temp_dict[user]["user"]

                scrapper.administrar_BD(user=user)
        #para ver el perfil actual
        return ("ok", scrapper.temp_dict[user]["cuentas"][0].text.split("\n")[0])
            


                     


    

    
    
    
        
        
def main(scrapper: scrapping, bot: telebot.TeleBot, user: int):
    """
    This function will do all the scrapping requesting to other functions and makes for sure that all is ok
    
    bot: instance of telebot
    user : telegram's user_id
    """

    #limpiar el texto
    
    # scrapper.temp_dict[user]["texto_r"] = scrapper.temp_dict[user]["obj_publicacion"].texto.splitlines()[0][:60].strip()
    

    comprobar_BD(scrapper.collection)

    scrapper.temp_dict[user]["if_cancelar"] = lambda scrapper=scrapper, user=user, bot=bot: if_cancelar(scrapper, user, bot)
        

    if not scrapper.interrupcion:
        texto = """
Empezaré a procesar tu petición...

<u><b>Información sobre la publicación actual</b></u>:
<blockquote>{}

{}

{}
</blockquote>
""".format(
    "<b>Publicacion(es) a compartir</b>: " + ", ".join(["<b>" + publicacion.titulo + "</b>" for publicacion in scrapper.temp_dict[user]["obj_publicacion"]]),

    "<b>Perfil(es) en los que compartir</b>: " + scrapper.temp_dict[user].get("perfil_seleccionado") if scrapper.temp_dict[user].get("perfil_seleccionado") else "<b>Perfil(es) en los que compartir</b>: (Se entrará con un perfil nuevo)",

    "<b>Tiempo para repetir publicación</b>: " + str(obtener_tiempo(scrapper.entrada.obtener_usuario(user).plan.repetir)) if isinstance(scrapper.entrada.obtener_usuario(user).plan.repetir, int) and not isinstance(scrapper.entrada.obtener_usuario(user).plan.repetir, bool) else "<b>Tiempo para repetir publicación</b>: (No hay tiempo definido por el usuario, <b>solo se repetirá 1 vez</b>)" if scrapper.entrada.obtener_usuario(user).plan.repetir else "<b>Tiempo para repetir publicación</b>: (Debe comprar un mejor plan para poder acceder a esto, <b>solo se repetirá 1 vez</b>)"
    ).strip()
        



        bot.send_message(user, m_texto(texto), reply_markup=telebot.types.ReplyKeyboardRemove())


    scrapper.temp_dict[user]["if_cancelar"]()

    print("Voy a hacer el loguin")

    if scrapper.interrupcion == False or "login" in scrapper.driver.current_url or not scrapper.entrada.obtener_usuario(user).cuentas:
        scrapper.temp_dict[user]["res"] = loguin(scrapper, user, bot)
    

    #comprobando estar en el inicio de la mainpage de facebook
    scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div#screen-root')))

    scrapper.guardar_datos(user)
    scrapper.guardar_datos()

    scrapper.temp_dict[user]["if_cancelar"]()

    if scrapper.temp_dict[user].get("perfil_seleccionado"):
        print("Voy a autenticarme con el perfil que estaba publicando antes de que me detuviera")
        scrapper.temp_dict[user]["res"] = elegir_cuenta(scrapper , user, bot, perfil_actual=scrapper.temp_dict[user]["perfil_seleccionado"])
        print("Autenticación con éxito")

    else:
        print("Voy a ver el perfil actual")
        scrapper.temp_dict[user]["res"] = elegir_cuenta(scrapper , user, bot, ver_actual=True)


    if not scrapper.temp_dict[user].get("perfil_seleccionado"):
    
        if not len(scrapper.temp_dict[user]["res"]) == 3:
        
            scrapper.temp_dict[user]["teclado"] = ReplyKeyboardMarkup(True, True, row_width=1, input_field_placeholder="¿Quieres cambiar a otro perfil?").add("Si", "No", row_width=2)
            
            scrapper.temp_dict[user]["perfil_seleccionado"] = str(scrapper.temp_dict[user]["res"][1])

            handlers(bot, user, "El perfil actual es:\n\n=> <b>" + str(scrapper.temp_dict[user]["res"][1]) + "</b>\n\n¿Quieres cambiar de perfil?", "perfil_pregunta", scrapper, markup=scrapper.temp_dict[user]["teclado"])

            
            
            if scrapper.temp_dict[user]["res"].text.lower() == "si":
                print("Voy a cambiar de perfil")
                
                if not "bookmarks" in scrapper.driver.current_url:
                    scrapper.load("https://m.facebook.com/bookmarks/")

                scrapper.temp_dict[user]["res"] = elegir_cuenta(scrapper, user, bot)
                if scrapper.temp_dict[user]["res"][0] == "error":


                    raise Exception("ID usuario: " + str(user) + "\n\nDescripción del error:\n" + str(scrapper.temp_dict[user]["res"][1]))

                else:
                    # scrapper.temp_dict[user]["info"] = bot.edit_message_text(text=f"🆕 Mensaje de Información\n\nHe cambiado al perfil de: {scrapper.temp_dict[user]["res"][1]}", chat_id=user, message_id=scrapper.temp_dict[user]["info"].message_id, reply_markup=telebot.types.ReplyKeyboardRemove())

                    scrapper.temp_dict[user]["perfil_seleccionado"] = str(scrapper.temp_dict[user]["res"][1])
                    
                    bot.send_message(user, m_texto("He cambiado al perfil de:\n\n=> <b>" + str(scrapper.temp_dict[user]["res"][1]) + "</b>\n\nLoguin completado exitosamente!\nEn breve comenzaré a publicar ☺"), reply_markup=telebot.types.ReplyKeyboardRemove())

            else:
                # scrapper.temp_dict[user]["info"] = bot.edit_message_text(text=f"🆕 Mensaje de Información\n\nMuy bien, continuaré con el perfil actual", chat_id=user, message_id=scrapper.temp_dict[user]["info"].message_id, reply_markup=telebot.types.ReplyKeyboardRemove())

                bot.send_message(user, m_texto("Muy bien, continuaré con el perfil actual\n\nLoguin completado exitosamente!"), reply_markup=telebot.types.ReplyKeyboardRemove())
        else:
            bot.send_message(user, m_texto("Al parecer, solamente está el perfil de:\n\n=> <b>" + str(scrapper.temp_dict[user]["res"][1]) +"</b>\n\nContinuaré con ese..."))



    scrapper.guardar_datos(user)


    scrapper.temp_dict[user]["if_cancelar"]()
    
    if not  scrapper.temp_dict[user].get("c_r"):
        scrapper.temp_dict[user]["c_r"] = 1 #esto indica la cantidad de veces que se ha hecho la publicación masiva de todos los grupos, es un contador



    #-----------------------------------PUBLICACIÓN----------------------------------------------
    if re.search(r"hora_reinicio", str(scrapper.temp_dict[user])):
        pass
    
    else:
        scrapper.temp_dict[user]["publicacion_res"] = publicacion(scrapper, bot , user)



    while not scrapper.temp_dict[user]["publicacion_res"][0] == "ok":
        

        scrapper.temp_dict[user]["publicacion"]["hora_reinicio"] = time.time() + scrapper.entrada.obtener_usuario(user).plan.repetir

        scrapper.guardar_datos(user)
                        
        while not time.time() >= scrapper.temp_dict[user]["publicacion"]["hora_reinicio"]:


            scrapper.temp_dict[user]["if_cancelar"]()
            time.sleep(1 * 60)

        
        del scrapper.temp_dict[user]["publicacion"]

        scrapper.temp_dict[user]["contador"] = 0

        scrapper.temp_dict[user]["c_r"] += 1

        scrapper.interrupcion = False

        scrapper.load("https://m.facebook.com/groups/")

        scrapper.temp_dict[user]["publicacion_res"] = publicacion(scrapper, bot , user)



    bot.send_message(user, scrapper.temp_dict[user]["publicacion_res"][1])

    return scrapper.temp_dict[user]["publicacion_res"]