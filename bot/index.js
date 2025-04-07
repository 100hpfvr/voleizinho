const { Client, LocalAuth } = require("whatsapp-web.js");
const qrcode = require("qrcode-terminal");
const admin = require("firebase-admin");
const serviceAccount = require("../firebase/firebase_config_node.json");

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

const client = new Client({
  authStrategy: new LocalAuth(),
  puppeteer: { headless: true, args: ["--no-sandbox"] }
});

client.on("qr", (qr) => qrcode.generate(qr, { small: true }));

client.on("ready", () => {
  console.log("✅ Bot pronto!");
  monitorarFirebase();
});

function monitorarFirebase() {
  db.collection("agenda").onSnapshot(async (snapshot) => {
    let mensagens = [];
    snapshot.forEach(doc => {
      const data = doc.data();
      if (data?.Titulares?.length) {
        mensagens.push(`\n*${doc.id}*\nConfirmados: ${data.Titulares.join(", ")}`);
      }
    });

    if (mensagens.length) {
      const chats = await client.getChats();
      const grupo = chats.find(chat => chat.name === "Voleizinho");
      if (grupo) grupo.sendMessage(mensagens.join("\n"));
    }
  });
}

client.initialize();