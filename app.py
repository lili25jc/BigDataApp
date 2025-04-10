from flask import Flask, render_template, request
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os


app = Flask(__name__)
mongo_uri = os.environ.get("MONGO_URI")

if not mongo_uri:
    # Usar una URI de conexión de MongoDB local si no se proporciona una URI de conexión
    mongo_uri = "mongodb+srv://DbCentral:DbCentral2025@cluster0.vhltza7.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

#Función para conectar a MongoDB    
def connect_mongo():
    try:
        client = MongoClient(mongo_uri, server_api=ServerApi('1'))
        print("Conexión exitosa a MongoDB")
        return client
    except Exception as e:
        print(f"Error al conectar a MongoDB: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    client = connect_mongo()
    database = []
    error_message = None
    collections_data = [] 
    
    if client:
        try:
            # Obtener la lista de bases de datos
            database = client.list_database_names()
        except Exception as e:
            error_message = f"NO es posible listar las bases de datos."
            print(f"Error listing database: {e}")
        finally:
            client.close()      
    else:
        error_message = "No fue posible conectar a MongoDB"
    
    if request.method == 'POST':
        select_db = request.form.get('database')  
        collections_data = get_collections_data(select_db)
        return render_template('index.html', databases=database, select_db=select_db, collections_data=collections_data, error_message=error_message)
    return render_template('index.html', databases=database, collections_data=collections_data, error_message=error_message)

def get_collections_data(database_name):
    client = connect_mongo()
    collections_data = []
    if client and database_name:
        db = client[database_name]
        try:
            collections = db.list_collection_names()
            for index, collection_name in enumerate(collections):
                count = db[collection_name].count_documents({})
                collections_data.append({
                    'index': index+1,
                    'name': collection_name,
                    'count': count
                })
        except Exception as e:
            print(f"Error al obtener las colecciones de la: {database_name}: {e}")
        finally:
            client.close()
    return collections_data

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=os.getenv("PORT", 5000))