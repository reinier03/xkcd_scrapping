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
import seleniumbase
from pymongo import MongoClient
import tempfile
import shutil
import sys
import json
import requests
import traceback

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from tb_src.main_classes import scrapping
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




    

def guardar_cookies(scrapper: scrapping, user, **kwargs):
    

    try:
        scrapper.temp_dict[user]["dict_cookies"] = cargar_cookies(scrapper, user, hacer_loguin=False)
        
        if isinstance(scrapper.temp_dict[user]["dict_cookies"], Exception):
            scrapper.temp_dict[user]["dict_cookies"] = ("error", e.args[0])
            
    except Exception as e:
        scrapper.temp_dict[user]["dict_cookies"] = ("error", e.args[0])
        
    scrapper.temp_dict[user]["dic"] = {}
    if scrapper.temp_dict[user]["dict_cookies"][0] == "ok":
        scrapper.temp_dict[user]["dict_cookies"] = scrapper.temp_dict[user]["dict_cookies"][-1]
        #si ya habían datos guardados y no se le pasó por parametro a la funcion entonces se mantienen esos datos
        for key, value in scrapper.temp_dict[user]["dict_cookies"].items():
            if not scrapper.temp_dict[user]["dic"].get(key):
                scrapper.temp_dict[user]["dic"][key] = value
    else:
        scrapper.temp_dict[user]["dict_cookies"] = {}
        
    with open(os.path.join(user_folder(user), "cookies.pkl"), "wb") as file_cookies:
        #recorrer los kwargs y agregarlos a las cookies
        if kwargs:
            if kwargs.get("cookiespkl"):
                dill.dump(kwargs.get("cookiespkl"), file_cookies)
                
            else:
                for key, value in kwargs.items():
                    scrapper.temp_dict[user]["dic"][key] = value
                
                scrapper.temp_dict[user]["dic"]["cookies"] = scrapper.driver.get_cookies()


                dill.dump(scrapper.temp_dict[user]["dic"], file_cookies)
                
        else:
            scrapper.temp_dict[user]["dic"]["cookies"] = scrapper.driver.get_cookies()


            dill.dump(scrapper.temp_dict[user]["dic"], file_cookies)


    try:
        with open(os.path.join(user_folder(user), "cookies.pkl"), "rb") as cookies:
            scrapper.collection.update_one({"telegram_id": user}, {"$set": {"cookies": dill.load(cookies)}})
            
    except:
        del scrapper.temp_dict[user]["dic"], scrapper.temp_dict[user]["dict_cookies"]
        raise Exception("error", "Error en ingresar las cookies a la base de datos:\n\nDescripción del error:\n" + str(format_exc()))
    
    del scrapper.temp_dict[user]["dic"]
    try:
        del scrapper.temp_dict[user]["dict_cookies"]
        
    except:
        pass
    
    print("Se guardaron cookies!")
    return ("ok", os.path.join(user_folder(user), "cookies.pkl"))



def cargar_cookies(scrapper: scrapping, user, bot=False , hacer_loguin=True):

    scrapper.temp_dict[user]["if_cancelar"]()
    
    #si hay cookies
    if list(filter(lambda file: "cookies.pkl" in file, os.listdir(user_folder(user)))):
        
        if hacer_loguin:
            scrapper.driver.get("https://facebook.com/robots.txt")
        
        with open(os.path.join(user_folder(user), "cookies.pkl"), "rb") as file_cookies:
            try:
                scrapper.temp_dict[user]["cookies_dict"] = dill.load(file_cookies)
            
            except:
                return ("error", format_exc())
            
            if not hacer_loguin:
                return ("ok", scrapper.temp_dict[user]["cookies_dict"])
            
            
            for cookie in scrapper.temp_dict[user]["cookies_dict"]["cookies"]:
                scrapper.driver.add_cookie(cookie)
                    
                             
    else:
        try:
            
            scrapper.temp_dict[user]["res"] = scrapper.collection.find_one({'_id': user})["cookies"]
            if scrapper.temp_dict[user]["res"]:
                #loguin por cookies
                if hacer_loguin:
                    scrapper.driver.get("https://facebook.com/robots.txt")
                    
                with open(os.path.join(user_folder(user), "cookies.pkl"), "wb") as cookies:
                    cookies.write(scrapper.temp_dict[user]["res"])
                    
                with open(os.path.join(user_folder(user), "cookies.pkl"), "rb") as cookies:
                    scrapper.temp_dict[user]["cookies_dict"] = dill.load(cookies)
                    
                    if not hacer_loguin:
                        return ("ok", scrapper.temp_dict[user]["cookies_dict"])
                    
                    for cookies in scrapper.temp_dict[user]["cookies_dict"]["cookies"]:
                        scrapper.driver.add_cookie(cookies)
                        
                        
            
                                    
        except Exception as e:
            try:
                if re.search('error=.*timeout', e.args[0]).group().split('(')[1]:
                    raise Exception("No hay conexión con la base de datos!" + "\nDescripción\n\n" + re.search('error=.*timeout', e.args[0]).group().split('(')[1])

            except:
                pass
            
            finally:
                return Exception("Error intentando acceder a la base de datos:\n\nDescripción:\n" + str(format_exc()))
    
    if hacer_loguin == True:
        scrapper.temp_dict[user]["if_cancelar"]()

        load(scrapper, "https://facebook.com")
        
            
        # scrapper.temp_dict[user]["info"] = bot.edit_message_text(text="🆕 Mensaje de Información\n\nMuy Bien, Ya accedí a Facebook :D", chat_id=user, message_id=scrapper.temp_dict[user]["info"].message_id)
        
        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))

        try:
            #podria salir un recuadro para elegir el perfil
            if len(scrapper.find_element(By.CSS_SELECTOR, 'img[data-type="image"][class="img contain"]')) == 4:

                #Aqui elijo el perfil
                scrapper.find_element(By.CSS_SELECTOR, 'div[tabindex="0"][data-focusable="true"][data-tti-phase="-1"][data-mcomponent="MContainer"][data-type="container"][class="m bg-s5"]').click()

                scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'input[type="password"]')))
                
                with open(os.path.join(user_folder(user), "cookies.pkl"), "rb") as file_cookies:
                    
                    scrapper.temp_dict[user]["password"] = dill.load(file_cookies)["password"]

                    for i in scrapper.temp_dict[user]["password"]:
                        scrapper.find_element(By.CSS_SELECTOR, 'input[type="password"]').send_keys(i)

                        time.sleep(0.5)

                    #click en continuar
                    scrapper.find_elements(By.CSS_SELECTOR, 'div[data-mcomponent="MContainer"][data-tti-phase="-1"][data-focusable="true"][data-type="container"][tabindex="0"]')[1].click()

                    #saldra un cartel de doble autenticacion obligatoria
                    #en este punto, si el usuario ya confirmo una doble autenticacion anteriormente, facebook ira directamente a la main page y no requerirá verificacion
                    try:
                        scrapper.wait_s.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[class="fl ac am"]')))
                        
                        #dare en aceptar
                        try:
                            scrapper.find_element(By.CSS_SELECTOR, 'div[class="fl ac am"]').click()

                            scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'input[type="text"]')))

                            for i in scrapper.temp_dict[user]["user"]:

                                scrapper.find_element(By.CSS_SELECTOR, 'input[type="text"]').send_keys(i)

                                time.sleep(0.5)

                            handlers(bot, user , "Introduce el código del SMS o el código que se te fué enviado a Whatsapp, revisa ambas\n\nEn caso de que no llegue, espera un momento..." , "correo_o_numero_verificacion", scrapper.temp_dict)

                            for i in scrapper.temp_dict[user]["res"]:

                                scrapper.find_element(By.CSS_SELECTOR, 'input[type="password"]').send_keys(i)

                                time.sleep(0.5)
                            
                            #Cuidado aqui! No termine de localizar el boton para continuar, este lo agrego porque creo que funcionará
                            scrapper.find_elements(By.CSS_SELECTOR, 'div[data-mcomponent="MContainer"][data-tti-phase="-1"][data-focusable="true"][data-type="container"][tabindex="0"]')[1].click()

                        except:

                            pass
                        

                    except:
                        pass

        except:
            pass


        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div#screen-root')))

        try:
            
            # scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="main"]')))
            print("Se cargaron cookies ")
            return ("ok", "login con cookies exitosamente", scrapper.temp_dict[user]["cookies_dict"])
    
        except Exception as er:
            give_error(bot, scrapper.driver, user, "ID usuario: "+ str(user) + "\n\nDescripción del error:\n" + str(format_exc()))
            return

    
    else:
        print("Se cargaron cookies_2")
        return ("ok", "login con cookies exitosamente", scrapper.temp_dict[user]["cookies_dict"])
        

