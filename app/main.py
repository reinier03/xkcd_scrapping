import requests
import shutil
import os
import telebot
from telebot.types import *
from telebot.handler_backends import ContinueHandling
import f_src
import sys
import dill
import re
from traceback import format_exc
import threading
from flask import Flask, request
import subprocess
import json
from f_src import facebook_scrapper
from tb_src.usefull_functions import *
from tb_src.usefull_functions import m_texto
from tb_src.main_classes import scrapping as scrapping
from tb_src.main_classes import *
from telebot.types import *
from tb_src import callbacks, panel_usuario, panel_admin




"""
-------------------------------------------------------
Variables de Entorno a Definir:
-------------------------------------------------------
token = token del bot
admin = ID del administrador del bot
MONGO_URL = Enlace del cluster de MongoDB (Atlas)
webhook_url = Si esta variable es definida se usará el metodo webhook, sino pues se usara el método polling

Para dudas o sugerencias contactarme a https://t.me/mistakedelalaif
"""

telebot.apihelper.ENABLE_MIDDLEWARE = True
bot = TelegramBot(os.environ["token"], parse_mode="html", disable_web_page_preview=True)

#----------------------------Configurando la info del bot---------------------------------
bot.set_my_description("""
¿Estás cansado de que para promocionarte en Facebook tienes que pasar horas publicando en los grupos y haciendo scroll?
¡Llegué para tí!
Conmigo solo tienes que enviarme el enlace de la publicación que quieres que todos vean y me encargaré de publicarlo en TODOS tus grupos. 

Si tienes dudas o preguntas contacta con @{} (mi creador)""".format(bot.get_chat(1413725506).username).strip())

bot.set_my_short_description("Comparto una publicación automáticamente por todos tus grupos Facebook. Útil para promocionar tus productos")
#----------------------------Configurando la info del bot---------------------------------


#------------------declaring main class--------------------------
scrapper = scrapping(bot)
#--------------------------END------------------------------


# media_group_clases = {}
# usuarios = {}
## usuarios = {id_usuario_telegram : main_classes.Usuario()}


bot.set_my_commands([
    BotCommand("/help", "Información sobre el bot"),
    BotCommand("/lista_planes", "Para ver TODOS los planes disponibles"),
    BotCommand("/publicaciones", "administra tus publicaciones"),
    BotCommand("/publicar", "Comienza a publicar"),
    BotCommand("/cancelar", "Cancela el proceso actual"),
    BotCommand("/panel", "Administrar tus publicaciones")


], BotCommandScopeAllPrivateChats())


if scrapper.admin:
    admin = int(os.environ["admin"])
    scrapper.admin_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Contacta con el Administrador 👮‍♂️", "https://t.me/{}?text=Hola+quisiera+poder+publicar+en+Facebook+con+un+bot".format(scrapper.bot.get_chat(scrapper.admin).username, scrapper.bot.user.username))
        ]])
    
    bot.set_my_commands([
        BotCommand("/help", "Información sobre el bot"),
        BotCommand("/lista_planes", "Para ver TODOS los planes disponibles"),
        BotCommand("/publicaciones", "administra tus publicaciones"),
        BotCommand("/publicar", "Comienza a publicar"),
        BotCommand("/cancelar", "Cancela el proceso actual"),
        BotCommand("/panel", "Panel de ajustes")], 
        BotCommandScopeChat(admin))

    bot.set_my_commands([
        BotCommand("/help", "Información sobre el bot"),
        BotCommand("/lista_planes", "Para ver TODOS los planes disponibles"),
        BotCommand("/publicaciones", "administra tus publicaciones"),
        BotCommand("/publicar", "Comienza a publicar"),
        BotCommand("/cancelar", "Cancela el proceso actual"),
        BotCommand("/panel", "Panel de ajustes")], 
        BotCommandScopeChat(scrapper.creador))

#por si corre en render
if os.environ.get("RENDER_EXTERNAL_URL"):
    os.environ["webhook_url"] = os.environ["RENDER_EXTERNAL_URL"]


for k,v in os.environ.items():
    if k in ["admin", "token", "MONGO_URL", "webhook_url"]:
        if k == "admin" and not scrapper.entrada.obtener_usuario(int(v)):
            scrapper.entrada.append(Usuario(int(v), Ilimitado(), False))

        scrapper.env.update({k: v})


#para evitar repeticion


@bot.middleware_handler()
def cmd_middleware(bot: telebot.TeleBot, update: telebot.types.Update):
    global scrapper

    # if update.message:
    #     scrapper.entrada.get_caducidad(update.message.from_user.id, scrapper)

    # elif update.callback_query.message:
    #     scrapper.entrada.get_caducidad(update.callback_query.message.from_user.id, scrapper

    


    return



@bot.message_handler(func=lambda message: not message.chat.type == "private")
def not_private(m):
    return

#en caso de que no tenga las variables de entorno principales:
@bot.message_handler(func=lambda m : not scrapper.admin or not os.environ.get("admin") or not scrapper.MONGO_URL)
def comprobar_venvs(m):
    comprobacion_env(m, scrapper)
    return


@bot.message_handler(func=lambda m, scrapper=scrapper: m.forward_from_chat or m.text.isdigit())
def obtener_info(m: telebot.types.Message):
    if m.forward_from_chat:
        mostrar_info_usuario(m.chat.id, m.forward_from_chat.id)
    elif bot.get_chat(int(m.text)):
        mostrar_info_usuario(m.chat.id, int(m.text))

    return


