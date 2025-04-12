import firebase_admin
from firebase_admin import credentials, firestore
import os

print("Iniciando teste do Firebase...")

try:
    # Verifica se o arquivo de credenciais existe
    if os.path.exists("firebase_config_py.json"):
        print("Arquivo de configuração do Firebase encontrado.")
        cred = credentials.Certificate("firebase_config_py.json")
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("Firebase inicializado com sucesso!")
        
        # Tenta acessar a coleção 'agenda'
        print("Tentando acessar a coleção 'agenda'...")
        docs = db.collection("agenda").stream()
        count = 0
        for doc in docs:
            print(f"Documento encontrado: {doc.id}")
            count += 1
        
        if count == 0:
            print("Nenhum documento encontrado na coleção 'agenda'.")
            print("Tentando criar um documento de teste...")
            db.collection("agenda").document("teste").set({"teste": True})
            print("Documento de teste criado com sucesso!")
    else:
        print("Arquivo de configuração do Firebase não encontrado.")
except Exception as e:
    print(f"Erro ao inicializar o Firebase: {str(e)}")

print("Teste concluído!")