def captcha(scrapper: scrapping, user, bot: telebot.TeleBot):
    try:
        if "captcha" in  scrapper.find_element(By.CSS_SELECTOR, "img.xz74otr.x168nmei.x13lgxp2.x5pf9jr.xo71vjh").get_attribute("src"):
            
            while True:
                #el enlace del captcha cambia cuando se introduce uno erróneo, ya que se vuelve a generar uno nuevo desde una dirección diferente
                scrapper.temp_dict[user]["url_captcha"] = scrapper.find_element(By.CSS_SELECTOR, "img.xz74otr.x168nmei.x13lgxp2.x5pf9jr.xo71vjh").get_attribute("src")
                #Esperar a que la foto se muestre adecuadamente en la pantalla para que selenium pueda hacerle captura
                scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "img.xz74otr.x168nmei.x13lgxp2.x5pf9jr.xo71vjh")))
                
            
                handlers(bot, user, "ATENCION!\nHa aparecido un captcha!\n\nIntroduce el código proporcionado en la foto CORRECTAMENTE para continuar...", "captcha", scrapper.temp_dict, file=telebot.types.InputFile(make_captcha_screenshoot(scrapper.find_element(By.CSS_SELECTOR, "img.xz74otr.x168nmei.x13lgxp2.x5pf9jr.xo71vjh"), user)))
                                   
                
                for i in scrapper.temp_dict[user]["res"]:
                    scrapper.find_element(By.CSS_SELECTOR, "input#«r1»").send_keys(i)
                    time.sleep(0.5)
                
                #click en continuar    
                
                scrapper.find_elements(By.CSS_SELECTOR, "span.x1lliihq.x193iq5w.x6ikm8r.x10wlt62.xlyipyv.xuxw1ft")[-1].click()
                
                try:
                    
                    scrapper.wait.until(ec.url_changes(scrapper.driver.current_url))
                    
                except:
                    pass
                    
                finally:
                    try:                                   
                        if "captcha" in  scrapper.find_element(By.CSS_SELECTOR, "img.xz74otr.x168nmei.x13lgxp2.x5pf9jr.xo71vjh").get_attribute("src"):
                            
                            if scrapper.find_element(By.CSS_SELECTOR, "img.xz74otr.x168nmei.x13lgxp2.x5pf9jr.xo71vjh").get_attribute("src") != scrapper.temp_dict[user]["url_captcha"]:
                                
                                # scrapper.temp_dict[user]["info"] = bot.edit_message_text(text="🆕 Mensaje de Información\n\nEl codigo que introduciste es incorrecto! :( \n\nVuelve a intentarlo", chat_id=user, message_id=scrapper.temp_dict[user]["info"].message_id)
                                
                                bot.send_message(user, "🆕 Mensaje de Información\n\nEl codigo que introduciste es incorrecto! :( \n\nVuelve a intentarlo")
                                
                                continue
                            
                        else:
                                                
                            # scrapper.temp_dict[user]["info"] = bot.edit_message_text(text="🆕 Mensaje de Información\n\nEl código introducido es correcto :)\n\nSeguiré procediendo...", chat_id=user, message_id=scrapper.temp_dict[user]["info"].message_id)
                            
                            bot.send_message(user, "🆕 Mensaje de Información\n\nEl código introducido es correcto :)\n\nSeguiré procediendo...")
                            
                            return ("ok", "captcha resuelto!")    
                            
                    except NoSuchElementException:
                        print("captcha resuelto")
                        return ("ok", "captcha resuelto!")    

                
                    
                
                
                
                
        else: 
            return ("no", "Al parecer no hay captcha")
    except NoSuchElementException:
        return ("no", "Al parecer no hay captcha")
    
    except:
        give_error(bot, scrapper.driver, user, "ID usuario: " + str(user) + "\n\nDescripción del error:\n" + str(format_exc()))


    
def loguin(scrapper: scrapping, user, bot, **kwargs):

    """
    Si no se proporciona un user_id, se creará uno nuevo
    
    Hace loguin en Facebook, determinará si hacer loguin desde cero o no si se le proporciona un user y si hay algún archivo de ese usuario en la BD
    """
    
    
    

    if list(filter(lambda file: file == "cookies.pkl", os.listdir(user_folder(user)))):
        
        # scrapper.temp_dict[user]["info"] = bot.edit_message_text(text="🆕 Mensaje de Información\n\nHay cookies de la sesion, voy a cargarlas.\n\nEspere un momento...", chat_id=user, message_id=scrapper.temp_dict[user]["info"].message_id)
        
        
        scrapper.temp_dict[user]["res"] = cargar_cookies(scrapper, user, bot)    
        if scrapper.temp_dict[user]["res"][0] == "error":
            give_error(bot, scrapper.driver, user, scrapper.temp_dict[user]["res"])
        

        if not scrapper.collection.find_one({"telegram_id": user}):
            scrapper.collection.insert_one({"_id": int(time.time()), "telegram_id": user})
            guardar_cookies(scrapper, user)
        
        return scrapper.temp_dict[user]["res"]
    
    else:
        if scrapper.collection.find_one({"telegram_id": user}):
            scrapper.temp_dict[user]["res"] = scrapper.collection.find_one({"telegram_id": user})
            if scrapper.temp_dict[user]["res"].get("cookies"):
                guardar_cookies(scrapper, user, cookiespkl=scrapper.temp_dict[user]["res"]["cookies"])
                return loguin(scrapper, user, bot)

            else:
                return loguin_cero(scrapper, user, bot)

        else:

            scrapper.collection.insert_one({"_id": int(time.time()), "telegram_id": user})
                
            return loguin_cero(scrapper, user, bot)
            
                
        
    


# input.x1s85apg => Input para enviar los videos

def cookies_caducadas(scrapper: scrapping, user, bot):

    
    if scrapper.find_element(By.CSS_SELECTOR, 'div[class="_45ks"]'):
        scrapper.temp_dict[user]["perfiles"] = scrapper.find_elements(By.CSS_SELECTOR, 'div[class="removableItem _95l5 _63fz"]')
        scrapper.temp_dict[user]["texto"] = ""
        scrapper.temp_dict[user]["lista_perfiles"] = []
        scrapper.temp_dict[user]["teclado"] = ReplyKeyboardMarkup(True, True, row_width=1, input_field_placeholder="Selecciona una cuenta")
        
        for e,i in enumerate(scrapper.temp_dict[user]["perfiles"], 1):
            scrapper.temp_dict[user]["lista_perfiles"].append(i.text)
            scrapper.temp_dict[user]["texto"] += str(e) + " => " + i.text
            scrapper.temp_dict[user]["teclado"].add(i.text)
            
        
        handlers(bot, user, "¿Cual cuenta deseas usar?\n\n" + str(scrapper.temp_dict[user]["texto"]), "perfil_seleccion", scrapper.temp_dict, markup=scrapper.temp_dict[user]["teclado"])
        

        
        #le resto uno para coincidir con el índice
        scrapper.temp_dict[user]["perfiles"][scrapper.temp_dict[user]["res"]].click()
        
        while True:
            handlers(bot, user, "Introduce la contraseña de esta cuenta a continuación", "password" ,scrapper.temp_dict)
            

                        
            scrapper.wait.until(ec.visibility_of_all_elements_located((By.CSS_SELECTOR, 'input[id="pass"][type="password"]')))[-1].send_keys(scrapper.temp_dict[user]["password"])
            
            
            try:
                e = scrapper.find_element(By.CSS_SELECTOR, 'input#email"')
                
            except:
                e = None
                
            if e:
                handlers(bot, user, "Introduce a continuación tu <b>Correo</b> o <b>Número de Teléfono</b> (agregando el código de tu país por delante ej: +53, +01, +52, etc) con el que te autenticas en Facebook: ", "user", scrapper.temp_dict)
                

                
                scrapper.find_element(By.CSS_SELECTOR, 'input#email"').send_keys(scrapper.temp_dict[user]["user"])

            
            
            try:
                #click para recordar contraseña
                scrapper.find_element(By.CSS_SELECTOR, 'span[class="_9ai8"]').click()
            
            except NoSuchElementException:
                pass
            
            #click en iniciar sesión
            scrapper.find_elements(By.CSS_SELECTOR, 'button[name="login"]')[-1].click()
            scrapper.wait.until(ec.url_changes(scrapper.driver.current_url))
            scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'body')))
            scrapper.temp_dict[user]["res"] = captcha(scrapper, user, bot)
            if scrapper.temp_dict[user]["res"] == "error":
                print(scrapper.temp_dict[user]["res"][1])
                
            elif scrapper.temp_dict[user]["res"][0] in ["ok", "no"]:
                guardar_cookies(scrapper, user)
                break

            elif scrapper.find_element(By.CSS_SELECTOR, 'div[class="mvm _akly"]'):
                scrapper.driver.back()
                continue

