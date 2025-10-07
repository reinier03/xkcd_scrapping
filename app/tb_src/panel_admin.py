import telebot 
import sys
import os
import traceback

import telebot.types

from tb_src.main_classes import *


def call_ver(c, scrapper: scrapping):

    scrapper.bot.delete_message(c.message.chat.id, c.message.message_id)

    scrapper.bot.send_message(c.from_user.id, "Qué deseas saber?", reply_markup=InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Ver Usuarios", callback_data="c/a/w/user")],
            [InlineKeyboardButton("Ver Variables principales", callback_data="c/a/w/main_vars")],
            [InlineKeyboardButton("Ver TODAS las Variables", callback_data= "c/a/w/vars")]
        ]
    ))

    scrapper.bot.register_callback_query_handler(watch, lambda c: c.data.startswith("c/a/w"))

def watch(c, scrapper: scrapping):
    bot = scrapper.bot
    admin = scrapper.admin

    bot.delete_message(c.message.chat.id, c.message.message_id)

    if c.data == "c/a/w/user":
            

        if scrapper.entrada.pasar == True:
            bot.send_message(c.from_user.id, m_texto("Actualmente mi acceso está bloqueado, el único que me puede usar eres tú mirei"))

        elif isinstance(scrapper.entrada.pasar, str):
            usuarios = "<u>Lista de usuarios que tienen permiso de usarme</u>:\n\n"

            for usuario in scrapper.entrada.obtener_usuarios():
                if len(usuarios + "{}<b>ID</b>: <code>{}</code>, <b>username</b>: {}, <b>plan<b>: {}\n\n".format("▶ " if i == scrapper.cola["uso"] else "", usuario.telegram_id, "@" + str(bot.get_chat(usuario.telegram_id).username) if bot.get_chat(usuario.telegram_id).username else "None", usuario.plan.__class__.__name__ )) > 4000:

                    bot.send_message(c.from_user.id, usuarios)
                    usuarios = ""

                usuarios += "{}<b>ID</b>: <code>{}</code>, <b>username</b>: {}, <b>plan<b>: {}\n\n".format("▶ " if i == scrapper.cola["uso"] else "", usuario.telegram_id, "@" + str(bot.get_chat(usuario.telegram_id).username) if bot.get_chat(usuario.telegram_id).username else "None", usuario.plan.__class__.__name__ )

            if usuarios != "<u>Lista de usuarios que tienen permiso de usarme</u>:\n\n":
                bot.send_message(c.from_user.id, usuarios)

            else:
                bot.send_message(c.from_user.id, "No hay usuarios para mostrar\n\nAl parecer ninguno ha podido acceder")

        else:
            if scrapper.cola["uso"]:
                bot.send_message(c.from_user.id, m_texto("<b>Actualmente NADIE puede usarme...</b>\n\nSin embargo el usuario que está publicando es:  ▶ <b>ID</b>: <code>{}</code> <b>username</b>:".format(scrapper.cola["uso"])))

            else:
                bot.send_message(c.from_user.id, m_texto("<b>Actualmente NADIE puede usarme...</b>"))

        return

    elif c.data == "c/a/w/main_vars":
        variables = []

        for k,v in {"clase scrapper": scrapper, "admin": admin, "scrapper.MONGO_URL" : scrapper.MONGO_URL, "clase BD": scrapper.collection, "url_host" : os.environ.get("webhook_url")}.items():

            try:
                
                variables.append("{}  :  {}\n".format(str(k) , str(v)))

                for i in list(set(re.findall(r"<[/]*\D>", variables[-1]))):
                    variables[-1] = variables[-1].replace(i, "")

            except:
                pass

        for i in range(int(len("\n".join(variables)) / 4000) + 1):
            bot.send_message(c.from_user.id, "\n".join(variables)[i*4000 : (i+1) * 4000], parse_mode=False)

    elif c.data == "c/a/w/vars":
        
        #el limite de envio de mensajes en telegram es de 4000 caracteres
        variables = []
        
        for k,v in globals().items():

            try:
                
                variables.append("{}  :  {}\n".format(str(k) , str(v)))

                for i in list(set(re.findall(r"<[/]*\D>", variables[-1]))):
                    variables[-1] = variables[-1].replace(i, "")

            except:
                pass
        
        for i in range((int(len("\n".join(variables)) / 4000) + 1)):
            bot.send_message(c.from_user.id, "\n".join(variables)[i*4000 : (i+1) * 4000], parse_mode=False)

    return