@bot.message_handler(func=lambda m, scrapper=scrapper: m.from_user.id in scrapper.entrada.obtener_usuarios_baneados())
def cmd_usuario_baneado(m):
    if m.from_user.id != scrapper.admin:
        bot.send_message(m.chat.id, m_texto("Actualmente estás <b>baneado</b> (osea, bloqueado de mis servicios)\n\nSi quieres usar mis servicios y crees que esto es injusto, habla con mi administrador 👇"), reply_markup=scrapper.admin_markup)

    else:
        bot.send_message(m.chat.id, m_texto("Actualmente estás <b>baneado</b> (osea, bloqueado de mis servicios)\n\nSi quieres usar mis servicios y crees que esto es injusto, habla con mi creador 👇"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Contactar con mi creador 👨‍💻", "https://t.me/{}".format(bot.get_chat(scrapper.creador).username))]]))


@bot.message_handler(commands=["start", "help"])
@bot.message_handler(func=lambda m: m.from_user.id in [admin, scrapper.creador] and m.text.strip() == "/admin")
def start(m):
    global scrapper
    
    if m.text.strip() == "/admin" and m.from_user.id in [scrapper.admin, scrapper.creador]:
        panel_admin.help_admin(m, bot)

    elif m.from_user.id == admin:
        bot.send_message(m.chat.id, "¿Quieres ver la ayuda para administradores o la ayuda para usuarios?", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Ayuda para administradores", callback_data="help/admin")],
            [InlineKeyboardButton("Ayuda para usuarios", callback_data="help/users")]
            ]))

        bot.register_callback_query_handler(panel_admin.help_admin, lambda c: c.data == "help/admin", True)
        bot.register_callback_query_handler(panel_usuario.help_usuario, lambda c: c.data == "help/users", True)

    elif not scrapper.entrada.get_caducidad(m.from_user.id, scrapper) == True:
        panel_usuario.help_usuario(m)
        
        
    else:
         bot.send_message(m.chat.id,                      
"""
Hola {} ! :D

¿Te parece tedioso estar re publicando por TODOS tus grupos en Facebook?
No te preocupes, yo me encargo por ti ;)

<u><b>Lista de Comandos</b></u>:
<b>/help</b> - Para ver la ayuda que muestro ahora mismo

<b>/lista_planes</b> - Para ver TODOS los planes disponibles

<b>/sobre_mi</b> - Información sobre el bot y su creador

Al parecer no tienes ningún <b>Plan</b> o ya <b>venció</b> el que habías contratado, por favor acceda a más información sobre nuestros planes escribiendo lo siguiente: <b>/lista_planes</b>
""".format(m.from_user.first_name))

    return


@bot.message_handler(["planes", "lista_planes"])
def cmd_lista_planes(m):
    for i in Planes_para_comprar().show(True):
        bot.send_message(m.chat.id, i)

    
    if scrapper.entrada.get_caducidad(m.from_user.id, scrapper , True):
        bot.send_message(m.chat.id, "👇 Escríbale al Administrador para adquirir algún plan 👇", reply_markup=scrapper.admin_markup)

    return


@bot.message_handler(commannd=["sobre_mi"])
def cmd_sobre_mi(m):
    bot.send_message(m.chat.id, """Este bot lo administra: 
{}
👆 Si tienes alguna queja o problema contáctalo/a

Bot desarrollado por:
@{} 
👆 si quieres más bots así contáctalo ;D
""".format("@" + bot.get_chat(scrapper.admin).username if bot.get_chat(scrapper.admin).username else "<b>[username no disponible]</b>", bot.get_chat(scrapper.creador).username).strip())

    return


def cu_handler(m):

    if not m.from_user.id in scrapper.entrada.obtener_usuarios():
        return True

    if scrapper.entrada.get_caducidad(m.from_user.id, scrapper) == True:
        return True
    
    elif scrapper.entrada.obtener_usuario(m.from_user.id):
        return scrapper.entrada.obtener_usuario(m.from_user.id).plan.plan == False


    else:
        return (m.from_user.id != scrapper.cola["uso"] and not m.from_user.id in scrapper.entrada.obtener_usuarios()) 

#este es el handler administrador de entrada
@bot.message_handler(func=cu_handler)
@bot.message_handler(func=lambda m: m.from_user.id in scrapper.usuarios_baneados and not m.from_user.id == scrapper.creador)
def cmd_bloqueado(m):
    global scrapper
    

    if m.from_user.id in [scrapper.admin, scrapper.creador]:
        return ContinueHandling()

    if m.from_user.id in scrapper.usuarios_baneados:
        bot.send_message(m.chat.id, m_texto("Actualmente estás BANEADO de mis servicios. No puedes usarme hasta que el administrador lo decida (algo habrás hecho)\n\n👇 Contacta con el administrador para rebatir tu caso 👇"), reply_markup=scrapper.admin_markup)

    elif not scrapper.entrada.obtener_usuarios():
        bot.send_message(m.chat.id, m_texto("No tienes contratado ninguno de mis servicios, habla con mi administrador para poder usarme\n👇Contáctalo👇"), reply_markup=scrapper.admin_markup)
        return

    elif not m.from_user.id in scrapper.entrada.obtener_usuarios():
        bot.send_message(m.chat.id, m_texto("No tienes contratado ninguno de mis servicios, habla con mi administrador para poder usarme\n👇Contáctalo👇"), reply_markup=scrapper.admin_markup)

        return
    
    elif scrapper.entrada.obtener_usuario(m.from_user.id).plan.plan == False:
        bot.send_message(m.chat.id, "TU servicio de publicación ya expiró, adquiere un nuevo servicio con mi administrador", reply_markup=scrapper.admin_markup)

    else:
        bot.send_message(m.chat.id, m_texto("Lo siento tigre, por ahora mi acceso está restringido hasta que el administrador lo decida\n👇Si tienes alguna queja contáctalo👇"), reply_markup=scrapper.admin_markup)

    return 