def loguin_cero(scrapper: scrapping, user, bot : telebot.TeleBot, load_url=True, **kwargs):

    print("Estoy usando el loguin desde cero")
    
    
    def doble_auth(scrapper: scrapping , user, bot: telebot.TeleBot):


        def doble_auth_codigo(scrapper: scrapping , user, bot: telebot.TeleBot):
        # e = scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))

            
            
            
            scrapper.wait.until(ec.any_of(lambda driver: driver.find_element(By.XPATH, '//*[contains(text(), "Backup code")]')))

            #aqui le doy click a el metodo de auth que en este caso sería por codigo de respaldo
            scrapper.find_element(By.XPATH, '//*[contains(text(), "Backup code")]').click()

            #le doy click a continuar
            scrapper.find_element(By.XPATH, '//*[contains(text(), "Continue")]').click()
            # scrapper.find_elements(By.CSS_SELECTOR, 'div[data-bloks-name="bk.components.Flexbox"][role="button"][tabindex="0"]')[1].click()

            #el siguiente elemento es el input en el que va el código
            scrapper.wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, 'input[inputmode="numeric"]')))
            
            scrapper.temp_dict[user]["e"] = scrapper.find_element(By.CSS_SELECTOR, 'input[inputmode="numeric"]')
            
            
            handlers(bot, user, "A continuación, introduce uno de los códigos de respaldo de Facebook\n\n(Estos códigos son de 8 dígitos numéricos y puedes obtenerlos en el centro de cuentas en los ajustes de tu cuenta de Facebook)" , "codigo_respaldo", scrapper.temp_dict, markup=ForceReply())
            
            #para borrar los espacios en el codigo de respaldo
            if re.search(r"\D", scrapper.temp_dict[user]["res"].text):
                scrapper.temp_dict[user]["res"].text = scrapper.temp_dict[user]["res"].text.replace(re.search(r"\D+", scrapper.temp_dict[user]["res"].text).group(), "").strip()

            for i in scrapper.temp_dict[user]["res"].text:
                scrapper.temp_dict[user]["e"].send_keys(i)
                time.sleep(0.5)
            
            
            scrapper.temp_dict[user]["url_actual"] = scrapper.driver.current_url
            

            #click en el boton de continuar
            scrapper.find_element(By.XPATH, '//*[contains(text(), "Continue")]').click()
            
            

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

            handlers(bot, user, "A continuación, ingresa el código númerico que ha sido enviado al email vinculado a esta cuenta para finalizar el loguin...","email_verification", scrapper.temp_dict)

            scrapper.find_element(By.CSS_SELECTOR, 'input').send_keys(scrapper.temp_dict[user]["res"].strip())


            scrapper.find_element(By.XPATH, '//*[contains(text(), "Continue")]').click()

            return "ok"


        scrapper.wait.until(ec.any_of(ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Check your email")]')),
        ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Try another way")]'))))

        try:
            if scrapper.find_element(By.XPATH, '//*[contains(text(), "Try another way")]'):
                scrapper.temp_dict[user]["doble"] = True
                try:
                    #Si este elemento no está es que aún está en el loguin debido a que los datos introducidos fueron incorrectos (es el mismo de arriba)
                    scrapper.find_element(By.XPATH, '//*[contains(text(), "Try another way")]').click()
                    
                    scrapper.wait_s.until(ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Choose a way to confirm")]')))
                    
                    try:
                        scrapper.find_element(By.XPATH, '//*[contains(text(), "Email")]').click()
                        scrapper.find_element(By.XPATH, '//*[contains(text(), "Continue")]').click()
                        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'body')))

                        print("Haremos la doble autenticación enviando el código al correo")
                        doble_auth_email_verification(scrapper, user, bot)   
                    except:
                        print("Haremos la doble autenticación con los códigos de recuperación")
                        doble_auth_codigo(scrapper, user, bot)

                except:

                    bot.send_photo(user, telebot.types.InputFile(make_screenshoot(scrapper.driver, user)) ,"Has introducido tus datos de loguin incorrectamente...\nPor favor, vuelve a intentarlo luego del próximo mensaje")
                    
                    del scrapper.temp_dict[user]["user"]
                    del scrapper.temp_dict[user]["password"]

                    return loguin_cero(scrapper, user, bot)
                
                
                
        except:
            pass            
                
        


        try:
            if scrapper.find_element(By.XPATH, '//*[contains(text(), "Check your email")]') and not scrapper.temp_dict[user]["doble"]:
                scrapper.temp_dict[user]["doble"] = True    
                print("Haremos la doble autenticación enviando el código al correo")
                doble_auth_email_verification(scrapper, user, bot)            
        
        except:
            pass
        
            
        
        

        if not scrapper.temp_dict[user].get("doble"):
            raise Exception("Abriste la funcion de doble autenticacion pero realmente no habia...que paso?")
        
        try:
            scrapper.temp_dict[user]["doble"] = False

            
            scrapper.wait.until(ec.url_changes(scrapper.temp_dict[user]["url_actual"]))
            

        except:
            pass

        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'body')))
                            
        #sustituto de remember_browser
        try:
            if scrapper.find_element(By.CSS_SELECTOR, 'div#screen-root'):

                bot.send_message(user, "🆕 Mensaje de Información\n\nOk, el codigo introducido es correcto")
        
                return ("ok", "se ha dado click en confiar dispositivo")
        
        except Exception as err:

            if not "save-device" in scrapper.driver.current_url:

                bot.send_message(user, m_texto("Has Introducido un código incorrecto!\n...Espera un momento..."))

                return loguin_cero(scrapper, user, bot)
            
            elif "save-device" in scrapper.driver.current_url:
                pass
            
            else:
                raise Exception("No se ha encontrado la pagina de confiar en este dispositivo?")
            
        

        
        #click en confiar en este dispositivo
        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="button"]')))
        scrapper.find_element(By.CSS_SELECTOR, 'div[role="button"]').click()

        # scrapper.temp_dict[user]["info"] = bot.edit_message_text(text="🆕 Mensaje de Información\n\nOk, el codigo introducido es correcto", chat_id=user, message_id=scrapper.temp_dict[user]["info"].message_id)     
        
        bot.send_message(user, "🆕 Mensaje de Información\n\nOk, el codigo introducido es correcto")
        
        return ("ok", "se ha dado click en confiar dispositivo")
            

            
            


    load(scrapper, "https://m.facebook.com/login/")
    
    # if load_url:

    #     load(scrapper, "https://m.facebook.com/login/")
                
    # else:
    #     load(scrapper, "https://facebook.com")
    
    scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))
    #-----------------obtener usuario para loguin---------------
    try:
        #A veces aparecerá una presentacion de unirse a facebook, le daré a que ya tengo una cuenta...
        scrapper.wait_s.until(ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "I already have an account")]')))
        scrapper.find_element(By.XPATH, '//*[contains(text(), "I already have an account")]').click()

        scrapper.wait.until(ec.any_of(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "input")) >= 2))

        scrapper.temp_dict[user]["e"] = scrapper.find_elements(By.CSS_SELECTOR, "input")[0]


        
    except:
        pass


    scrapper.wait.until(ec.any_of(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "input")) >= 2))
    # scrapper.temp_dict[user]["e"] = driver.find_element(By.ID, "m_login_email")
    scrapper.temp_dict[user]["e"] = scrapper.find_elements(By.CSS_SELECTOR, "input")[0]


    
    

    if not scrapper.temp_dict[user].get("user"):
        handlers(bot, user, "Introduce a continuación tu <b>Correo</b> o <b>Número de Teléfono</b> (agregando el código de tu país por delante ej: +53, +01, +52, etc) con el que te autenticas en Facebook: ", "user", scrapper.temp_dict)

    ActionChains(scrapper.driver).send_keys_to_element(scrapper.temp_dict[user]["e"], scrapper.temp_dict[user]["user"]).perform()
    # scrapper.temp_dict[user]["e"].send_keys(scrapper.temp_dict[user]["user"])
    
    
    #-----------------obtener password para loguin---------------
    # scrapper.temp_dict[user]["e"] = driver.find_element(By.ID, "m_login_password")
    scrapper.temp_dict[user]["e"] = scrapper.find_elements(By.CSS_SELECTOR, "input")[1]
    
    if not scrapper.temp_dict[user].get("password"):
        handlers(bot, user, "Introduce a continuación la contraseña", "password", scrapper.temp_dict)
    

    scrapper.temp_dict[user]["url_actual"] = scrapper.driver.current_url

    ActionChains(scrapper.driver).send_keys_to_element(scrapper.temp_dict[user]["e"], scrapper.temp_dict[user]["password"]).perform()
    
    # scrapper.temp_dict[user]["e"].send_keys(scrapper.temp_dict[user]["password"])
    
    scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-anchor-id="replay"]')))

    # scrapper.find_element(By.CSS_SELECTOR, 'div[data-anchor-id="replay"]').click()
    

    try:
        scrapper.wait_s.until(ec.element_to_be_clickable((By.XPATH, '//span[contains(text(), "Log in")]')))
        scrapper.find_element(By.XPATH, '//span[contains(text(), "Log in")]').click()
    except:
        scrapper.find_elements(By.CSS_SELECTOR, 'div[role="button"]')[2].click()
        

    try:
        scrapper.wait.until(ec.url_changes(scrapper.temp_dict[user]["url_actual"]))
        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'body')))
    except:
        pass
    


    
    
    try:
        #cuando no introduces bien ninguno de tus datos:
        if scrapper.find_element(By.CSS_SELECTOR, 'div[class="wbloks_73"]'):
            
            bot.send_photo(user, telebot.types.InputFile(make_screenshoot(scrapper.driver, user)), "Al parecer los datos que me has enviado son incorrectos\nTe he enviado una captura de lo que me muestra Facebook\n\nPor favor ingrese <b>correctamente</b> sus datos otra vez...")
            del scrapper.temp_dict[user]["password"]
            del scrapper.temp_dict[user]["user"]
            return loguin_cero(scrapper, user, bot)
            
    except:
        pass

    

    if scrapper.driver.current_url.endswith("#"):
        
        doble_auth(scrapper, user, bot)
        # if "No se ha podido dar click en el botón de doble autenticación" in scrapper.temp_di
            
            
    scrapper.wait.until(ec.any_of(lambda driver: driver.find_elements(By.CSS_SELECTOR, 'body')))

    try:
        scrapper.temp_dict[user]["res"] = scrapper.wait_s.until(ec.any_of(lambda driver: "save-device" in driver.current_url))
    except:
        scrapper.temp_dict[user]["res"] = None

    if scrapper.temp_dict[user]["res"]:

        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-bloks-name="bk.components.Flexbox"][role="button"]')))

        scrapper.find_element(By.CSS_SELECTOR, 'div[data-bloks-name="bk.components.Flexbox"][role="button"]').click()

        scrapper.wait.until(ec.invisibility_of_element_located((By.CSS_SELECTOR, 'div[data-bloks-name="bk.components.Flexbox"][role="button"]')))


            
        
        

    # scrapper.temp_dict[user]["info"] = bot.edit_message_text(text=f"🆕 Mensaje de Información\n\nNo has introducido tus datos correctamente, vuelve a intentarlo", chat_id=user, message_id=scrapper.temp_dict[user]["info"].message_id) 

    


    try:
        # if scrapper.wait.until(ec.all_of(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, 'div[data-tti-phase="-1"][role="button"][tabindex="0"][data-focusable="true"][data-mcomponent="MContainer"][data-type="container"]')) >= 3 and not "save-device" in driver.current_url)):
        
        #error de loguin validacion
        if scrapper.wait.until(ec.any_of(lambda driver: driver.find_elements(By.CSS_SELECTOR, 'div#screen-root') and not "save-device" in driver.current_url)):

            guardar_cookies(scrapper, user, loguin={"user": scrapper.temp_dict[user]["user"], "password": scrapper.temp_dict[user]["password"]})

            
            
            return ("ok", "loguin desde cero satisfactorio :)")

        
    except:
        
        bot.send_photo(user, telebot.types.InputFile(make_screenshoot(scrapper.driver, user)) , "🆕 Mensaje de Información\n\nNo has introducido tus datos correctamente, vuelve a intentarlo")

        del scrapper.temp_dict[user]["password"]
        del scrapper.temp_dict[user]["user"]

        return loguin_cero(scrapper, user, bot)
        