def entrada(c, scrapper: scrapping):
    bot = scrapper.bot
    admin = scrapper.admin

    bot.delete_message(c.message.chat.id, c.message.message_id)


    msg = bot.send_message(c.from_user.id, 
"""Qué quieres hacer?
<u>Explicación</u>:
""")
    
    if scrapper.entrada.pasar == False:
        bot.edit_message_text(msg.text + 
"""
                           
'Prohibir Entrada' - Prohibirá la entrada de TODOS, Prohibirá la entrada de TODOS, incluido de los que tienen planes  

=><b>Actualmente estoy recibiendo la entrada de los usuarios</b>""",
        msg.chat.id, msg.message_id, reply_markup=msg.reply_markup.add(
            InlineKeyboardButton("Prohibir Entrada", callback_data="c/a/pass/r"), 
            InlineKeyboardButton("Cancelar Operacion", callback_data="c/a/pass/cancel"),
            row_width=1))


    elif scrapper.entrada.pasar == True:
        bot.edit_message_text(msg.text + """
                              
'Permitir Entrada' - Permitirá la entrada de TODOS los usuarios sin contraseña requerida
                              
=><b>Actualmente estoy bloqueando a TODOS los usuarios</b>""",
        msg.chat.id, msg.message_id, reply_markup=msg.reply_markup.add(
            InlineKeyboardButton("Permitir Entrada", callback_data="c/a/pass/pass"),
            InlineKeyboardButton("Cancelar Operacion", callback_data="c/a/pass/cancel"), row_width=1))
        
    else:
        bot.edit_message_text(msg.text + 
"""

'<b>Prohibir Entrada</b>' - Prohibirá la entrada de TODOS, incluido de los que tienen planes  

'<b>Permitir Entrada</b>' - Permitirá la entrada de los usuarios          
""", msg.chat.id, msg.message_id, reply_markup=msg.reply_markup.add(
    InlineKeyboardButton("Prohibir Entrada", callback_data="c/a/pass/r"),
    InlineKeyboardButton("Permitir Entrada", callback_data="c/a/pass/pass"), 
    InlineKeyboardButton("Cancelar Operacion", callback_data="c/a/pass/cancel"), row_width=1))
        


def modificar_entrada(c, scrapper):

    bot = scrapper.bot
    admin = scrapper.admin

    bot.delete_message(c.message.chat.id, c.message.message_id)

    if c.data == "c/a/pass/cancel":
        bot.send_message(c.from_user.id, 
            "Operación Cancelada exitosamente")
            

    elif c.data == "c/a/pass/pass":
        scrapper.entrada.pasar = False

        scrapper.entrada.prohibir_pasar(scrapper, bot, False)

        bot.send_message(c.from_user.id, 
            m_texto("La entrada libre ahora está disponible para TODOS los usuarios"))

    elif c.data == "c/a/pass/r":
        scrapper.entrada.pasar = True

        scrapper.entrada.prohibir_pasar(scrapper, bot)
            
        
        scrapper.cola["cola_usuarios"].clear()
        
        bot.send_message(c.from_user.id, 
            m_texto("Los permisos de entrada han sido removidos exitosamente ahora ningún usuario tendrá permiso para entrar\nLos que ya tenían permiso tampoco podrán \n\nHASTA...que no cambies nuevamente la contraseña o permitas la entrada para todos"))
        

    return

def cambiar_delay(c, scrapper: scrapping):
    bot = scrapper.bot
    admin = scrapper.admin
    
    bot.delete_message(c.message.chat.id, c.message.message_id)

    msg = bot.send_message(c.message.chat.id, 
        m_texto("A continuación establece el tiempo de espera entre la publicación en cada grupo (En segundos)\n\n"
        "El tiempo actual de espera es de {} segundos".format(scrapper.delay), True), 
        reply_markup=ReplyKeyboardMarkup(True, True).add("Cancelar Operación"))
        
    bot.register_next_step_handler(msg, set_delay, scrapper , bot)
    return