@bot.message_handler(commands=["cancelar"])
def cmd_cancelar(m):
    global scrapper
    m.text = m.text.strip()

    if len(m.text.split()) > 1 and m.from_user.id in [admin, scrapper.creador] and m.text.split()[1].isdigit():
        if scrapper.cola["uso"] == int(m.text.split()[1]):
            if bot.get_chat(int(m.text.split()[1])):
                bot.send_message(m.chat.id, m_texto("Muy Bien, Cancelaré la operación actual para ese usuario"),  reply_markup=telebot.types.ReplyKeyboardRemove())

                scrapper.temp_dict[int(m.text.split()[1])]["cancelar_forzoso"] = True

                liberar_cola(scrapper, scrapper.cola["uso"], bot)

                # if not scrapper.temp_dict[scrapper.cola["uso"]].get("texto_r"):
                #     liberar_cola(scrapper, scrapper.cola["uso"], bot)
                
                
            else:
                bot.send_message(m.from_user.id, m_texto("¡El usuario que ingresaste no existe!\n\nOperación Cancelada"))
        
        else:
            bot.send_message(m.chat.id, m_texto("Este usuario no está usando las publicaciones"), reply_markup=telebot.types.ReplyKeyboardRemove())

    elif scrapper.cola["uso"] == m.from_user.id:

        scrapper.temp_dict[m.from_user.id]["cancelar"] = True

        # if not scrapper.temp_dict[scrapper.cola["uso"]].get("texto_r"):
        #     liberar_cola(scrapper, scrapper.cola["uso"], bot)

        liberar_cola(scrapper, m.from_user.id, bot)
        

    else:
        bot.send_message(m.from_user.id, m_texto("¡No tienes ningún proceso activo!"), reply_markup=telebot.types.ReplyKeyboardRemove())

    return

@bot.message_handler(["publicaciones"])
def cmd_administrar_publicaciones(m):
    bot.delete_message(m.chat.id, m.message_id)
    panel_usuario.opciones_publicaciones(m.from_user.id, scrapper)
    
# @bot.message_handler(commands=["cambiar"], func=lambda m: m.from_user.id != scrapper.cola["uso"])
# def cmd_delete(m):
#     global scrapper

#     if not scrapper.collection.find_one({"telegram_id": m.from_user.id}) and not user_folder(m.from_user.id, True):
#         bot.send_message(m.chat.id, m_texto("Ni siquiera me has usado aún!\n\nNo tengo datos tuyos los cuales restablecer\nEnviame /info para comenzar a usarme :D"))
#         return


    
#     msg = bot.send_message(m.chat.id, m_texto("La opción actual borrará la información que tengo de tu cuenta y tendrías que volver a ingresar todo desde cero nuevamente...\n\nEstás seguro que deseas hacerlo?", True), reply_markup=ReplyKeyboardMarkup(True, True).add("Si", "No"))
    

#     bot.register_next_step_handler(msg, borrar_question)


def borrar_question(m):
    global scrapper

    if m.text.lower() == "si": 
        
        
        try:
            scrapper.collection.delete_one({"telegram_id": m.from_user.id})
        except:
            pass
        try:
            shutil.rmtree(user_folder(m.from_user.id))
        except:
            pass
        

        bot.send_message(m.chat.id, m_texto("Ya se ha borrado todo exitosamente :-("), reply_markup=ReplyKeyboardRemove())

    else:
        bot.send_message(m.chat.id, m_texto("Operación Cancelada con éxito :D"), reply_markup=ReplyKeyboardRemove())

    return


# @bot.message_handler(commands=["cookies"])
# def cmd_cookies(m):
#     global scrapper
#     if m.from_user.id != scrapper.cola["uso"]:
#         markup = InlineKeyboardMarkup(
#                 [
#                     [InlineKeyboardButton("Recibirlas", callback_data="cookies/recibir")], 
#                     [InlineKeyboardButton("Cargarlas", callback_data="cookies/cargar")]
#                 ]
#             )
#     else:
#         markup = InlineKeyboardMarkup(
#                 [
#                     [InlineKeyboardButton("Recibirlas", callback_data="cookies/recibir")]
#                 ]
#             )
            
#     bot.send_message(m.chat.id, "A continuación, aclárame algo... Quieres <b>RECIBIR</b> tus cookies o quieres darme alguna que ya hayas recibido y <b>CARGARLAS</b>?", reply_markup=markup)
    
    
#     bot.register_callback_query_handler(callbacks.cargar_cookies, lambda c: c.data == "cookies/cargar", True)
#     bot.register_callback_query_handler(callbacks.recibir_cookies, lambda c: c.data == "cookies/recibir", True)

#     return


            


@bot.message_handler(commands=["info"])
def cmd_publish(m):
    global scrapper

    
    bot.send_message(m.chat.id,
"""
Si eres nuevo por aquí sigue estos pasos para compartir una publicación en Facebook:
(Toca sobre el recuadro para desplegar el mensaje completo)

<blockquote expandable>
1 - Si no tienes ninguna, crea una nueva publicación con el comando /publicaciones y sigue las instrucciones

2 - Enviame /publicar y selecciona el perfil donde quieres que se publique, los grupos en los que se publicará será de ese perfil, si es tu primera vez aquí pues no tendrás ninguno asi que tendras que ingresar las credenciales de la cuenta de facebook con la que puedes ingresar

3 - Seguidamente selecciona la publicación o las publicaciones que quieres compartir

4 - Introduce tu usuario y luego la contraseña de facebook. Luego facebook escoge una alternativa para verificar tu cuenta: o te envia un codigo al WhatsApp del numero asociado a ese Facebook o envia el codigo a el correo asociado a esa cuenta, de todas maneras, el bot se encargará de dejarte en claro cual de los codigos debes de ingresar

5 - A continuación, si la cuenta con la que te logueaste tiene varios perfiles entonces deberás seleccionar con cual de todos tus perfiles publicarás

6 - Disfrutar de tu día mientras yo me encargo de publicar :D</blockquote>

{}

""".format("<blockquote>Te quedan " + scrapper.entrada.get_caducidad(m.from_user.id, scrapper) + " para que expire el plan que contrataste</blockquote>" if not m.from_user.id in [admin, scrapper.creador] else "").strip())
    return
    