def publicacion(scrapper: scrapping, bot:telebot.TeleBot, user, load_url=True, contador = 0, **kwargs):
    
    scrapper.temp_dict[user]["if_cancelar"]()

    if scrapper.temp_dict[user].get("contador"):
        contador = scrapper.temp_dict[user]["contador"]

    

        

    def obtener_texto(error: bool, aprobar=False):
            
        try:
            scrapper.temp_dict[user]["info"] = bot.edit_message_text("✅Se ha publicado en: " + str(len(scrapper.temp_dict[user]["publicacion"]["publicados"])) + " grupo(s)" + "\n⛔Han quedado pendientes en: " + str(len(scrapper.temp_dict[user]["publicacion"]["pendientes"])) + " grupo(s)" + "\n❌Se han producido errores en: " + str(len(scrapper.temp_dict[user]["publicacion"]["error"])) + " grupo(s)", user, scrapper.temp_dict[user]["info"].message_id)
        except:
            scrapper.temp_dict[user]["info"] = bot.send_message(user, "✅Se ha publicado en: " + str(len(scrapper.temp_dict[user]["publicacion"]["publicados"])) + " grupo(s)" + "\n⛔Han quedado pendientes en: " + str(len(scrapper.temp_dict[user]["publicacion"]["pendientes"])) + " grupo(s)" + "\n❌Se han producido errores en: " + str(len(scrapper.temp_dict[user]["publicacion"]["error"])) + " grupo(s)")
        
        #4000 caracteres es el limite de telegram para los mensajes, si sobrepasa la cantidad tengo que enviar otro mensaje            



        if len(scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] + "❌ " + scrapper.temp_dict[user]["publicacion"]["nombre"] + "\n") >= 4000:
            
            
            if error == True:
                scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] = str(contador + 1) + "=> ❌ <code>" + scrapper.temp_dict[user]["publicacion"]["nombre"] + "</code> " 
            else:
                if aprobar:
                    scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] = str(contador + 1) + "=> ⛔ <code>" + scrapper.temp_dict[user]["publicacion"]["nombre"] + "</code> " 
                else:
                    scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] = str(contador + 1) + "=> ✅ <code>" + scrapper.temp_dict[user]["publicacion"]["nombre"] + "</code> "
                
            
            
            #para asegurarme de que hay que enviar un nuevo mensaje retorno "nuevo" y si es admin va a devolver el tiempo de demora
            if user == scrapper.admin:
                scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] = scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] + get_time(scrapper, user) + "\n"
                return ("nuevo", scrapper.temp_dict[user]["publicacion"]["texto_publicacion"])
            
            else:
                scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] = scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] + "\n"
                return ("nuevo", scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] + "\n")
                
        else:
            
            if error == True:
                scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] += str(contador + 1) + "=> ❌ <code>" + scrapper.temp_dict[user]["publicacion"]["nombre"] + "</code> "
                
            else:
                if aprobar:
                    scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] += str(contador + 1) + "=> ⛔ <code>" + scrapper.temp_dict[user]["publicacion"]["nombre"] + "</code> "
                else:
                    scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] += str(contador + 1) + "=> ✅ <code>" + scrapper.temp_dict[user]["publicacion"]["nombre"] + "</code> "

            
            if user == scrapper.admin:
                scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] = scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] + get_time(scrapper, user) + "\n"

                return ("no", scrapper.temp_dict[user]["publicacion"]["texto_publicacion"])
            
            else:
                scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] = scrapper.temp_dict[user]["publicacion"]["texto_publicacion"] + "\n"

                return ("no", scrapper.temp_dict[user]["publicacion"]["texto_publicacion"])

    
    def enviar_grupos():
        

        if scrapper.temp_dict[user]["publicacion"]["nombre"] in scrapper.temp_dict[user]["publicacion"]["publicados"]:
            print("✅ " + str(scrapper.temp_dict[user]["publicacion"]["nombre"]))
            scrapper.temp_dict[user]["res"] = obtener_texto(False)

        elif scrapper.temp_dict[user]["publicacion"]["nombre"] in scrapper.temp_dict[user]["publicacion"]["pendientes"]:
            print("⛔️ " + str(scrapper.temp_dict[user]["publicacion"]["nombre"]))
            scrapper.temp_dict[user]["res"] = obtener_texto(True, True)

        elif scrapper.temp_dict[user]["publicacion"]["nombre"] in scrapper.temp_dict[user]["publicacion"]["error"]:
            print("❌ {}".format(scrapper.temp_dict[user]["publicacion"]["nombre"])) 
            scrapper.temp_dict[user]["res"] = obtener_texto(True)



        if scrapper.temp_dict[user]["res"][0] == "nuevo":
            scrapper.temp_dict[user]["publicacion"]["msg_publicacion"] = bot.send_message(user, scrapper.temp_dict[user]["res"][1])

        else:

            try:
                scrapper.temp_dict[user]["publicacion"]["msg_publicacion"] = bot.edit_message_text(scrapper.temp_dict[user]["res"][1] , user, scrapper.temp_dict[user]["publicacion"]["msg_publicacion"].message_id)

            except:
                scrapper.temp_dict[user]["publicacion"]["msg_publicacion"] = bot.send_message(user, scrapper.temp_dict[user]["res"][1])


    # if "bookmarks" in scrapper.driver.current_url:
    #     scrapper.find_element(By.CSS_SELECTOR, 'div[role="button"]').click()

    if kwargs.get("diccionario"):
        scrapper.temp_dict = kwargs["diccionario"]

    if scrapper.temp_dict[user].get("repetir") and not scrapper.interrupcion:
        bot.send_message(user, m_texto("A continuación, comenzaré a publicar en breve...\n\nEsta será la vez #<b>{}</b> que publicaré por todos los grupos disponibles". format(scrapper.temp_dict[user]["c_r"])))
        

    
    
    if not scrapper.temp_dict[user].get("repetir") and not scrapper.interrupcion:
        handlers(bot, user, "A continuación, establece un tiempo de espera luego de finalizada la publicación masiva para volver a repetir el proceso en bucle\nIngresa el tiempo de repetición en HORAS\n\nSi solo deseas que no se repita y se publique solamente esta vez en todos tus grupos pulsa en '<b>No Repetir</b>'", "bucle_publicacion", scrapper.temp_dict, markup=ReplyKeyboardMarkup(True, True).add("No Repetir"))

        if scrapper.temp_dict[user]["res"]:

            scrapper.temp_dict[user]["repetir"] = scrapper.temp_dict[user]["res"]
    
    
    scrapper.temp_dict[user]["a"] = ActionChains(scrapper.driver, duration=0)

    scrapper.temp_dict[user]["tiempo_debug"] = []
    
    if kwargs.get("temp_dic"):
        scrapper.temp_dict[user]["publicacion"] = kwargs.get("info_publicacion")
    
    elif not scrapper.temp_dict[user].get("publicacion"):
        scrapper.temp_dict[user]["publicacion"] = {"publicados" : [], "error" : [], "pendientes": [], "lista_grupos": [] ,"texto_publicacion": "Lista de Grupos en los que se ha Publicado:\n\n"}
        
        
    scrapper.temp_dict[user]["publicacion"]["lista_grupos"] = []


    load(scrapper, "https://m.facebook.com/groups/")
    
    
    #bucle para publicar por los grupos
    
    while True:


        if scrapper.temp_dict[user].get("demora"):
            scrapper.temp_dict[user]["contador"] = contador


        # if scrapper.temp_dict[user]["publicacion"].get("nombre"):
        #     if not re.search(scrapper.temp_dict[user]["publicacion"]["nombre"] , scrapper.temp_dict[user]["publicacion"]["texto_publicacion"]):
        #         enviar_grupos()

        if contador % 10 == 0 and contador != 0:
            scrapper.driver.refresh()

        #Esta variable es para poder luego guardarla en la BD de MongoDB
        

        administrar_BD(scrapper, bot, user=user, publicacion=scrapper.temp_dict[user]["publicacion"])

        scrapper.temp_dict[user]["if_cancelar"]()
        
        
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
        
    
        
        
        if not scrapper.temp_dict[user]["publicacion"]["lista_grupos"]:
            
            give_error(bot, scrapper.driver, user, "¡No hay ningún grupo al que publicar!\n\nDescripcion del error:\n" + str(format_exc()))
        
        #si ya recorrimos todos los elementos de la lista de grupos el contador tendrá un valor mayor a la cantidad de grupos de la lista ya que en cada vuelta de bucle aumenta (le sumo 1 porque el índice de los grupos comienza en 0)

        
        while len(scrapper.temp_dict[user]["publicacion"]["lista_grupos"]) < (contador + 1):

            
            get_time_debug(scrapper, user)

            scrapper.temp_dict[user]["e"] = obtener_grupos(scrapper, user, True)

            scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "obtener grupos luego de que el contador fuera mayor linea {}".format(traceback.extract_stack()[-1].lineno)))
                        

            if len(scrapper.temp_dict[user]["e"]) == len(scrapper.temp_dict[user]["publicacion"]["lista_grupos"]):

                bot.unpin_all_chat_messages(user)
                
                if not scrapper.temp_dict[user].get("repetir"):

                    bot.send_message(user, "Se ha publicado exitosamente en " + str(len(scrapper.temp_dict[user]["publicacion"]["publicados"]) + len(scrapper.temp_dict[user]["publicacion"]["pendientes"])) + " grupo(s)")

                    return ("ok", "Se ha publicado exitosamente en " + str(len(scrapper.temp_dict[user]["publicacion"]["publicados"]) + len(scrapper.temp_dict[user]["publicacion"]["pendientes"])) + " grupo(s)")
                
                else:
                    
                    bot.send_message(user, m_texto("Publiqué en " + str(len(scrapper.temp_dict[user]["publicacion"]["publicados"]) + len(scrapper.temp_dict[user]["publicacion"]["pendientes"])) + " grupos satisfactoriamente\nAhora esperaré {} hora(s) y {} minuto(s) antes de volver a publicar masivamente\n\nCuando quieras cancelar envíame /cancelar".format(int(scrapper.temp_dict[user]["repetir"] / 60 / 60), int(scrapper.temp_dict[user]["repetir"] / 60 % 60))))
                    
                    return ("repetir", scrapper.temp_dict[user]["c_r"])

                    

            
            else:                
                scrapper.temp_dict[user]["publicacion"]["lista_grupos"] = scrapper.temp_dict[user]["e"].copy()

                del scrapper.temp_dict[user]["e"]

        




        try:
            scrapper.driver.execute_script('document.querySelectorAll("div.m.fixed-container.bottom").forEach(e => e.remove());')
        except:
            pass
        
        get_time_debug(scrapper, user)

        hacer_scroll(scrapper, user,
                     scrapper.temp_dict[user]["publicacion"]["lista_grupos"][contador].size["height"] * contador + scrapper.temp_dict[user]["top"] - scrapper.driver.execute_script("return window.pageYOffset;"),
                     (scrapper.temp_dict[user]["publicacion"]["lista_grupos"][contador].size["height"] * contador + scrapper.temp_dict[user]["top"] - scrapper.driver.execute_script("return window.pageYOffset;")) // (scrapper.temp_dict[user]["publicacion"]["lista_grupos"][contador].size["height"] * 8 + scrapper.temp_dict[user]["top"]))

        # hacer_scroll(scrapper, user, scrapper.temp_dict[user]["publicacion"]["lista_grupos"][contador], (contador + 1) // 4, contador)

        for i in range(3):
            try:
                scrapper.wait_s.until(ec.element_to_be_clickable(scrapper.temp_dict[user]["publicacion"]["lista_grupos"][contador]))
                scrapper.temp_dict[user]["publicacion"]["lista_grupos"][contador].click()
                break
            except Exception as e:
                if i >= 2:
                    raise Exception("No se pudo clickear en el grupo: " + scrapper.temp_dict[user]["publicacion"]["nombre"])

                if isinstance(e, IndexError):
                    scrapper.temp_dict[user]["publicacion"]["lista_grupos"] = obtener_grupos(scrapper, user, True)

                scrapper.temp_dict[user]["a"].scroll_to_element(scrapper.temp_dict[user]["publicacion"]["lista_grupos"][contador]).perform()

                time.sleep(2)


        scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "hacer scroll y darle click al grupo #{} linea {}".format(contador + 1, traceback.extract_stack()[-1].lineno)))
        
        #Guardar el nombre del grupo....
        get_time_debug(scrapper, user)

        scrapper.wait.until(ec.invisibility_of_element_located(scrapper.temp_dict[user]["publicacion"]["lista_grupos"][contador]))
        scrapper.wait.until(ec.any_of(lambda driver: driver.find_elements(By.CSS_SELECTOR, 'h1')[1].text))


        scrapper.temp_dict[user]["publicacion"]["nombre"] = scrapper.find_elements(By.CSS_SELECTOR, 'h1')[1].text.split(">")[0].strip().replace("\n", " ")

        scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "obtener el nombre del grupo #{} linea {}".format(contador + 1, traceback.extract_stack()[-1].lineno)))
        
        get_time_debug(scrapper, user)
        
        try:
            
            #esperar a "Write something..." o "What are you selling?"

            scrapper.wait_s.until(ec.visibility_of_element_located((By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[6]/div[2]/div')))
            
            
            
            
            for i in range(3):
                try:
                    scrapper.wait.until(ec.visibility_of_element_located((By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[6]/div[2]/div')))

                    scrapper.find_element(By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[6]/div[2]/div').click()

                    break

                except:
                    if i >= 2:
                        raise Exception("No está el elemento para ir al formulario de la publicación")
                    
                    else:
                        try:
                            scrapper.temp_dict[user]["a"].scroll_to_element(scrapper.find_element(By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[6]/div[2]/div')).perform()
                        except:
                            pass

                        time.sleep(2)

        except:
            #Maximo de peticiones:
            #Puede darse el caso de que el grupo donde se planea publicar las publicaciones tengan que ser aprobadas por los administradores y ya se ha sobrepasado la cantidad de publicaciones que el usuario puede pedir que se aprueben, entonces tampoco aparezca el botón 
            # O eso de arriba, o simplemente ocurrió un error

            scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "Espera del elemento 'Write something' pero ERROR al INTENTAR hacer scroll y darle click al elemento para entrar en el formulario de publicacion del grupo #{}, creo que he hecho muchas peticiones de publicación, linea {}".format(contador + 1, traceback.extract_stack()[-1].lineno)))

            scrapper.temp_dict[user]["publicacion"]["error"].append(scrapper.temp_dict[user]["publicacion"]["nombre"])


            contador += 1

            #el boton para ir atrás, a los grupos
            scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="button"]')))
            scrapper.find_element(By.CSS_SELECTOR, 'div[role="button"]').click()

            scrapper.temp_dict[user]["demora"] = time.time() - scrapper.temp_dict[user]["demora"]
            scrapper.temp_dict[user]["tiempo_debug"].append("=> " + "{}:{}".format(int(scrapper.temp_dict[user]["demora"] / 60), int(scrapper.temp_dict[user]["demora"] % 60)) + " minutos <= tiempo para publicar en el grupo")

            enviar_grupos()
            continue

            
        
        
     

        scrapper.wait_s.until(ec.invisibility_of_element_located((By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[6]/div[2]/div')))

        scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "Espera del elemento 'Write something' hacer scroll y darle click al elemento para entrar en el formulario de publicacion del grupo #{}, linea {}".format(contador + 1, traceback.extract_stack()[-1].lineno)))

        ##### 
        

        #-------------aqui estoy dentro del formulario de la publicación---------------------

        
        get_time_debug(scrapper, user)

        try:
            #Si este elemento se encuentra es que el grupo es de venta , los que dicen "selling" son son grupos atípicos y normalmente no dejan publicar tan facilmente, asi que los omito
            

            scrapper.wait_s.until(ec.any_of(lambda driver: driver.find_element(By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[3]/div[16]').find_element(By.CSS_SELECTOR, 'span[role="link"]')))

            scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "Espera del elemento que me indica si el grupo #{} es de ventas, SI ES DE VENTAS ERROR, linea {}".format(contador + 1, traceback.extract_stack()[-1].lineno)))

            scrapper.temp_dict[user]["publicacion"]["error"].append(scrapper.temp_dict[user]["publicacion"]["nombre"])

            contador += 1

            for i in range(2):
                #el boton para ir atrás, a los grupos
                scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="button"]')))
                scrapper.find_element(By.CSS_SELECTOR, 'div[role="button"]').click()

            
            scrapper.temp_dict[user]["demora"] = time.time() - scrapper.temp_dict[user]["demora"]
            scrapper.temp_dict[user]["tiempo_debug"].append("=> " + "{}:{}".format(int(scrapper.temp_dict[user]["demora"] / 60), int(scrapper.temp_dict[user]["demora"] % 60)) + " minutos <= tiempo para publicar en el grupo")

            enviar_grupos()
            continue

            
        except:
            pass

        try:

            scrapper.wait_s.until(ec.visibility_of_element_located((By.XPATH, '//*[@id="screen-root"]/div/div[2]/div[5]/div/div')))

            scrapper.find_element(By.XPATH, '//*[@id="screen-root"]/div/div[2]/div[5]/div/div').click()


        except Exception as e:
            #Los que dicen "selling" son grupos atípicos y normalmente no dejan publicar tan facilmente, asi que los omito

            scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "darle click al cajón de texto dentro del formulario de publicación en el grupo #{} HA HABIDO UN ERROR, el elemento no está, muy posiblemente sea un grupo de venta, linea {}".format(contador + 1, traceback.extract_stack()[-1].lineno)))
            scrapper.temp_dict[user]["publicacion"]["error"].append(scrapper.temp_dict[user]["publicacion"]["nombre"])

            contador += 1

            #el boton para ir atrás, a los grupos
            for i in range(2):
                scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="button"]')))
                scrapper.find_element(By.CSS_SELECTOR, 'div[role="button"]').click()

            scrapper.temp_dict[user]["demora"] = time.time() - scrapper.temp_dict[user]["demora"]
            scrapper.temp_dict[user]["tiempo_debug"].append("=> " + "{}:{}".format(int(scrapper.temp_dict[user]["demora"] / 60), int(scrapper.temp_dict[user]["demora"] % 60)) + " minutos <= tiempo para publicar en el grupo")

            enviar_grupos()
            continue


        #//*[@id="screen-root"]/div/div[2]/div[5]/div/div
        scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "darle click al cajón de texto dentro del formulario de publicación en el grupo #{} linea {}".format(contador + 1, traceback.extract_stack()[-1].lineno)))

        get_time_debug(scrapper, user)

        for i in range(10):
            try:
                scrapper.wait_s.until(ec.visibility_of_element_located((By.XPATH, '//*[@id="screen-root"]/div/div[2]/div[5]')))

                scrapper.temp_dict[user]["a"].send_keys_to_element(scrapper.find_element(By.XPATH, '//*[@id="screen-root"]/div/div[2]/div[5]'), scrapper.temp_dict[user]["texto_p"]).perform()

                break

            except:
                if i >= 9:
                    Exception("NO se econtró el cuadro de texto del formulario de la publicación")

                else:
                    time.sleep(2)
        
        #comprobar que el texto se insertó adecuadamente
        # scrapper.wait.until(ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "{}")]'.format(scrapper.temp_dict[user]["texto_p"].splitlines()[-1]))))

        scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "introducir el texto dentro del formulario de publicación en el grupo #{} linea {}".format(contador + 1, traceback.extract_stack()[-1].lineno)))


        
        if scrapper.temp_dict[user].get("foto_p"):
            get_time_debug(scrapper, user)

            envia_fotos_input(scrapper, user, scrapper.temp_dict[user]["foto_p"])

            scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "introducir la foto dentro del formulario de publicación en el grupo #{} linea {}".format(contador + 1, traceback.extract_stack()[-1].lineno)))

        


        get_time_debug(scrapper, user)



        scrapper.wait.until(ec.visibility_of_all_elements_located((By.XPATH, '//*[@id="screen-root"]/div/div[2]/*[@data-mcomponent="MContainer"]')))

        scrapper.find_elements(By.XPATH, '//*[@id="screen-root"]/div/div[2]/*[@data-mcomponent="MContainer"]')[-1].find_element(By.XPATH, './*').find_element(By.XPATH, './*').click()

        # scrapper.temp_dict[user]["e"] = scrapper.find_elements(By.XPATH, '//*[@id="screen-root"]/div/div[2]/*[@data-mcomponent="MContainer"]')[-1]

        # for i in range(5):
        
        #     try:
        #         scrapper.temp_dict[user]["e"].click()
        #         break

        #     except:
        #         if i >= 4:
        #             raise Exception("")

        #         scrapper.temp_dict[user]["e"] = scrapper.temp_dict[user]["e"].find_element(By.XPATH, './*')
                
        #         time.sleep(2)

        #esperar a regresar..
        scrapper.wait.until(ec.visibility_of_all_elements_located((By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[6]/div[2]/div')))

        scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "click en el botón de publicar en el formulario del grupo #{} linea {}".format(contador + 1, traceback.extract_stack()[-1].lineno)))

        #----------------------------Formulario END---------------------------------
               
        
        
        
        if not scrapper.temp_dict[user]["publicacion"].get("msg_publicacion"):
            
            
            scrapper.temp_dict[user]["info"] = bot.send_message(user, "✅Se ha publicado en: " + str(len(scrapper.temp_dict[user]["publicacion"]["publicados"])) + " grupo(s)" + "\n⛔Han quedado pendientes en: " + str(len(scrapper.temp_dict[user]["publicacion"]["pendientes"])) + " grupo(s)" + "\n❌Se han producido errores en: " + str(len(scrapper.temp_dict[user]["publicacion"]["error"])) + " grupo(s)")
            
            bot.pin_chat_message(scrapper.temp_dict[user]["info"].chat.id , scrapper.temp_dict[user]["info"].message_id, True)
            
            scrapper.temp_dict[user]["publicacion"]["msg_publicacion"] = bot.send_message(user, scrapper.temp_dict[user]["publicacion"]["texto_publicacion"])
        
        
        get_time_debug(scrapper, user)

        



        scrapper.wait.until(ec.visibility_of_all_elements_located((By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[6]/div[2]/div')))

        # scrapper.temp_dict[user]["a"].scroll_by_amount(0 , scrapper.find_element(By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[6]/div[2]/div').location["y"] + scrapper.find_element(By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[6]/div[2]/div').size["height"]).perform()


        #verificar si el nombre de la cuenta actual esta entre las últimas publicaciones del grupo para asi comprobar que se publicó correctamente
        for iteracion_buscar in range(3):

            # if iteracion_buscar == 0:
            #     scrapper.driver.refresh()
            #     facebook_popup(scrapper)


            def comprobar_p(scrapper, espera: int = 8):
                """
                True si encuentra la publicacion en el grupo
                False si no la encuentra
                "pendiente" si está pendiente
                """

                try:                             
                    #este revisa la primera publicación del grupo
                    WebDriverWait(scrapper.driver, espera).until(ec.all_of(lambda driver, scrapper=scrapper, user=user: driver.find_element(By.XPATH, '//*[contains(text(), "{}")]'.format(str(scrapper.temp_dict[user]["perfil_actual"]).strip())), lambda driver, scrapper=scrapper, user=user: driver.find_element(By.XPATH, '//*[contains(text(), "{}")]'.format(scrapper.temp_dict[user]["texto_r"]))))

                    scrapper.temp_dict[user]["publicacion"]["publicados"].append(scrapper.temp_dict[user]["publicacion"]["nombre"])

                    return True
                
                except:
                    pass
                    
                    
                try:
                    # if scrapper.find_element(By.XPATH, '//*[contains(text(), "Your post is pending")]'):

                    # if WebDriverWait(scrapper.driver, espera).until(ec.any_of(lambda driver: len(driver.find_element(By.XPATH, '//*[@id="screen-root"]/div/div[3]/div[8]').find_elements(By.XPATH, './*')) == 2, ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "pendiente")]')), ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "pending")]')))):

                    if WebDriverWait(scrapper.driver, espera).until(ec.any_of(ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "pendiente")]')), ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Your post is pending")]')))):

                        scrapper.temp_dict[user]["publicacion"]["pendientes"].append(scrapper.temp_dict[user]["publicacion"]["nombre"])
                            
                        return "pendiente"
                
                except:
                    pass

                    
                
                
                return False
                

            match comprobar_p(scrapper):
                
                case True:

                    break

                case "pendiente":


                    break

                case False:

                    if not iteracion_buscar >= 2:

                        if iteracion_buscar == 0:
                            scrapper.driver.refresh()

                        try:
                            for i in range(iteracion_buscar + 1):
                                scrapper.find_element(By.CSS_SELECTOR, "body").send_keys(Keys.END)
                        except:
                            pass

                        time.sleep(2)
                    #----------------------------------------------------------------------------------

                    else:
                        scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "comprobar que la publicación se hizo en el grupo pero se obtuvo UN ERROR en el grupo #{} linea {}".format(contador + 1, traceback.extract_stack()[-1].lineno)))

                        print("❌ {}".format(scrapper.temp_dict[user]["publicacion"]["nombre"]))
                        scrapper.temp_dict[user]["publicacion"]["error"].append(scrapper.temp_dict[user]["publicacion"]["nombre"])


                        #el boton para ir atrás, a los grupos
                        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="button"]')))
                        scrapper.find_element(By.CSS_SELECTOR, 'div[role="button"]').click()

                        contador += 1

                        scrapper.temp_dict[user]["demora"] = time.time() - scrapper.temp_dict[user]["demora"]
                        scrapper.temp_dict[user]["tiempo_debug"].append("=> " + "{}:{}".format(int(scrapper.temp_dict[user]["demora"] / 60), int(scrapper.temp_dict[user]["demora"] % 60)) + " minutos <= tiempo para publicar en el grupo")

                        enviar_grupos()
                        continue

                        
                                
                    

            



        scrapper.temp_dict[user]["tiempo_debug"].append(get_time_debug(scrapper, user, "comprobar que la publicación se hizo en el grupo #{}, SI SE HIZO, linea {}".format(contador + 1, traceback.extract_stack()[-1].lineno)))
        
        
        contador += 1

        #el boton para ir atrás, a los grupos
        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="button"]')))
        ActionChains(scrapper.driver).click(scrapper.find_element(By.CSS_SELECTOR, 'div[role="button"]')).perform()

        scrapper.temp_dict[user]["demora"] = time.time() - scrapper.temp_dict[user]["demora"]
        scrapper.temp_dict[user]["tiempo_debug"].append("=> " + "{}:{}".format(int(scrapper.temp_dict[user]["demora"] / 60), int(scrapper.temp_dict[user]["demora"] % 60)) + " minutos <= tiempo para publicar en el grupo")

        scrapper.temp_dict[user]["timeout"] = time.time() + scrapper.delay

        enviar_grupos()

        while time.time() < scrapper.temp_dict[user]["timeout"]:
            scrapper.temp_dict[user]["if_cancelar"]()
            time.sleep(5)

        
            
                  
                