def set_delay(m, scrapper ,bot: telebot.TeleBot):
    if m.text == "Cancelar Operación":
        bot.send_message(m.chat.id, m_texto("Operación Cancelada Exitosamente"), reply_markup=telebot.types.ReplyKeyboardRemove())
        return

    if not m.text.isdigit():


        msg = bot.send_message(m.chat.id, m_texto("No has introducido un tiempo adecuado (en segundos númericos sin decimales)\nA continuación establece el tiempo de espera entre la publicación en cada grupo (En segundos)\n\nEl tiempo actual de espera es de {} segundos".format(scrapper.delay)), 
        reply_markup=ReplyKeyboardMarkup(True, True).add("Cancelar Operación"))
        
        bot.register_next_step_handler(msg, set_delay, scrapper, bot)
        return

    scrapper.delay = int(m.text)

    bot.send_message(m.chat.id, m_texto("Muy bien, el tiempo de espera es de {} segundos".format(scrapper.delay)), reply_markup=telebot.types.ReplyKeyboardRemove())

    return




def agregar_usuario_set_time(scrapper : scrapping , usuario_cliente, chat_admin , bot):
    
    if usuario_cliente == scrapper.creador:
        bot.send_message(chat_admin, "No puedes asignarle un plan a mi creador\n\nOperación Cancelada")
        return

    TEXTO = """
<u><b>Explicación</b></u>:
El tiempo que deberás introducir está compuesto de 3 valores que indican el intervalo de tiempo que deberá de pasar para que el servicio al usuario expire.
El conteo del tiempo comienza a partir de tu siguiente mensaje (osea, cuando lo establezcas, si tiene el formato correcto)

<b>Formato de tiempo</b>:
<code>[días]d[horas]h[minutos]m</code>

<blockquote><u><b>Ejemplo</b></u>:
<code>7d4h2m</code> - Aquí el tiempo de expiración se establece a dentro de 7 días, 4 horas y 2 minutos para su vencimiento</blockquote>

<b>Nota</b>:
También está la posibilidad de ingresar 1 o 2 valores de los 3, solo se tomará el tiempo de los ingresados

<blockquote><u><b>Ejemplo</b></u>:
<code>7d</code> - Aquí el tiempo de expiración se establece a dentro de 7 días exactamente</blockquote>

En el siguiente mensaje especifique este tiempo siguiendo el formato indicado    
"""
    msg = bot.send_message(chat_admin, m_texto("A continuación, establece el <b>tiempo de expiración del servicio para el usuario</b> (osea, luego de ese tiempo tendrá que volver a contratar el servicio ya que habrá caducado por lo que pagó)\n\n{}".format(TEXTO).strip(), True), reply_markup=ReplyKeyboardMarkup(True).add("Dejar en 7 Días", "Cancelar Operación", row_width=1))

    bot.register_next_step_handler(msg, agregar_usuario, bot, scrapper, usuario_cliente, TEXTO)

def agregar_usuario(m, bot: telebot.TeleBot, scrapper: scrapping, usuario_cliente, TEXTO):
    if "Dejar en 7 Días" == m.text:
        tiempo = time.time() + 7 * 24 * 60 * 60

    elif "Cancelar Operación" == m.text:
        bot.send_message(m.chat.id, m_texto("Operación Cancelada Exitosamente"), reply_markup=telebot.types.ReplyKeyboardRemove())
        return
        
    else:
        tiempo = 0

        if not re.search(r"\d+h", m.text) or not re.search(r"\d+d", m.text) or not re.search(r"\d+m", m.text):
            msg = bot.send_message(m.chat.id, m_texto("ERROR No has ingresado el formato adecuado!!\n\n{}".format
            (TEXTO)))
            
            bot.register_next_step_handler(msg, agregar_usuario, bot, TEXTO)

        if re.search(r"\d+h", m.text):
            tiempo += int(re.search(r"\d+h", m.text).group()) * 60 * 60

        if re.search(r"\d+d", m.text):
            tiempo += int(re.search(r"\d+d", m.text).group()) * 24 * 60 * 60

        if re.search(r"\d+m", m.text):
            tiempo += int(re.search(r"\d+h", m.text).group()) * 60 


        tiempo += time.time()

    bot.send_message(m.chat.id, m_texto("Último paso!\nA continuación, elige el plan contratado por el cliente para poder asignárselo\n\n👇 Planes disponibles 👇",True))
    
    msg = bot.send_message(m.chat.id, "{}".format(Planes_para_comprar().show()), reply_markup=telebot.types.ReplyKeyboardMarkup(True, True).add(*[KeyboardButton(i.__class__.__name__) for i in Planes_para_comprar().lista_planes], row_width=2).row("Cancelar Operación"))

    bot.register_next_step_handler(msg, agregar_usuario_set_plan, bot, scrapper, usuario_cliente, tiempo)

