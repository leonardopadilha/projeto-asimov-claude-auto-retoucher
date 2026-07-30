# Auto Retoucher

Ferramenta que analisa uma foto com IA e gera um laudo técnico de retoque fotográfico (estilo Photoshop), com pontos marcados diretamente na imagem indicando cada item identificado (olheiras, manchas, brilho, textura de pele, etc.).

## Como funciona

1. O usuário faz upload de uma foto pelo frontend.
2. O backend (FastAPI) salva a imagem e envia para um agente de IA (`agno` + Gemini).
3. O agente analisa a imagem e, para cada problema encontrado, chama a ferramenta `FalPointTool`, que usa a API da Fal AI (modelo `moondream3-preview/point`) para localizar as coordenadas exatas do elemento na foto.
4. O agente retorna um laudo estruturado em JSON (schema `SkinAnalysisSchema`) com descrição, relevância (`ESSENCIAL` / `RECOMENDADO` / `OPCIONAL`), técnica de Photoshop sugerida e coordenadas do ponto.
5. O frontend exibe a imagem com marcadores interativos sobre cada ponto e a lista do laudo.
6. Cada análise é salva em `history/` para consulta posterior sem precisar reprocessar.

## Estrutura do projeto

```
api.py                 # Servidor FastAPI (rotas /, /analyze, /history)
agent_api.py            # Agente de IA que analisa a imagem e monta o laudo
tools/
  fal_point_tool.py      # Tool do agente que localiza pontos na imagem via Fal AI
  models.py               # Schemas Pydantic (SkinAnalysisSchema)
prompts/
  skin.md                 # Prompt de instrução do agente
templates/
  index.html               # Interface web (upload, resultados, histórico)
uploads/                  # Imagens enviadas pelos usuários
history/                  # Resultado das análises já feitas (JSON)
```

## Requisitos

- Python >= 3.13
- Chaves de API configuradas em um arquivo `.env` na raiz do projeto:
  ```
  GOOGLE_API_KEY=...
  FAL_KEY=...
  MOONDREAM_API_KEY=...
  ```

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Executando

```bash
python api.py
```

O servidor sobe em `http://localhost:8000`. Abra essa URL no navegador para usar a interface de upload.

> **Atenção:** rode sempre com o Python do `.venv` (onde as dependências foram instaladas), não com o Python global do sistema.
