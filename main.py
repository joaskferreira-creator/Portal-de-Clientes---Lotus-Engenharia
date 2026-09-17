from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from notion_client import Client
import os
app = FastAPI()
app.mount("/static", StaticFiles(directory="."), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CONFIGURAÇÕES

DATA_SOURCE_ID = "1fdd8a8c-4985-8023-8a95-000bb60ecc0f"

# CONEXÃO COM NOTION
notion = Client(
    auth=os.getenv("NOTION_TOKEN")
)
response = notion.data_sources.query(
    data_source_id=DATA_SOURCE_ID
)
@app.get("/")
def home():
    return RedirectResponse(url="/portal")

@app.get("/portal")
def portal():

    with open("index.html", "r", encoding="utf-8") as arquivo:
        conteudo = arquivo.read()

    return HTMLResponse(content=conteudo)


@app.get("/clientes")
def clientes():

    response = notion.data_sources.query(
    data_source_id=DATA_SOURCE_ID
)

    resultado = []

    for cliente in response["results"]:

        props = cliente["properties"]

        nome = props["Nome do Cliente"]["title"][0]["plain_text"]

        andamento = props["Andamento do Cliente"]["status"]["name"]

        codigo = props["Codigo_ID"]["unique_id"]

        codigo_completo = str(codigo["number"])

        resultado.append({
            "codigo": codigo_completo,
            "cliente": nome,
            "andamento": andamento
        })

    return resultado


@app.get("/cliente/{codigo_busca}")
def buscar_cliente(codigo_busca: str):
    print("TOKEN OK:", bool(os.getenv("NOTION_TOKEN")))
    response = notion.data_sources.query(
        data_source_id=DATA_SOURCE_ID
    )

    for cliente in response["results"]:

        props = cliente["properties"]

        codigo = props["Codigo_ID"]["unique_id"]
        codigo_completo = str(codigo["number"])

        if codigo_completo == str(codigo_busca):

            nome = props["Nome do Cliente"]["title"][0]["plain_text"]

            andamento = props["Andamento do Cliente"]["status"]["name"]

            documentacao = props["Documentação"]["status"]["name"]

            concessionaria = ""

            if props["Concessionárias"]["select"]:
                concessionaria = (
                    props["Concessionárias"]["select"]["name"]
                )

            procuracao = [
                item["name"]
                for item in props["Procuração"]["multi_select"]
            ]

            # ==========================
            # CAMPOS ADICIONAIS
            # ==========================

            art_status = []
            n_art = ""
            data_parecer = ""
            data_envio = ""
            protocolo = ""

            # ART Status (Multi Select)
            try:
                if props.get("ART Status"):
                    art_status = [
                        item["name"]
                        for item in props["ART Status"]["multi_select"]
                    ]
            except:
                pass

            # N° ART (Número)
            try:
                campo = props.get("N°ART")

                if campo and campo["number"] is not None:
                    n_art = str(campo["number"])

            except:
                pass

            # Data do Parecer
            try:
                campo = props.get("Data do Parecer")

                if campo and campo["date"]:
                    data_parecer = campo["date"]["start"]

            except:
                pass

            # Data de Envio
            try:
                campo = props.get("Data de Envio")

                if campo and campo["date"]:
                    data_envio = campo["date"]["start"]

            except:
                pass

            # Protocolo Homologação
            try:
                campo = props.get("Protocolo Homologação")

                if campo and campo["rich_text"]:
                    protocolo = campo["rich_text"][0]["plain_text"]

            except:
                pass

            # ==========================
            # DIAGRAMA
            # ==========================

            diagrama = {
                "disponivel": False,
                "url": ""
            }

            campo_diagrama = props.get("Diagrama")

            if campo_diagrama and campo_diagrama["files"]:

                arquivo = campo_diagrama["files"][0]

                if "file" in arquivo:

                    diagrama["disponivel"] = True
                    diagrama["url"] = arquivo["file"]["url"]

                elif "external" in arquivo:

                    diagrama["disponivel"] = True
                    diagrama["url"] = arquivo["external"]["url"]

            return {

                "codigo": codigo_completo,
                "cliente": nome,

                "andamento": andamento,
                "documentacao": documentacao,

                "concessionaria": concessionaria,

                "procuracao": procuracao,

                "art_status": art_status,

                "n_art": n_art,

                "data_parecer": data_parecer,

                "data_envio": data_envio,

                "protocolo": protocolo,

                "diagrama": diagrama

            }

    return {
        "erro": "Cliente não encontrado"
    }
