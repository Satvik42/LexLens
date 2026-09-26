"""In-process memory of Gemini models that should not be called yet."""


class ModelCooldown:
    def __init__(self, clock) -> None:
        self._clock = clock
        self._until: dict[str, float] = {}

    def allow(self, model: str) -> bool:
        return self._until.get(model, 0.0) <= self._clock()

    def mark(self, model: str, seconds: float) -> None:
        self._until[model] = self._clock() + seconds

    def soonest(self, models: list[str]) -> str:
        return min(models, key=lambda model: self._until.get(model, 0.0))