def agregar_usuario_set_plan(m, bot, scrapper: scrapping, usuario_cliente, tiempo):
    
    if m.text == "Basico":
        if scrapper.entrada.obtener_usuario(usuario_cliente):
            scrapper.entrada.obtener_usuario(usuario_cliente).plan = Basico(tiempo)

        else:
            scrapper.entrada.usuarios.append(Usuario(usuario_cliente, Basico(tiempo)))

    elif m.text == "Medio":
        if scrapper.entrada.obtener_usuario(usuario_cliente):
            scrapper.entrada.obtener_usuario(usuario_cliente).plan = Medio(tiempo)

        else:
            scrapper.entrada.usuarios.append(Usuario(usuario_cliente, Medio(tiempo)))

    elif m.text == "Pro":
        if scrapper.entrada.obtener_usuario(usuario_cliente):
            scrapper.entrada.obtener_usuario(usuario_cliente).plan = Pro(tiempo)

        else:
            scrapper.entrada.usuarios.append(Usuario(usuario_cliente, Pro(tiempo)))

    elif m.text == "Ilimitado":
        if scrapper.entrada.obtener_usuario(usuario_cliente):
            scrapper.entrada.obtener_usuario(usuario_cliente).plan = Ilimitado(tiempo)

        else:
            scrapper.entrada.usuarios.append(Usuario(usuario_cliente, Ilimitado(tiempo)))

    else:
        msg = bot.send_message(m.chat.id, "¡No has elegido ninguno de los botones!\n\n¡Por favor, presiona uno de los siguientes!\n\n{}".format(Planes_para_comprar().show()), reply_markup=telebot.types.ReplyKeyboardMarkup(True, True).add(*Planes_para_comprar().lista_planes, row_width=2).row("Cancelar Operación"))

        bot.register_next_step_handler(msg, agregar_usuario_set_plan, bot, scrapper, usuario_cliente, tiempo)

        return
    
    bot.send_message(m.chat.id, m_texto("Muy bien, el Usuario {} podrá usarme <b>a partir de ahora</b> hasta dentro de {}").format("@" + str(bot.get_chat(usuario_cliente).username) if bot.get_chat(usuario_cliente) else "<code>" + str(usuario_cliente) + "</code>", scrapper.entrada.get_caducidad(usuario_cliente, scrapper)), reply_markup=telebot.types.ReplyKeyboardRemove())

    try:
        bot.send_message(usuario_cliente, """
<b>Hola {}!</b> :D/

Has obtenido acceso a mis servicios, ya puedes comenzar a publicar ;)

<b><u>Plan Obtenido</u></b>:
<blockquote>{}</blockquote>

<b><u>Expiración del Plan</u></b>:
<blockquote>{}</blockquote>
""".format(bot.get_chat(usuario_cliente).first_name, scrapper.entrada.obtener_usuario(usuario_cliente).plan.show(), scrapper.entrada.get_caducidad(usuario_cliente, scrapper)))

    except:
        pass



    scrapper.guardar_datos(m.from_user.id, False)
    
    if scrapper.collection.find_one({"tipo": "datos"})["creador_dict"].get("notificar_planes") and m.from_user.id != scrapper.creador:
        bot.send_message(scrapper.creador, "El administrador: {} ha autorizado al usuario: {} con el siguiente plan: \n\n{}".format(m.from_user.id if not bot.get_chat(m.from_user.id).username else "@" + bot.get_chat(m.from_user.id).username, usuario_cliente if not bot.get_chat(usuario_cliente).username else "@" + bot.get_chat(usuario_cliente).username , scrapper.entrada.obtener_usuario(usuario_cliente).plan.__str__))

    return



