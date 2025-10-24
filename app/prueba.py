# from pymongo import MongoClient
# import os

# cli = MongoClient(os.environ["MONGO_HOST"])
# db = cli["face"]
# collection = db["usuarios"]
# res = collection.delete_many({})

# print(res)

import easyocr

reader = easyocr.Reader(['ja','en'], gpu=False, detail = 0) # this needs to run only once to load the model into memory
result = reader.readtext(r'D:\captura_identificar.png')

breakpoint()
