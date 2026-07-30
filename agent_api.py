import logging
import os
import json
import re

from agno.agent import Agent
from agno.media import Image
from agno.models.google import Gemini
from tools.fal_point_tool import FalPointTool
from tools.models import SkinAnalysisSchema
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("agent_api")


def get_agent():
    return Agent(
        model=Gemini(id="gemini-3-flash-preview"),
        tools=[FalPointTool()],
        description=(
            "Você é um especialista em retoque fotográfico. "
            "Sua tarefa é analisar imagens e retornar dados estruturados em JSON."
        ),
    )


def extract_json(text: str) -> dict | None:
    """Extrai o primeiro objeto JSON válido de uma string (com ou sem markdown)."""
    # Bloco ```json ... ```
    m = re.search(r'```json\s*([\s\S]*?)\s*```', text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError as e:
            log.warning("Falha ao parsear bloco ```json: %s", e)

    # Bloco ``` ... ``` genérico
    m = re.search(r'```\s*([\s\S]*?)\s*```', text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError as e:
            log.warning("Falha ao parsear bloco ```: %s", e)

    # Primeiro objeto { ... } solto no texto
    m = re.search(r'\{[\s\S]*\}', text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError as e:
            log.warning("Falha ao parsear objeto JSON solto: %s", e)

    # Tentativa direta
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return None


def analyze_image(image_path: str) -> SkinAnalysisSchema:
    log.info("=== Iniciando análise: %s ===", image_path)

    agent = get_agent()

    with open("prompts/skin.md", "r", encoding="utf-8") as f:
        skin_prompt = f.read().format(img_path=image_path)

    prompt = f"""
{skin_prompt}

---

IMPORTANTE — siga estas regras à risca:

1. Para CADA item identificado no laudo, você DEVE chamar a ferramenta
   `find_points_in_image` passando `image_path="{image_path}"` e uma `prompt`
   descrevendo o elemento a localizar (ex: "olheiras", "manchas na testa").
   Sem essa chamada o item NÃO terá coordenadas válidas.

2. Após obter TODOS os pontos, retorne SOMENTE um objeto JSON válido, sem
   markdown, sem explicações, sem texto extra — apenas o JSON puro.

3. Esquema obrigatório:
{{
  "report": [
    {{
      "description": "descrição detalhada do problema",
      "relevance": "ESSENCIAL" | "RECOMENDADO" | "OPCIONAL",
      "photoshop_technique": "técnica Photoshop sugerida",
      "query": "query usada na ferramenta",
      "x_point": <float entre 0 e 1>,
      "y_point": <float entre 0 e 1>
    }}
  ]
}}
"""

    log.info("Prompt enviado ao agente (primeiros 400 chars):\n%s…", prompt[:400])

    try:
        response = agent.run(
            prompt,
            images=[Image(filepath=image_path)],
        )

        # ── Log de todas as mensagens da conversa ──────────────────────────
        log.info("--- Mensagens da conversa ---")
        if hasattr(response, "messages") and response.messages:
            for i, msg in enumerate(response.messages):
                role = getattr(msg, "role", "?")
                content = getattr(msg, "content", "")
                # Tool calls
                tool_calls = getattr(msg, "tool_calls", None)
                if tool_calls:
                    for tc in tool_calls:
                        fn   = getattr(tc, "function", None)
                        name = getattr(fn, "name", "?") if fn else "?"
                        args = getattr(fn, "arguments", "?") if fn else "?"
                        log.info("  [msg %d] TOOL CALL  → %s(%s)", i, name, str(args)[:200])
                # Tool results
                tool_results = getattr(msg, "tool_results", None)
                if tool_results:
                    for tr in tool_results:
                        log.info("  [msg %d] TOOL RESULT → %s", i, str(tr)[:300])
                if content:
                    snippet = str(content)[:300].replace("\n", " ")
                    log.info("  [msg %d] %s: %s", i, role.upper(), snippet)
        else:
            log.warning("response.messages não disponível ou vazio")

        # ── Conteúdo final ─────────────────────────────────────────────────
        content = response.content
        log.info("--- Conteúdo final do agente ---")
        log.info("Tipo: %s", type(content).__name__)
        if isinstance(content, str):
            log.info("Conteúdo (primeiros 800 chars):\n%s", content[:800])
        else:
            log.info("Conteúdo (repr): %s", repr(content)[:400])

        # ── Parse JSON ────────────────────────────────────────────────────
        if isinstance(content, str):
            json_data = extract_json(content)
            if json_data:
                log.info("JSON extraído com sucesso. Chaves: %s", list(json_data.keys()))
                report = json_data.get("report", [])
                log.info("Itens no report: %d", len(report))
                for idx, item in enumerate(report):
                    log.info(
                        "  item[%d] relevance=%s x=%.3f y=%.3f desc=%s",
                        idx,
                        item.get("relevance", "?"),
                        item.get("x_point", -1),
                        item.get("y_point", -1),
                        str(item.get("description", ""))[:60],
                    )
                try:
                    result = SkinAnalysisSchema(**json_data)
                    log.info("SkinAnalysisSchema criado com %d itens.", len(result.report))
                    return result
                except Exception as ve:
                    log.error("Erro ao validar SkinAnalysisSchema: %s", ve)
            else:
                log.error(
                    "Não foi possível extrair JSON da resposta.\nConteúdo completo:\n%s",
                    content,
                )

        if isinstance(content, SkinAnalysisSchema):
            log.info("Resposta já era SkinAnalysisSchema — %d itens.", len(content.report))
            return content

        log.error("Retornando report vazio — nenhum dado válido obtido.")
        return SkinAnalysisSchema(report=[])

    except Exception as e:
        log.exception("Exceção durante agent.run: %s", e)
        return SkinAnalysisSchema(report=[])


if __name__ == "__main__":
    try:
        result = analyze_image("images/img2.jpeg")
        print(result.model_dump_json(indent=2))
    except Exception as e:
        log.exception("Erro no teste direto: %s", e)
