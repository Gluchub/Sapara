import pyrebase
from main import usersing
from dotenv import load_dotenv
import os

load_dotenv()

firebaseConfig = {
  'apiKey': os.getenv('FIREBASE_API_KEY'),
  'authDomain': "sapara-email.firebaseapp.com",
  'databaseURL': "https://sapara-email-default-rtdb.asia-southeast1.firebasedatabase.app",
  'projectId': "sapara-email",
  'storageBucket': "sapara-email.appspot.com",
  'messagingSenderId': "799997717376",
  'appId': "1:799997717376:web:062b09a2b431e31beb2f65",
  'measurementId': "G-1G9Y3LP5Z6"
}

firebase= pyrebase.initialize_app(firebaseConfig)

db= firebase.database()

def chathistory_by_id(chat_id):
    chat_history= db.child('Chathistory').child(chat_id).get()
    return chat_history

def create_user():
    while True:
        user = usersing()
        if len(user)> 70 :
            continue
        else:
            break
    return user

def create_doc(data):
    result=db.child('Chathistory').push(data)
    chat_id=result['name']
    print(result['name'])
    return chat_id

def retrieve_data():
    data = db.child('Chathistory').get()
    return data.val()

def remove_data(chat_id):
    db.child('Chathistory').child(chat_id).remove()