from flask import Flask, render_template, request, session, redirect, url_for
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import os

app = Flask(__name__)

# Configuración
app.secret_key = os.environ.get("SECRET_KEY", "DB2025")
mongo_uri = os.environ.get("MONGO_URI", "mongodb+srv://LILIJC:DB2025@cluster0.qkojfmq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# Variables globales
contactos_collection = None
db_client = None

def connect_mongo():
    try:
        client = MongoClient(mongo_uri, server_api=ServerApi('1'))
        # Verificar conexión
        client.admin.command('ping')
        db = client['BigDataApp']
        global contactos_collection
        contactos_collection = db['contactos']
        print("Conexión exitosa a MongoDB")
        return client
    except Exception as e:
        print(f"Error al conectar a MongoDB: {e}")
        return None

# Inicializar conexión
db_client = connect_mongo()

# Decorador para verificar login
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Rutas básicas
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    if contactos_collection is None:
        return render_template('contacto.html', error="Error de conexión con la base de datos.")

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('correo')
        mensaje = request.form.get('mensaje')

        if not nombre or not email or not mensaje:
            return render_template('contacto.html', error="Todos los campos son obligatorios.")

        contacto_doc = {
            'nombre': nombre,
            'email': email,
            'mensaje': mensaje,
            'fecha': datetime.now()
        }

        try:
            contactos_collection.insert_one(contacto_doc)
            return render_template('contacto.html', success="Mensaje enviado correctamente.")
        except Exception as e:
            print(f"Error al guardar en MongoDB: {e}")
            return render_template('contacto.html', error="Error al enviar el mensaje.")

    return render_template('contacto.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        client = connect_mongo()
        if client:
            try:
                db = client['administracion']
                seguridad_collection = db['seguridad']
                username = request.form.get('usuario')
                password = request.form.get('contrasena')

                user = seguridad_collection.find_one({'usuario': username, 'pass': password})

                if user:
                    session['usuario'] = username
                    return redirect(url_for('gestion_mongodb'))
                return render_template('login.html', error="Credenciales inválidas.")
            finally:
                client.close()
        return render_template('login.html', error="Error de conexión.")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def gestion_mongodb():
    databases = []
    error_message = None
    collections_data = []
    select_db = None

    client = connect_mongo()
    if client:
        try:
            databases = client.list_database_names()
            if request.method == 'POST':
                select_db = request.form.get('database')
                collections_data = get_collections_data(select_db)
        except Exception as e:
            error_message = "Error al acceder a la base de datos."
            print(f"Error: {e}")
        finally:
            client.close()
    else:
        error_message = "Error de conexión a MongoDB."

    return render_template(
        'admin.html',
        databases=databases,
        select_db=select_db,
        collections_data=collections_data,
        error_message=error_message
    )

def get_collections_data(selected_db):
    collections_data = []
    if not selected_db:
        return collections_data

    client = connect_mongo()
    if client:
        try:
            db = client[selected_db]
            collections = db.list_collection_names()
            for index, name in enumerate(collections, 1):
                count = db[name].count_documents({})
                collections_data.append({
                    'index': index,
                    'name': name,
                    'count': count
                })
        except Exception as e:
            print(f"Error al obtener colecciones de {selected_db}: {e}")
        finally:
            client.close()
    return collections_data

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)