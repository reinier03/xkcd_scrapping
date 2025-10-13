from pymongo import MongoClient
import os

cli = MongoClient(os.environ["MONGO_HOST"])
db = cli["face"]
c = db["usuarios"]

breakpoint()


