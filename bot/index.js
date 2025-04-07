const fs = require("fs");
const qrcode = require("qrcode-terminal");
const {Client, LocalAuth} = require("whatsapp-web.js");
const chokidar = require("chokidar");

// Inicializa o cliente com autenticação persistente
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: ["--no-sandbox"],
    },
});
const dataFilePath = "./volei_agenda.json";


// Gera QR Code no terminal para login
client.on("qr", (qr) => {
    qrcode.generate(qr, {small: true});
});

// Confirma login
client.on("ready", () => {
    console.log("✅ Cliente WhatsApp pronto!");
    monitorarJSON();
});

// Lê e formata o conteúdo do JSON
function obterMensagemFormatada() {
    const data = JSON.parse(fs.readFileSync(dataFilePath, "utf8"));
    let mensagens = [];

    for (const dia in data) {
        const confirmados = data[dia]["Titulares"];
        if (confirmados && confirmados.length > 0) {
            mensagens.push(`\n*${dia}*\nConfirmados: ${confirmados.join(", ")}`);
        }
    }

    return mensagens.join("\n");
}

// Monitoramento com debounce
let ultimaMensagem = "";

function monitorarJSON() {
    chokidar.watch(dataFilePath).on("change", () => {
        const novaMensagem = obterMensagemFormatada();
        if (novaMensagem !== ultimaMensagem) {
            ultimaMensagem = novaMensagem;
            enviarMensagemParaGrupo(novaMensagem);
        }
    });
}

// Envia mensagem para o grupo pelo nome
async function enviarMensagemParaGrupo(mensagem) {
    const chats = await client.getChats();
    const grupo = chats.find((chat) => chat.name === "Demônios da Garoa");

    if (grupo) {
        grupo.sendMessage(mensagem);
        console.log("📤 Mensagem enviada para o grupo!");
    } else {
        console.log("❌ Grupo 'Voleizinho' não encontrado!");
    }
}

client.initialize();
