import logging
import time
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from twilio.rest import Client

# Configurações do Twilio
ACCOUNT_SID = "AC26b02e2da624219242572a471e7fccab"
AUTH_TOKEN = "6bcd094983599a970961c42eb6b24858"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"  # Número do Twilio para WhatsApp
DESTINATION_NUMBER = "whatsapp:+555193402351"  # Seu número ou do grupo

# Caminho do arquivo JSON
JSON_FILE_PATH = r'C:\Users\mateus\Documents\Projetos\voleizinho\volei_agenda.json'
ultimo_estado = ""
ultima_modificacao = 0

# Função para enviar mensagens pelo Twilio
client = Client(ACCOUNT_SID, AUTH_TOKEN)

def enviar_mensagem_twilio(mensagem):
    content_message = json.dumps({"1": mensagem})
    message = client.messages.create(
        from_=TWILIO_WHATSAPP_NUMBER,
        content_sid='HX04f53b8e134d73751f8a4c55a36ec7e3',
        content_variables=content_message,
        # body=mensagem,
        to=DESTINATION_NUMBER
    )

def obter_lista_presenca():
    with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    mensagens = []
    for dia, info in data.items():
        confirmados = info.get("Titulares", [])
        if confirmados:
            mensagem = f"\n\n*{dia}*\nConfirmados:\n " + "\n ".join(confirmados)
            mensagens.append(mensagem)
    return "".join(mensagens)

class MonitorJSON(FileSystemEventHandler):
    def on_modified(self, event):
        global ultimo_estado, ultima_modificacao
        if event.src_path.endswith("volei_agenda.json"):
            agora = time.time()
            if agora - ultima_modificacao < 2:
                # Debounce: ignora eventos múltiplos em menos de 2 segundos
                return
            ultima_modificacao = agora
            logging.info("Arquivo JSON modificado! Verificando presença...")
            nova_mensagem = obter_lista_presenca()
            if nova_mensagem and nova_mensagem != ultimo_estado:
                ultimo_estado = nova_mensagem
                enviar_mensagem_twilio(nova_mensagem)
if __name__ == "__main__":
    event_handler = MonitorJSON()
    observer = Observer()
    observer.schedule(event_handler, path=r'C:\Users\mateus\Documents\Projetos\voleizinho', recursive=False)
    observer.start()
    print("Monitorando alterações no JSON...")
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()