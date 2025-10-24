from pymongo import MongoClient
import os

cli = MongoClient(os.environ["MONGO_HOST"])
db = cli["face"]
collection = db["usuarios"]
res = collection.delete_many({})

print(res)

input()