def elegir_cuenta(scrapper: scrapping, user, bot: telebot.TeleBot , ver_actual=False, perfil_actual=False):


    scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'body')))
    scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div#screen-root')))
    
    
    try:
        #si ya el menú de cuentas está desplegado... hay que omitir cosas
        scrapper.temp_dict[user]["e"] = scrapper.wait_s.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="list"]')))

        scrapper.temp_dict[user]["e"] = True
        
    except: 
        scrapper.temp_dict[user]["e"] = False


    #el menu no está desplegado    
    if not scrapper.temp_dict[user]["e"]:  
        # scrapper.driver.get(scrapper.driver.current_url + "/bookmarks/")

        #este elemento es el de los ajustes del perfil (las 3 rayas de la derecha superior)
        scrapper.wait.until(ec.any_of(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, 'div[role="button"]')) > 3))

        scrapper.wait.until(ec.element_to_be_clickable(scrapper.find_element(By.CSS_SELECTOR, 'div[role="button"]')))
        #//*[contains(text(), "Your Pages and profiles")]/../../../..
        #//div[contains(@role,"button")][contains(@aria-label, "Switch Profile")]
        scrapper.temp_dict["url_actual"] = scrapper.driver.current_url
        
        if not scrapper.temp_dict[user]["e"]:
            for i in range(3):

                try:
                    scrapper.find_elements(By.CSS_SELECTOR, 'div[role="button"]')[2].click()
                    break
                except Exception as err:
                    if i >= 2:
                        raise err

                    else:
                        time.sleep(3)
                        pass
            # scrapper.find_elements(By.CSS_SELECTOR, 'div[data-tti-phase="-1"][role="button"][tabindex="0"][data-focusable="true"][data-mcomponent="MContainer"][data-type="container"]')[2].click()

            scrapper.wait_s.until(ec.url_changes(scrapper.temp_dict["url_actual"]))

            if not scrapper.driver.current_url.endswith("bookmarks/"):
                load(scrapper, "https://m.facebook.com/bookmarks/")

            # #Elemento de Configuracion de cuenta
            scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="list"]')))



            #Flecha para ver otros perfiles/cambiar
            
            scrapper.wait.until(ec.visibility_of_all_elements_located((By.CSS_SELECTOR, 'div[tabindex="0"][role="button"][data-focusable="true"][data-tti-phase="-1"][data-mcomponent="MContainer"][data-type="container"][class="m"]')))


            if len(scrapper.find_elements(By.CSS_SELECTOR, 'div[tabindex="0"][role="button"][data-focusable="true"][data-tti-phase="-1"][data-mcomponent="MContainer"][data-type="container"][class="m"]')) >= 4:

                
                scrapper.find_elements(By.CSS_SELECTOR, 'div[tabindex="0"][role="button"][data-focusable="true"][data-tti-phase="-1"][data-mcomponent="MContainer"][data-type="container"][class="m"]')[-1].click()



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

                scrapper.temp_dict[user]["perfil_actual"] = scrapper.temp_dict[user]["res"].text.split("\n")[0].strip()

                return ("ok", scrapper.temp_dict[user]["res"].text.split("\n")[0].strip(), "uno")


        
            

   
        

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
        scrapper.temp_dict[user]["perfil_actual"] = scrapper.temp_dict[user]["cuentas"][0].text.split("\n")[0]
        return ("ok", scrapper.temp_dict[user]["cuentas"][0].text.split("\n")[0], "uno")

    
    
    if not ver_actual:
        
        scrapper.temp_dict[user]["teclado"] = ReplyKeyboardMarkup(True, True, input_field_placeholder="Elige un perfil")
        scrapper.temp_dict[user]["perfiles"] = []
    
        for e,cuenta in enumerate(scrapper.temp_dict[user]["cuentas"], 1):     
            
            scrapper.temp_dict[user]["perfiles"].append(cuenta.text.split("\n")[0].strip())
            
            scrapper.temp_dict[user]["teclado"].add(cuenta.text.split("\n")[0].strip())               
            

        if perfil_actual:
            scrapper.temp_dict[user]["res"] = scrapper.temp_dict[user]["perfiles"].index(perfil_actual)

        else:
            handlers(bot, user, "Cual de los perfiles de esta cuenta quieres usar?", "perfil_elegir", scrapper.temp_dict, markup=scrapper.temp_dict[user]["teclado"])

        scrapper.temp_dict[user]["e"] = scrapper.temp_dict[user]["cuentas"][scrapper.temp_dict[user]["res"]]


        borrar_elemento(scrapper, 'div[role="presentation"]')
        
        for i in range(5):
            try:
                scrapper.wait_s.until(ec.element_to_be_clickable(scrapper.temp_dict[user]["e"]))
                # scrapper.temp_dict[user]["cuentas"][scrapper.temp_dict[user]["res"]].click()
                # scrapper.temp_dict[user]["e"].find_element(By.CSS_SELECTOR, "img").click()
                ActionChains(scrapper.driver).click(scrapper.temp_dict[user]["e"].find_element(By.CSS_SELECTOR, "img")).perform()
                break 
        
            except:
                if i >=4:
                    raise Exception("No puedo encontrar el elemento para cambiar de perfil")

                else:
                    scrapper.temp_dict[user]["e"] = scrapper.temp_dict[user]["e"].find_element(By.XPATH, '..')

        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "div#screen-root")))

        

        guardar_cookies(scrapper, user)
        
        scrapper.temp_dict[user]["perfil_actual"] = scrapper.temp_dict[user]["perfiles"][scrapper.temp_dict[user]["res"]]

        return ("ok", scrapper.temp_dict[user]["perfil_actual"])
        
    else:
        #para ver el perfil actual
        return ("ok", scrapper.temp_dict[user]["cuentas"][0].text.split("\n")[0])
            


                     


    

    
    
    
        
        
