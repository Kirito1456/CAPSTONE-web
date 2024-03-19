import pymongo

def connect_to_mongodb():
    client = pymongo.MongoClient("mongodb+srv://admin:Qvr4tlGx4qFPdgoU@pharmacy.h3k6bxm.mongodb.net/?retryWrites=true&w=majority&appName=pharmacy")
    db = client["pharmacy"]
    collection = db["drugs"]
    return collection