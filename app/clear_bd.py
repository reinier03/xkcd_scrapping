from pymongo import MongoClient
import os

cli = MongoClient(os.environ["MONGO_HOST"])
db = cli["face"]
collection = db["usuarios"]

breakpoint()


#'Somos de Sancti spiritus 56740155 Domicilio a jatibonico cabaiguan y trinidad Manillas'

res = collection.delete_many({})

print(res)

input()