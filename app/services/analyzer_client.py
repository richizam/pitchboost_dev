# analyzer_client.py
from app.schemas.analyze import AnalyzeResponse, Scores

class AnalyzerClient:
    async def analyze(self, *, user_id: str, scenario: str, audio_url: str) -> AnalyzeResponse:
        # Mock para CP1. Despues Reemplazo por httpx a AI Platform real en CP2.
        scores = Scores(clarity=80, structure=72, persuasion=76, total=76)
        return AnalyzeResponse(
            scores=scores,
            strengths=["Чёткое интро", "Понятная проблема"],
            improvements=["Добавить доказательства", "Усилить призыв к действию"],
            rewritten_pitch_60s=(
                "Здравствуйте! Меня зовут ..., мы решаем проблему ... "
                "Наше решение даёт ... Призыв к действию: ..."
            ),
        )

analyzer_client = AnalyzerClient()
