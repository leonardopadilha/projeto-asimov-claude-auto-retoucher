from typing import Literal
from pydantic import BaseModel, Field


class ReportItem(BaseModel):
    description: str = Field(description="A descrição do problema")
    relevance: Literal["ESSENCIAL", "RECOMENDADO", "OPCIONAL"]
    photoshop_technique: str = Field(description="A técnica Photoshop sugerida para resolver o problema")
    query: str = Field(description="A query para a ferramenta Fal AI para encontrar a localização do problema")
    x_point: float = Field(description="A coordenada x do problema. Dada pela ferramenta.")
    y_point: float = Field(description="A coordenada y do problema. Dada pela ferramenta.")

class SkinAnalysisSchema(BaseModel):
    report: list[ReportItem] = Field(description="O relatório de análise da pele")