def main(scrapper: scrapping, bot: telebot.TeleBot, user):
    """
    This function will do all the scrapping requesting to other functions and makes for sure that all is ok
    
    bot: instance of telebot
    user : telegram's user_id
    """

    #limpiar el texto

    scrapper.driver.delete_all_cookies()
    
    scrapper.temp_dict[user]["texto_r"] = scrapper.temp_dict[user]["texto_p"].splitlines()[0][:60].strip()
    

    comprobar_BD(scrapper.collection)
    
    scrapper.temp_dict[user]["if_cancelar"] = lambda scrapper=scrapper, user=user, bot=bot: if_cancelar(scrapper, user, bot)

    if not scrapper.interrupcion and not scrapper.temp_dict[user].get("repetir"):
        scrapper.temp_dict[user]["info"] = bot.send_message(user, m_texto("Empezaré a procesar tu petición..."), reply_markup=telebot.types.ReplyKeyboardRemove())

    scrapper.temp_dict[user]["if_cancelar"]()

    print("Voy a hacer el loguin")
    scrapper.temp_dict[user]["res"] = loguin(scrapper, user, bot)        

    print("Empezaré a comprobar si hay algún error luego del loguin")

    
            
    try:
        #comprobando estar en el inicio de la mainpage de facebook
        scrapper.temp_dict[user]["e"] = scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div#screen-root')))

    except:
        scrapper.temp_dict[user]["e"] = None

        give_error(bot, scrapper.driver, user, "ID usuario: " + str(user) + "\nFaltó algo :(",)
    

    administrar_BD(scrapper, bot)

    scrapper.temp_dict[user]["if_cancelar"]()

    if scrapper.temp_dict[user].get("perfil_actual"):
        print("Voy a autenticarme con el perfil que estaba publicando antes de que me detuviera")
        scrapper.temp_dict[user]["res"] = elegir_cuenta(scrapper , user, bot, perfil_actual=scrapper.temp_dict[user]["perfil_actual"])
        print("Autenticación con éxito")

    else:
        print("Voy a ver el perfil actual")
        scrapper.temp_dict[user]["res"] = elegir_cuenta(scrapper , user, bot, ver_actual=True)


    if not scrapper.temp_dict[user].get("perfil_actual"):
    
        if not len(scrapper.temp_dict[user]["res"]) == 3:
        
            scrapper.temp_dict[user]["teclado"] = ReplyKeyboardMarkup(True, True, row_width=1, input_field_placeholder="¿Quieres cambiar a otro perfil?").add("Si", "No", row_width=2)
            
            scrapper.temp_dict[user]["perfil_actual"] = str(scrapper.temp_dict[user]["res"][1])

            handlers(bot, user, "El perfil actual es:\n\n=> <b>" + str(scrapper.temp_dict[user]["res"][1]) + "</b>\n\n¿Quieres cambiar de perfil?", "perfil_pregunta", scrapper.temp_dict, markup=scrapper.temp_dict[user]["teclado"])

            
            
            if scrapper.temp_dict[user]["res"].text.lower() == "si":
                print("Voy a cambiar de perfil")

                
                scrapper.temp_dict[user]["res"] = elegir_cuenta(scrapper, user, bot)
                if scrapper.temp_dict[user]["res"][0] == "error":


                    give_error(bot, scrapper.driver, user, "ID usuario: " + str(user) + "\n\nDescripción del error:\n" + str(scrapper.temp_dict[user]["res"][1]))

                else:
                    # scrapper.temp_dict[user]["info"] = bot.edit_message_text(text=f"🆕 Mensaje de Información\n\nHe cambiado al perfil de: {scrapper.temp_dict[user]["res"][1]}", chat_id=user, message_id=scrapper.temp_dict[user]["info"].message_id, reply_markup=telebot.types.ReplyKeyboardRemove())

                    scrapper.temp_dict[user]["perfil_actual"] = str(scrapper.temp_dict[user]["res"][1])
                    
                    bot.send_message(user, m_texto("He cambiado al perfil de:\n\n=> <b>" + str(scrapper.temp_dict[user]["res"][1]) + "</b>\n\nLoguin completado exitosamente!"), reply_markup=telebot.types.ReplyKeyboardRemove())

            else:
                # scrapper.temp_dict[user]["info"] = bot.edit_message_text(text=f"🆕 Mensaje de Información\n\nMuy bien, continuaré con el perfil actual", chat_id=user, message_id=scrapper.temp_dict[user]["info"].message_id, reply_markup=telebot.types.ReplyKeyboardRemove())

                bot.send_message(user, m_texto("Muy bien, continuaré con el perfil actual\n\nLoguin completado exitosamente!"), reply_markup=telebot.types.ReplyKeyboardRemove())
        else:
            bot.send_message(user, m_texto("Al parecer, solamente está el perfil de:\n\n=> <b>" + str(scrapper.temp_dict[user]["res"][1]) +"</b>\n\nContinuaré con ese..."))

        
    
        

    
            
    guardar_cookies(scrapper, user)
    administrar_BD(scrapper, bot) 


    scrapper.temp_dict[user]["if_cancelar"]()
    
    if not  scrapper.temp_dict[user].get("c_r"):
        scrapper.temp_dict[user]["c_r"] = 1 #esto indica la cantidad de veces que se ha hecho la publicación masiva de todos los grupos, es un contador



    #-----------------------------------PUBLICACIÓN----------------------------------------------
    if re.search(r"hora_reinicio", str(scrapper.temp_dict[user])):
        pass
    
    else:
        scrapper.temp_dict[user]["publicacion_res"] = publicacion(scrapper, bot , user)



    if not scrapper.temp_dict[user]["publicacion_res"][0] == "ok":
        

        scrapper.temp_dict[user]["publicacion"]["hora_reinicio"] = time.time() + scrapper.temp_dict[user]["repetir"]

        administrar_BD(scrapper, bot) 
                        
        while not time.time() >= scrapper.temp_dict[user]["publicacion"]["hora_reinicio"]:


            scrapper.temp_dict[user]["if_cancelar"]()
            time.sleep(1 * 60)

        
        del scrapper.temp_dict[user]["publicacion"]

        scrapper.temp_dict[user]["contador"] = 0

        scrapper.temp_dict[user]["c_r"] += 1

        scrapper.interrupcion = False

        return main(scrapper, bot, user)

    return scrapper.temp_dict[user]["publicacion_res"]