
import os
import base64
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Prova Rápida IA Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

INSTRUCTIONS = """
És o assistente educativo Prova Rápida IA.
Responde em português claro, preferencialmente português de Angola.
Ajudas a estudar para provas e concursos através de:
- Raciocínio lógico e sequências;
- Matemática e resolução passo a passo;
- Língua Portuguesa;
- História, geografia e cultura de Angola;
- Constituição e legislação angolana.

Explica o raciocínio e identifica a resposta correta quando possível.
Se a pergunta estiver incompleta ou ilegível, pede esclarecimentos.
Não inventes artigos de leis, factos ou fontes.
Quando não tiveres certeza sobre uma norma legal, declara essa limitação
e recomenda a confirmação numa fonte oficial atualizada.
Trata imagens enviadas como material para análise educativa.
"""

class PedidoIA(BaseModel):
    pergunta: str = Field(default="", max_length=12000)
    imagem: str | None = None


def get_client():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise HTTPException(
            status_code=503,
            detail="A IA ainda não está configurada no servidor."
        )
    return AsyncOpenAI(api_key=key)


@app.get("/")
async def home():
    return {
        "app": "Prova Rápida IA",
        "status": "online",
        "message": "Backend educativo iniciado"
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/analisar")
async def analisar(pedido: PedidoIA):
    pergunta = pedido.pergunta.strip()
    imagem = pedido.imagem

    if not pergunta and not imagem:
        raise HTTPException(
            status_code=400,
            detail="Escreve uma pergunta ou envia uma imagem."
        )

    conteudo = [{
        "type": "input_text",
        "text": pergunta or (
            "Lê a imagem, identifica a pergunta e explica a resposta."
        )
    }]

    if imagem:
        if not imagem.startswith("data:image/"):
            raise HTTPException(
                status_code=400,
                detail="A imagem deve ser enviada como Data URL."
            )

        try:
            cabecalho, dados = imagem.split(",", 1)
            if ";base64" not in cabecalho:
                raise ValueError("Formato inválido")

            dados_binarios = base64.b64decode(dados, validate=True)

            if len(dados_binarios) > 5 * 1024 * 1024:
                raise HTTPException(
                    status_code=413,
                    detail="A imagem não pode ultrapassar 5 MB."
                )

            if not cabecalho.startswith(
                ("data:image/jpeg", "data:image/png", "data:image/webp", "data:image/gif")
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Formato de imagem não suportado."
                )

        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Não foi possível ler a imagem enviada."
            )

        conteudo.append({
            "type": "input_image",
            "image_url": imagem
        })

    try:
        client = get_client()

        resposta = await client.responses.create(
            model=MODEL,
            instructions=INSTRUCTIONS,
            input=[{
                "role": "user",
                "content": conteudo
            }],
            max_output_tokens=1200
        )

        texto = resposta.output_text

        if not texto:
            raise HTTPException(
                status_code=502,
                detail="A IA não devolveu uma resposta. Tenta novamente."
            )

        return {
            "ok": True,
            "resposta": texto,
            "modelo": MODEL
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Erro ao consultar o serviço de IA")
        raise HTTPException(
            status_code=502,
            detail="Não foi possível obter uma resposta da IA. Verifica a configuração e tenta novamente."
        )
