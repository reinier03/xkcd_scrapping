from f_src.facebook_scrapper import cargar_cookies
from tb_src.main_classes import scrapping 
from tb_src.usefull_functions import *
from f_src.chrome_driver import uc_driver
import dill
import tempfile
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
breakpoint()

with open("variables_entorno_copia.env", "wb") as file:
    file.write()

with open("variables_entorno.env", "r") as file:
    texto = file.read()

os.remove("variables_entorno.env")

if "admin=" in texto and "MONGO_URL=" in texto:
    for i in texto.splitlines():
        os.environ[re.search(r".*=", i).group().replace("=", "")] = re.search(r"=.*", i).group().replace("=", "")