def notificar(c):
    global scrapper

    bot.delete_message(c.message.chat.id, c.message.message_id)

    if c.data == "notify/si":
        if c.from_user.id in scrapper.cola["cola_usuarios"]:
            bot.send_message(c.from_user.id, "¡Ya estás entre los ususarios que voy a notificar!")
        else:
            scrapper.cola["cola_usuarios"].append(c.from_user.id)
            bot.send_message(c.from_user.id, m_texto("Muy bien, <b>te notificaré</b> cuando esté desocupado y puedas publicar...\n\nSi alguien más comienza a publicar antes que tú perderás la oportunidad y tendrás que volver a esperar, en resumen, ponte atento a este chat"))
    else:
        if c.from_user.id in scrapper.cola["cola_usuarios"]:
            scrapper.cola["cola_usuarios"].remove(c.from_user.id)

        bot.send_message(c.from_user.id, "Muy bien, <b>NO te notificaré</b> entonces")

    return


def call_notificar(c):
    global scrapper

    bot.delete_message(c.message.chat.id, c.message.message_id)
    
    scrapper.cola["cola_usuarios"].remove(c.from_user.id)
    bot.send_message(c.message.chat.id, "Muy bien, te dejaré de notificar")

    return




#--------------------OJO : Las siguientes lineas son para el futuro, si funciona-----------

# @bot.message_handler(commands=["crear"])
# def cmd_crear(m):
#     usuarios[m.from_user.id] = Usuario(m.from_user.id)

#     m = bot.send_message(m.chat.id, "Aquí podrás crear la publicación que quieres que se comparta en Facebook (en principio, será solo 1)\n\nA continuación de este mensaje, enviame el texto de la publicación o presiona en 'Sin texto' para no poner texto", reply_markup=ReplyKeyboardMarkup(True, True).add("Sin texto"))

#     bot.register_next_step_handler(m, crear_texto)

#     return


# def crear_texto(m: telebot.types.Message):
#     if not m.content_type == "text":
#         m = bot.send_message(m.chat.id, "No me envíes otra cosa que no sea el texto de la Publicación!\nVuelve a intentarlo\n\nnA continuación de este mensaje, enviame el texto de la publicación o presiona en 'Sin texto' para no poner texto", reply_markup=ReplyKeyboardMarkup(True, True).add("Sin texto", "Cancelar Operación"))

#         bot.register_next_step_handler(m, crear_texto)

#     elif m.text.lower() == "cancelar operación":
#         bot.send_message(m.chat.id, "Operación Cancelada", reply_markup=telebot.types.ReplyKeyboardRemove())

#     elif m.text.lower() == "sin texto":
#         m = bot.send_message(m.chat.id, "¡Muy bien, tu publicación no tendrá texto entonces!\n\nA continuación de este mensaje, enviame las FOTOS que quieres que tenga dicha publicación", reply_markup=telebot.types.ReplyKeyboardRemove())
    
#     else:
        

#         usuarios[m.from_user.id].publicaciones.append(Publicacion(usuarios[m.from_user.id].id))
#         usuarios[m.from_user.id].publicaciones[-1].texto = m.text

#         media_group_clases[m.from_user.id] = (MediaGroupCollector(usuarios[m.from_user.id].id, m.from_user.id))

#         bot.send_message(m.chat.id, "A continuación envía las fotos (o la foto) de la publicación que quieres compartir", reply_markup=telebot.types.ReplyKeyboardRemove())

#         return



# @bot.message_handler(content_types=["photo"])
# def photo_handler(m: telebot.types.Message):
#     if m.media_group_id and media_group_clases.get(m.from_user.id):
#         with media_group_clases.get(m.from_user.id) as user_media:
#             print("recibí una foto de: {}".format(user_media.telegram_id))
            
#             if user_media.timer:
#                 user_media.timer.close()

#             user_media.adjuntos.append(bot.get_file(m.photo[-1].file_id).file_path)
            
#             user_media.timer = threading.Timer(user_media.TIMEOUT, get_photos, (media_group_clases, user_media))
#             user_media.timer.start()
            
#     else:
#         return
    

# def get_photos(media_group_clases: dict, user_media: MediaGroupCollector):

#     if not os.path.isdir(os.path.join(user_folder(user_media.telegram_id), "publicaciones")):
#         os.mkdir(os.path.join(user_folder(user_media.telegram_id), "publicaciones"))

#     for foto in user_media.adjuntos:
#         with open(os.path.join(user_folder(user_media.telegram_id), "publicaciones" , "u-{}_i-{}.jpg").format(user_media.user_id, len(usuarios[user_media.telegram_id].publicaciones)), "wb") as foto:
            
#             foto.write(bot.download_file(foto))

#             usuarios[user_media.telegram_id].publicaciones[-1].adjuntos.append(os.path.join(user_folder(user_media.td:elegram_id), "publicaciones" , "u-{}_i-{}.jpg").format(user_media.user_id, len(usuarios[user_media.telegram_id].publicaciones)))

#             usuarios[user_media.telegram_id].publicaciones[-1].id_publicacion = len(usuarios[user_media.telegram_id].publicaciones)


#     del media_group_clases[user_media.telegram_id]

#     return

            
#--------------------------------------------------------------------------------------