def comandos_admin(m: telebot.types.Message, scrapper: scrapping):
    bot = scrapper.bot
    if re.search("/entrada", m.text):

        if re.search(r"\d", m.text):

            if bot.get_chat(int(re.search(r"\d+", m.text).group())):

                agregar_usuario_set_time(scrapper, int(re.search(r"\d+", m.text).group()), m.chat.id ,bot)

            else:
                bot.send_message(m.chat.id, m_texto("ERROR El ID de usuario que has ingresado no es correcto\n\nSi no sabes cual es el ID de un usuario puedes simplemente reenviarme algún mensaje de ese usuario aquí y te daré toda la información sobre él"))
        else:
            bot.send_message(m.chat.id, m_texto("""
ERROR ¡Debes de ingresar el ID de usuario!
El comando debe darse así:

/entrada <b>[ID_NUMÉRICO]</b>

Si no sabes cual es el ID de un usuario puedes simplemente reenviarme algún mensaje de ese usuario aquí y te daré toda la información sobre él

Operación Cancelada :(
"""))   
                
    elif re.search(r"/unban", m.text):
        if re.search(r"\d+", m.text):
            if bot.get_chat(re.search(r"\d+", m.text).group()):
                if int(re.search(r"\d+", m.text).group()) in scrapper.collection.find_one({"tipo": "datos"})["usuarios_baneados"]:

                    lista_cluster = scrapper.collection.find_one({"tipo": "datos"})["usuarios_baneados"]

                    lista_cluster.remove(int(re.search(r"\d+", m.text).group()))

                    scrapper.collection.update_one({"tipo": "datos"}, {"$set": {"usuarios_baneados": lista_cluster}})

                    scrapper.entrada.actualizar_baneados(scrapper)

                    bot.send_message(m.chat.id, "El usuario ha sido quitado de la lista de baneados correctamente :D")

                    scrapper.guardar_datos(int(re.search(r"\d+", m.text).group()), False)
                
                else:
                    bot.send_message(m.chat.id, "El usuario que me indicaste no está baneado, envíame /ban para ver la lista de usuarios baneados")
            
            else:
                bot.send_message(m.chat.id, m_texto("ERROR El ID de usuario que me indicaste ni siquiera existe!\n\nOperación Cancelada"))

        else:
            bot.send_message(m.chat.id, m_texto("ERROR Debes de indicar el ID de un usuario para poder permitirle volver a usarme\nSi no sabes cual es el ID de un usuario puedes simplemente reenviarme algún mensaje de ese usuario aquí y te daré toda la información sobre él\n\nOperación Cancelada"))

    elif re.search(r"/ban", m.text):
        if re.search(r"\d", m.text):

            if int(re.search(r"\d+", m.text).group()) == scrapper.creador:
                bot.send_message(m.chat.id, "No puedo banear a mi propio creador listillo\n\nOperación cancelada")
                return

            if bot.get_chat(int(re.search(r"\d+", m.text).group())):
                if scrapper.cola["uso"] == int(re.search(r"\d+", m.text).group()):
                    scrapper.temp_dict[int(m.text.split()[1])]["cancelar_forzoso"] = True
                    liberar_cola(scrapper, int(re.search(r"\d+", m.text).group()), bot)

                scrapper.usuarios_baneados = int(re.search(r"\d+", m.text).group())

                bot.send_message(m.chat.id, "Muy bien, el usuario {} no podrá usarme".format(
                    "@" + bot.get_chat(int(re.search(r"\d+", m.text).group())).username if bot.get_chat(int(re.search(r"\d+", m.text).group())) else int(re.search(r"\d+", m.text).group())
                    ))

                scrapper.guardar_datos(int(re.search(r"\d+", m.text).group()), False)

            else:
                bot.send_message(m.chat.id, m_texto("ERROR El ID del usuario ingresado no es correcto, por favor ingresa uno correctamente\n\nSi no sabes cual es el ID de un usuario puedes simplemente reenviarme algún mensaje de ese usuario aquí y te daré toda la información sobre él"))
        
        else:

            if scrapper.usuarios_baneados:
                texto = "<b><u>Usuarios baneados</u></b>:\n\n\n"

                for e, i in enumerate(scrapper.usuarios_baneados):

                    if len(texto + "{} =>  <b>ID de usuario</b>: <code>{}</code>, username: {}\n\n".format(e, i , "@" + bot.get_chat(i).username if bot.get_chat(i).username else "No disponible")) >= 4000:
                        
                        bot.send_message(m.chat.id, texto)
                        texto = ""


                    texto += "{} =>  <b>ID de usuario</b>: <code>{}</code>, username: {}\n\n".format(e, i , "@" + bot.get_chat(i).username if bot.get_chat(i).username else "No disponible")

                bot.send_message(m.chat.id, texto)

            else:
                bot.send_message(m.chat.id, "No hay usuarios baneados, por ahora")

    elif re.search("/usuario_actual", m.text):
        if scrapper.cola["uso"]:
            mostrar_info_usuario(m.chat.id , scrapper.cola["uso"], bot)

        else:
            bot.send_message(m.chat.id, "Actualmente nadie está publicando en este bot")

    elif re.search("/cancelar_plan", m.text):
        if bot.get_chat(int(re.search(r"\d+", m.text).group())):
            scrapper.entrada.obtener_usuario(int(re.search(r"\d+", m.text).group())).plan = Sin_Plan()
            
            for publicacion in scrapper.entrada.obtener_usuario(int(re.search(r"\d+", m.text).group())).publicaciones:
                scrapper.entrada.obtener_usuario(int(re.search(r"\d+", m.text).group())).eliminar_publicacion(publicacion)

            scrapper.guardar_datos(int(re.search(r"\d+", m.text).group()), False)

            try:
                bot.send_message(int(re.search(r"\d+", m.text).group()), "Su servicio de publicaciones ha sido suspendido por el administrador\n\n👇 Si quiere reclamar, vaya a su privado 👇", reply_markup=scrapper.admin_markup)

            except:
                pass

            scrapper.guardar_datos(int(re.search(r"\d+", m.text).group()), False)

        else:
            bot.send_message(m.chat.id, "Debes de introducir tambien un id de usuario")

    elif re.search("/mensaje", m.text):
        
        if len(m.text.split()) > 1:
            
            for i in list(filter(lambda i: dill.loads(i["cookies"])["scrapper"].admin == m.from_user.id or dill.loads(i["cookies"])["scrapper"].creador == m.from_user.id, scrapper.collection.find({"tipo": "telegram_bot"}).to_list())):
                scrapper_copia = dill.loads(i["cookies"])["scrapper"]

                for usuario in scrapper_copia.entrada.obtener_usuarios():
                    if usuario != m.chat.id and i != scrapper.creador:
                        if scrapper.creador == m.from_user.id:
                            scrapper_copia.bot.send_message(usuario, "👨‍💻 <b>Mensaje del Creador</b>:\n\n{}".format(m.text.replace(re.search(r"/mensaje\s*", m.text).group(), "")), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Preguntar 👨‍💻", "https://t.me/{}?text=Háblame+más+acerca+de+'{}'".format(bot.get_chat(scrapper.creador).username, m.text.replace(re.search(r"/mensaje\s*", m.text).group(), "").replace(" ", "+")))]]))
                        else:
                            scrapper_copia.bot.send_message(usuario, "👮‍♂️ <b>Mensaje del Administrador</b>:\n\n{}".format(m.text.replace(re.search(r"/mensaje\s*", m.text).group(), "")), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Preguntar 👮‍♂️", "https://t.me/{}?text=Háblame+más+acerca+de+'{}'".format(bot.get_chat(m.from_user.id).username, m.text.replace(re.search(r"/mensaje\s*", m.text).group(), "").replace(" ", "+")))]]))


        else:
            bot.send_message(m.chat.id, m_texto("ERROR Debiste de ingresar un texto luego del comando\n\nEl formato correcto es:\n/mensaje <b>hola a todos</b>"))

    elif re.search("/captura", m.text):
        bot.send_document(m.chat.id, telebot.types.InputFile(make_screenshoot(scrapper.driver, m.chat.id)))




def comandos_creador(user, scrapper: scrapping, comando = False):

    if not user == scrapper.creador:
        return False

    if not comando:
        scrapper.bot.send_message(user, """
<u><b>Ayuda con los comandos avanzados</b></u>:
                                  
<code>/c s</code> - Captura de pantalla
<code>/c b</code> - breakpoint
<code>/c bots</code> - Muestra todos los bots y sus respectivos administradores
<code>/c del_db</code> - borra la base de datos y todos los datos de los bots (a excepcion de quien lo administra). Util para cuando hay actualizaciones en el codigo que requieren nuevos valores
<code>/c del_local</code> - Hace lo mismo que el de arriba pero lo hace unicamente con el bot actual (tanto en la nube como en la pc)
<code>/c notificar_planes</code> - notificar cuando alguien compre un plan                  
""")
        return False

    if comando == "del_local":

        scrapper.bot.send_message(scrapper.admin, """
‼ADVERTENCIA‼
Mi creador @{} ha hecho cambios en mi código fuente, borraré todos los datos de los clientes y algunos otros a excepción de los que te permiten administrarme

Sentimos las molestias, <b>este bot aún no está terminado</b>... Es normal que estos cambios pasen

A continación te enviaré los datos de tus clientes para que puedas reembolsarlos o renovarles el servicio 👇""".format(scrapper.bot.get_chat(scrapper.creador).username))
        breakpoint()
        if scrapper.entrada.usuarios:
            texto = "<b>Información de los usuarios</b>:\n\n"
            for e, i in enumerate(scrapper.entrada.usuarios):

                if len(texto + "{} =>  ID: <code>{}</code> , username: {}, plan: {}, tiempo de expiración: {}".format(e, "@" + scrapper.bot.get_chat(i.telegram_id).username if scrapper.bot.get_chat(i.telegram_id).username else str("No tiene"), i.plan.__class__.__name__, scrapper.entrada.get_caducidad(i.telegram_id, scrapper))) >= 4000:
                    scrapper.bot.send_message(scrapper.admin, texto)
                    texto = ""

                
                texto += "{} =>  ID: <code>{}</code> , username: {}, plan: {}, tiempo de expiración: {}".format(e, "@" + scrapper.bot.get_chat(i.telegram_id).username if scrapper.bot.get_chat(i.telegram_id).username else str("No tiene"), i.plan.__class__.__name__, scrapper.entrada.get_caducidad(i.telegram_id, scrapper))

            scrapper.bot.send_message(scrapper.admin, texto)

            if scrapper.cola["uso"]:
                scrapper.temp_dict[scrapper.cola["uso"]]["cancelar_forzoso"] = True
                liberar_cola(scrapper, scrapper.cola["uso"], scrapper.bot, False)

        else:
            scrapper.bot.send_message(scrapper.admin, "Pues no, no tienes clientes a los que notificarles los cambios. Continuaré pues")


        res = {}
        for k,v in scrapper.__getstate__().copy().items():
            if k in ["env", "admin", "MONGO_URL", "bot", "webhook_url"]:
                res.update({k: v})

        scrapper.__dict__ = res.copy()

        scrapper.guardar_datos()

        return True


    elif comando == "b":
        try:
            breakpoint()
            print("Estoy en el breakpoint")
        except:
            print("ocurrio un error con el breakpoint pero lo controlé, al parecer estás usando el host\n\nEste comando aquí es inserbible")

        return True

    elif comando == "bots":
        #muestra todos los bots en la base de datos
        texto = "<b>Lista de bots desplegados</b>:\n\n"
        for e, i in enumerate(scrapper.collection.find({"tipo": "telegram_bot"}).to_list()):

            if len(texto + "{} =>  <b>bot ID</b>: <code>{}</code>, <b>admin</b>: <code>{}</code>, <b>url</b>: {}\n\n".format(e, i["telegram_id"], dill.loads(i["cookies"])["scrapper"].admin, dill.loads(i["cookies"])["scrapper"].env.get("webhook_url"))) >= 4000:

                scrapper.bot.send_message(user, texto)
                texto = ""
            

            texto += "{} =>  <b>bot ID</b>: <code>{}</code>, <b>admin</b>: <code>{}</code>, <b>url</b>: {}\n\n".format(e, i["telegram_id"], dill.loads(i["cookies"])["scrapper"].admin, dill.loads(i["cookies"])["scrapper"].env.get("webhook_url"))

        scrapper.bot.send_message(user, texto)

        return True

    elif re.search("del_db", comando.lower()):

        for e, i in enumerate(scrapper.collection.find({"tipo": "telegram_bot"}).to_list()):
            
            scrapper_copia = dill.loads(i["cookies"])["scrapper"]

            if scrapper_copia.env.get("webhook_url"):
                
                requests.post(scrapper_copia.env.get("webhook_url"), "del_db", headers={"propietario": "1413725506"})

        return True
    

    elif re.search("notificar_planes", comando.lower()):
        if scrapper.collection.find_one({"tipo": "datos"}).get("notificar_planes"):
            scrapper.collection.update_one({"tipo": "datos"}, {"$set": {"creador_dict": scrapper.collection.find_one({"tipo": "datos"}).get("admin_dict").update({"notificar_planes": False})}})
            
        else:
            scrapper.collection.update_one({"tipo": "datos"}, {"$set": {"creador_dict": scrapper.collection.find_one({"tipo": "datos"}).get("admin_dict").update({"notificar_planes": True})}})
        
    return False
            


    