@bot.message_handler(commands=["publicar"])
def get_work(m: telebot.types.Message):
    global scrapper

    if m.from_user.id == int(scrapper.admin) and int(scrapper.admin) != scrapper.creador:
        bot.send_message(m.chat.id, "Los administradores no pueden publicar, solamente los usuarios que han pagado por el servicio o mi creador\n\nOperación Cancelada")
        return

    if m.from_user.id == scrapper.cola["uso"]:
        bot.send_message(m.chat.id, m_texto("¡No puedes tener más de una publicación activa!\n\nEscribe /cancelar para cancelar el proceso"))
        return
    
    elif scrapper.cola["uso"]:

        if not m.from_user.id in scrapper.cola["cola_usuarios"] and not m.from_user.id == scrapper.cola["uso"]:

            bot.send_message(m.chat.id, "Al parecer alguien ya me está usando :(\nLo siento pero por ahora estoy ocupado\n\n<b>¿Quieres que te notifique cuando dejen de usarme?</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Si", callback_data="notify/si"), InlineKeyboardButton("No", callback_data="notify/no")]]))  

            bot.register_callback_query_handler(notificar, lambda c: c.data in ["notify/si", "notify/no"])
            return
        
        elif m.from_user.id in scrapper.cola["cola_usuarios"]:
            bot.send_message(m.chat.id, "¡Ya te dije que te iba a notificar cuando estuviera desocupado!")

            return



    
    elif not scrapper.cola["uso"]:    

        
        if scrapper.entrada.obtener_usuario(m.from_user.id):
            scrapper.cargar_datos_usuario(m.from_user.id)

            if not scrapper.entrada.obtener_usuario(m.from_user.id).publicaciones and not scrapper.collection.find_one({"tipo": "usuario", "telegram_id": m.from_user.id}) and not user_folder(m.from_user.id, True):

                bot.send_message(m.chat.id, "¡Ni siquiera tienes publicaciones agregadas para comenzar a compartirlas en Facebook!\n\n👇 Por favor, agrega una 👇", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Agregar Publicación", callback_data="p/add")]]))

                liberar_cola(scrapper, m.from_user.id, bot)

                return
            
            elif not scrapper.entrada.obtener_usuario(m.from_user.id).publicaciones and (scrapper.collection.find_one({"tipo": "usuario", "telegram_id": m.from_user.id}) or user_folder(m.from_user.id, True)):
                scrapper.administrar_BD(True, m.from_user.id)

                if not scrapper.entrada.obtener_usuario(m.from_user.id).publicaciones:

                    bot.send_message(m.chat.id, "¡Ni siquiera tienes publicaciones agregadas para comenzar a compartirlas en Facebook!\n\n👇 Por favor, agrega una 👇", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Agregar Publicación", callback_data="p/add")]]))

                    return
                    

        m.text = m.text.strip()
        scrapper.cola["uso"] = m.from_user.id
        scrapper.temp_dict[m.from_user.id] = {}
        scrapper.temp_dict[m.from_user.id]["obj_publicacion"] = []   

        #si el texto es "/publicar 3" 
        if len(m.text.split()) > 1:
            if re.search(r"\d+", m.text):
                scrapper.temp_dict[m.from_user.id]["contador"] = int(re.search(r"\d+", m.text).group()) -1 if not int(re.search(r"\d+", m.text).group()) < 0 else 0

            if "-t" in m.text:
                scrapper.temp_dict[m.from_user.id]["mostrar_tiempo_debug"] = True

            else:
                scrapper.temp_dict[m.from_user.id]["mostrar_tiempo_debug"] = False

        
        #cambiar
        
        if m.from_user.id in scrapper.cola["cola_usuarios"]:
            scrapper.cola["cola_usuarios"].remove(m.from_user.id)
        
        for i in scrapper.cola["cola_usuarios"]:
            try:
                bot.send_message(i, m_texto("Olvídalo :/\nYa me están usando nuevamente\n\n<b>Te volveré a avisar cuando esté desocupado</b>, pero debes de estar atento"), reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("No notificar más", callback_data="no_mas")]
                    ]
                ))

                bot.register_callback_query_handler(call_notificar, lambda call: call.data == "no_mas" and call.from_user.id == i)  

            except:
                pass

        

        if scrapper.entrada.obtener_usuario(m.from_user.id).cuentas:
            bot.send_message(m.chat.id, "<u><b>Opciones disponibles</b></u>:\nDale a '<b>Elegir Perfil</b>' para elegir entre algunos de los que has introducido aquí para comenzar a publicar\n\nDale a '<b>Acceder con un perfil nuevo</b>' para acceder con una cuenta que no has puesto aquí anteriormente\n\nDale a '<b>Cancelar</b>' para cancelar la operación de publicación", reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🔳 Elegir perfil", callback_data="p/c/e/w/0")], 
                    [InlineKeyboardButton("🆕 Acceder con un perfil nuevo", callback_data="p/c/n")],
                    [InlineKeyboardButton("❌ Cancelar Operación", callback_data="cancel")]
                ]))

        else:
            callbacks.mensaje_elegir_publicacion(m.from_user.id, scrapper)

            
    return




@bot.message_handler(commands=["panel"])
def cmd_panel(m: telebot.types.Message):

    bot.delete_message(m.chat.id, m.message_id)

    if not m.from_user.id == int(admin) and not m.from_user.id == int(scrapper.creador):
        bot.send_message(m.chat.id, "Bienvenido al panel de control <b>{}</b> que deseas hacer? :D\n\nEn este panel podrás administrar lo que puedes hacer con tu plan {}".format(bot.get_chat(m.from_user.id).first_name , scrapper.entrada.obtener_usuario(m.from_user.id).plan.__class__.__name__), reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("👀 Ver / Administrar Publicaciones", callback_data="c/p")],
                [InlineKeyboardButton("🔁 Cambiar tiempo repetición", callback_data="c/d")],
                [InlineKeyboardButton("📨 Información útil", callback_data="c/w")],
            ]))
    

    elif m.from_user.id == scrapper.creador:
        bot.send_message(m.chat.id, 
            "Bienvenido al panel de control <b>{}</b> que deseas hacer? :D\n\nEstás accediendo a este panel como administrador".format(m.from_user.first_name), 
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⌛ Cambiar la espera entre CADA grupo", callback_data="c/a/d")],
                # [InlineKeyboardButton("⛔ Administrar Entrada", callback_data="c/a/pass")],
                [InlineKeyboardButton("👀 Ver / Administrar Publicaciones", callback_data="c/p")],
                [InlineKeyboardButton("🔁 Cambiar tiempo repetición", callback_data="c/d")],
                [InlineKeyboardButton("🛃 Ver información", callback_data="c/a/w")],
                # [InlineKeyboardButton("♻ Reiniciar Bot", callback_data="c/a/reload")]
                # [InlineKeyboardButton("👥 Administrar Usuarios", callback_data="c/u")]
            ]))

    elif m.from_user.id == int(admin):
        bot.send_message(m.chat.id, 
            "Bienvenido al panel de control <b>{}</b> que deseas hacer? :D\n\nEstás accediendo a este panel como administrador".format(m.from_user.first_name), 
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⌛ Cambiar la espera entre CADA grupo", callback_data="c/a/d")],
                # [InlineKeyboardButton("⛔ Administrar Entrada", callback_data="c/a/pass")],
                [InlineKeyboardButton("👀 Ver / Administrar Publicaciones", callback_data="c/p")],
                [InlineKeyboardButton("🔁 Cambiar tiempo repetición", callback_data="c/d")],
                [InlineKeyboardButton("🛃 Ver información", callback_data="c/a/w")],
                # [InlineKeyboardButton("♻ Reiniciar Bot", callback_data="c/a/reload")]
                # [InlineKeyboardButton("👥 Administrar Usuarios", callback_data="c/u")]
            ]))

    return


@bot.callback_query_handler(lambda c: c.data.startswith("publicar/"))
def cual_publicar(c):
    if (not re.search("elegir", c.data) and not re.search(r"\d+", c.data)) or c.data == "publicar/elegir/publicar" or "/b" in c.data:
        try:
            bot.delete_message(c.message.chat.id, c.message.message_id)

        except:
            pass

    if c.data == "publicar/seleccionar":
        ver_lista_publicaciones(c, scrapper, bot, elegir=True)

    elif c.data == "publicar/all":
        scrapper.temp_dict[c.from_user.id]["obj_publicacion"] = [i for i in scrapper.entrada.obtener_usuario(c.from_user.id).publicaciones]

        threading.Thread(name="Hilo usuario: {}".format(c.from_user.id), target=scrapper.start_publish, args=(c.from_user.id,)).start()

    elif c.data.startswith("publicar/elegir"):
        if c.data == "publicar/elegir/publicar":

            threading.Thread(name="Hilo usuario: {}".format(c.from_user.id), target=scrapper.start_publish, args=(c.from_user.id,)).start()
         
        elif c.data == "publicar/elegir/b":
            callbacks.mensaje_elegir_publicacion(c.from_user.id, scrapper)

        else:

            if not scrapper.temp_dict[c.from_user.id].get("obj_publicacion"):
                scrapper.temp_dict[c.from_user.id]["obj_publicacion"] = [scrapper.entrada.obtener_usuario(c.from_user.id).publicaciones[int(re.search(r"\d+", c.data).group())]]

            else:
                #verificar si está seleccionada o no
                if scrapper.entrada.obtener_usuario(c.from_user.id).publicaciones[int(re.search(r"\d+", c.data).group())] in scrapper.temp_dict[c.from_user.id]["obj_publicacion"]:
                    scrapper.temp_dict[c.from_user.id]["obj_publicacion"].remove(scrapper.entrada.obtener_usuario(c.from_user.id).publicaciones[int(re.search(r"\d+", c.data).group())])

                else:
                    scrapper.temp_dict[c.from_user.id]["obj_publicacion"].append(scrapper.entrada.obtener_usuario(c.from_user.id).publicaciones[int(re.search(r"\d+", c.data).group())])


            ver_lista_publicaciones(c, scrapper, bot, elegir=True)


    return

@bot.callback_query_handler(lambda c: (c.data.startswith("c/") or c.data.startswith("p/")) or re.search(r"/a/\d+", c.data))
def cmd_panel_usuario(c):
    if (not "p/wl" in c.data and not "p/del" in c.data) or c.data.startswith("p/wl/a/") or c.data.startswith("p/u") or c.data.endswith("/b"):
        
        bot.delete_message(c.from_user.id, c.message.message_id)


    if c.data in ["c/a/w/user", "c/a/w/main_vars", "c/a/w/vars"]:
        panel_admin.watch(c, scrapper)

    elif c.data == "c/a/w":
        panel_admin.call_ver(c, scrapper)

    elif c.data in ["c/a/pass/r", "c/a/pass/cancel", "c/a/pass/pass"]:
        panel_admin.modificar_entrada(c, scrapper)

    elif c.data == "c/a/pass":
        panel_admin.entrada(c, scrapper)

    elif c.data == "c/a/d":
        panel_admin.cambiar_delay(c, scrapper)

    #para el delay entre cada publicacion masiva
    elif "c/d" == c.data:
        if scrapper.entrada.obtener_usuario(c.from_user.id).plan.repetir or c.from_user.id in [scrapper.admin, scrapper.creador]:
            panel_usuario.definir_repiticion(c, scrapper)

        else:
            bot.send_message(c.message.chat.id, m_texto("ERROR Lo siento tigre, tu plan {} no permite repeticiones automaticas\n\n👇 Contacta con el administrador para obtener uno que sí lo permita 👇"), reply_markup=scrapper.admin_markup)

    #esto muestra el panel para agregar o ver publicaciones
    elif "c/p" == c.data:
        panel_usuario.opciones_publicaciones(c.from_user.id, scrapper)

    elif "c/w" == c.data:
        TEXTO = """
<b>Nombre de usuario</b>: {}

<b>Alias de usuario</b>: {}

<b>ID del usuario</b> : <code>{}</code>

<b>Total de Publicaciones creadas</b>: {}

<b><u>Plan Actual</u></b>:
<blockquote>{}</blockquote>

<b><u>Tiempo para que caduque el Plan</u></b>:
<blockquote>{}</blockquote>
""".format(bot.get_chat(c.from_user.id).first_name, "@" + bot.get_chat(c.from_user.id).username if bot.get_chat(c.from_user.id).username else "¡No tienes!", c.from_user.id ,len(scrapper.entrada.obtener_usuario(c.from_user.id).publicaciones), scrapper.entrada.obtener_usuario(c.from_user.id).plan.show(), scrapper.entrada.get_caducidad(c.from_user.id, scrapper)).strip()

        if bot.get_chat(c.message.chat.id).photo:
            with open(os.path.join(user_folder(c.from_user.id), "foto_perfil.jpg"), "wb") as file:
                file.write(bot.download_file(bot.get_file(bot.get_chat(c.message.chat.id).photo.big_file_id).file_path))

            bot.send_document(c.message.chat.id, InputFile(os.path.join(user_folder(c.from_user.id), "foto_perfil.jpg"), str(c.from_user.id) + ".jpg") , caption= TEXTO)

            os.remove(os.path.join(user_folder(c.from_user.id), "foto_perfil.jpg"))

        else:
            bot.send_message(c.message.chat.id, TEXTO)
            

    elif c.data.startswith("p/add") or c.data.startswith("p/w") or c.data.startswith("p/"):

        
        if c.data.startswith("p/c/e"):
            callbacks.elegir_cuenta_publicar(c, scrapper)

        elif c.data == "p/c/n":

            callbacks.mensaje_elegir_publicacion(c.from_user.id, scrapper)

            return
        

        if "p/add" in c.data and len(scrapper.entrada.obtener_usuario(c.from_user.id).publicaciones) >= scrapper.entrada.obtener_usuario(c.from_user.id).plan.publicaciones and not scrapper.entrada.obtener_usuario(c.from_user.id).plan.publicaciones == True:

            bot.send_message(c.from_user.id, "¡Ya has llegado al límite de publicaciones que puedes llegar con tu plan {}! (Máximo de publicaciones: {})\n\nDebes <b>Eliminar alguna que ya tengas</b> o Contactar con el administrador para <b>contratar un plan más avanzado</b> que te permita más".format(scrapper.entrada.obtener_usuario(c.from_user.id).plan.__class__.__name__ , scrapper.entrada.obtener_usuario(c.from_user.id).plan.publicaciones), reply_markup=scrapper.admin_markup)

            return

        if c.data == "p/wl" and len(scrapper.entrada.obtener_usuario(c.from_user.id).publicaciones) == 0:
            bot.edit_message_text("Lo siento pero ni siquiera tienes ninguna publicación creada :(\n\n👇 Agrega alguna 👇", c.message.chat.id, c.message.message_id, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Agregar Publicación", callback_data="p/add")]]))

            return
        
        callbacks.manage_publicaciones(c, scrapper, bot)

    

@bot.callback_query_handler(lambda c: c.data in ["cancel", "clear"])
def cancelar(c):

    if c.data == "cancel":

        if c.from_user.id == scrapper.cola["uso"]:
            liberar_cola(scrapper, c.from_user.id, bot)

        bot.delete_message(c.message.chat.id, c.message.message_id)

        bot.send_message(c.message.chat.id, "Muy Bien, la operación ha sido exitosamente cancelada", reply_markup=ReplyKeyboardRemove())
    
    elif c.data == "clear":
        
        bot.delete_message(c.message.chat.id, c.message.message_id)

    return


@bot.callback_query_handler(func=lambda c: c.data == "c/reload")
def cmd_reload(c):

    bot.send_message(c.from_user.id, "Estás seguro de que deseas continuar?, Esta acción no se puede deshacer e interrumpirá todos los procesos activos", reply_markup=InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Si, Deseo reiniciar", callback_data="c/reload/s")],
            [InlineKeyboardButton("No, No lo hagas", callback_data="cancel")]
        ]
    , row_width=1))

    bot.register_callback_query_handler(reboot, lambda c: c.data == "c/reload/s")

def reboot(c):
    print("Voy a reiniciar el bot")
    if len(sys.argv) > 1:
        os.execv(os.execv(sys.executable, [sys.executable, '"' + __file__ + '"']) + sys.argv)
    else:
        os.execv(os.execv(sys.executable, [sys.executable, '"' + __file__ + '"']))
    return

@bot.message_handler(commands=["c"], func=lambda message: message.from_user.id in [scrapper.creador, admin])
def cmd_command(message):
    try:
        dic_temp = {}
        dic_temp[message.from_user.id] = {"comando": False, "res": False, "texto": ""}
        dic_temp[message.from_user.id]["comando"] = message.text.split()
        if message.from_user.id == scrapper.creador:
            if len(dic_temp[message.from_user.id]["comando"]) <= 1:
                panel_admin.comandos_creador(message.from_user.id, scrapper)
                return

                
        else:
            bot.send_message(message.chat.id, "No has ingresado nada")
            return
        
        dic_temp[message.from_user.id]["comando"] = " ".join(dic_temp[message.from_user.id]["comando"][1:len(dic_temp[message.from_user.id]["comando"])])

        #--------------comandos personales-------------

        if dic_temp[message.from_user.id]["comando"] == "s":
            scrapper.driver.save_screenshot("captura.png")

            bot.send_photo(message.chat.id, telebot.types.InputFile("captura.png", "captura.png"), caption="Captura de la sesión actual")

            os.remove("captura.png")

            return

        if panel_admin.comandos_creador(message.from_user.id, scrapper, dic_temp[message.from_user.id]["comando"]):
            return


        #--------------comandos personales END-------------

        dic_temp[message.from_user.id]["res"] = subprocess.run(dic_temp[message.from_user.id]["comando"], shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
        
        if dic_temp[message.from_user.id]["res"].returncode:
            dic_temp[message.from_user.id]["texto"]+= "❌ Ha ocurrido un error usando el comando...\n\n"
        
        if dic_temp[message.from_user.id]["res"].stderr:
            dic_temp[message.from_user.id]["texto"]+= "stderr:\n{}\n\n".format(dic_temp[message.from_user.id]["res"].stderr)

        else:
            dic_temp[message.from_user.id]["texto"]+= "stderr:\nComando ingresado ✅\n\n".format(dic_temp[message.from_user.id]["res"].stderr)
            
        if dic_temp[message.from_user.id]["res"].stdout:
            dic_temp[message.from_user.id]["texto"]+= "stdout\n{}\n\n".format(dic_temp[message.from_user.id]["res"].stdout)

        else:
            dic_temp[message.from_user.id]["texto"]+= "stdout\nComando ingresado ✅\n\n".format(dic_temp[message.from_user.id]["res"].stderr)
            
            
        try:
            bot.send_message(message.chat.id, dic_temp[message.from_user.id]["texto"])
        except:
            with open("archivo.txt", "w") as file:
                file.write(dic_temp[message.from_user.id]["texto"])
            
            with open("archivo.txt", "rb") as file:
                bot.send_document(message.chat.id, telebot.types.InputFile(file.name))
                
            os.remove("archivo.txt")
                
    
    except Exception as e:
        bot.send_message(message.chat.id, "Error:\n{}".format(e.args))



@bot.message_handler(func=lambda x: True)
def cmd_any(m: telebot.types.Message):
    m.text = m.text.strip()

    if m.text.strip().startswith("/") and m.from_user.id in [admin, scrapper.creador]:

        panel_admin.comandos_admin(m, scrapper)



    else:
        bot.send_message(m.chat.id, "Escribe /help, para recibir ayuda")
    
    # if m.text.lower() == "cancelar operacion" and scrapper.cola["uso"] == m.chat.id:
    #     liberar_cola(scrapper, m.from_user.id)

    #     bot.send_message("Operación Cancelada exitosamente por el handler")
    # else:
        

    return

#comprobar si habia un proceso activo y el host se calló
if scrapper.cola["uso"] and scrapper.temp_dict.get(scrapper.cola["uso"]):
    
    scrapper.interrupcion = True #Esta variable la defino como flag para omitir todos los mensajes del bot hasta el punto donde estaba y que no sea repetitivo para el usuario

    print("Al parecer, habia un proceso de publicación activo, a continuación lo reanudaré")
    threading.Thread(name="Hilo usuario: {}".format(scrapper.cola["uso"]), target=scrapper.start_publish, args=(scrapper.cola["uso"],)).start()

else:
    scrapper.cola["uso"] = False


if not scrapper.interrupcion and os.environ.get("admin"):
    bot.send_message(admin, "El bot de publicaciones de Facebook está listo :)")
    

app = Flask(__name__)

@app.route("/", methods=['POST', 'GET'])
def webhook():
    global scrapper
    
    if request.method.lower() == "post":   
        
            
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            try:
                if "host" in update.message.text and update.message.chat.id in [admin, scrapper.creador]:
                    bot.send_message(update.message.chat.id, "El url del host es: <code>{}</code>".format(request.url))
                    
                    #en los host gratuitos, cuando pasa un tiempo de inactividad el servicio muere, entonces hago este GET a la url para que no muera  
                    if not list(filter(lambda i: i.name == "hilo_requests", threading.enumerate())):
                        
                        def hilo_requests():
                            while True:
                                requests.get(os.getenv("webhook_url"))
                                time.sleep(60)
                                

                        threading.Thread(target=hilo_requests, name="hilo_requests").start()

            except:
                pass
            
            bot.process_new_updates([update])


    else:
        return "<a href='https://t.me/{}'>Contáctame</a>".format(bot.user.username)
        
    return "<a href='https://t.me/{}'>Contáctame</a>".format(bot.user.username)

@app.route("/healthz")
def check():
    return "200 OK"


def flask():
    if os.getenv("webhook_url"):
        bot.remove_webhook()
        time.sleep(2)
        bot.send_message(int(os.environ.get("admin")), "Estoy usando el método webhook")
        bot.set_webhook(url=os.environ["webhook_url"])
    
    app.run(host="0.0.0.0", port=5000)


try:
    print("La dirección del servidor es:{}".format(request.host_url))
    
except:
    hilo_flask=threading.Thread(name="hilo_flask", target=flask)
    hilo_flask.start()
    
if not os.getenv("webhook_url"):
    bot.remove_webhook()
    time.sleep(2)
    if os.environ.get("admin"):
        bot.send_message(int(os.environ.get("admin")), "Estoy usando el método polling")

    bot.infinity_polling(timeout=80,)