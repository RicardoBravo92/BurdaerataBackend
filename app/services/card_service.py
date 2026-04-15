import json
from pathlib import Path
from random import choice

from app.schemas.card import (
    QuestionCard,
    AnswerCard,
    QuestionCardListItem,
    AnswerCardListItem,
)


def _load_cards() -> tuple[list[QuestionCard], list[AnswerCard]]:
    path = Path(__file__).parent.parent / "core" / "cards_data.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    questions = [QuestionCard(**q) for q in data["questions"]]
    answers = [AnswerCard(**a) for a in data["answers"]]
    return questions, answers


class CardService:
    def __init__(self):
        self._questions: list[QuestionCard] = []
        self._answers: list[AnswerCard] = []
        self._load()

    def _load(self):
        self._questions, self._answers = _load_cards()

    def get_question_by_id(self, card_id: str) -> QuestionCard | None:
        for q in self._questions:
            if q.id == card_id:
                return q
        return None

    def get_answer_by_id(self, card_id: str) -> AnswerCard | None:
        for a in self._answers:
            if a.id == card_id:
                return a
        return None

    def list_questions(self) -> list[QuestionCardListItem]:
        return [
            QuestionCardListItem(id=q.id, blank_count=q.blank_count)
            for q in self._questions
        ]

    def list_answers(self) -> list[AnswerCardListItem]:
        return [AnswerCardListItem(id=a.id) for a in self._answers]

    def get_random_question(self) -> QuestionCard:
        return choice(self._questions)

    def get_random_answer(self) -> AnswerCard:
        return choice(self._answers)

    def get_random_answers(self, count: int) -> list[AnswerCard]:
        import random

        return random.sample(self._answers, min(count, len(self._answers)))

    def get_question_text(self, card_id: str) -> str | None:
        q = self.get_question_by_id(card_id)
        return q.text if q else None

    def get_answer_text(self, card_id: str) -> str | None:
        a = self.get_answer_by_id(card_id)
        return a.text if a else None

    @property
    def question_count(self) -> int:
        return len(self._questions)

    @property
    def answer_count(self) -> int:
        return len(self._answers)


card_service = CardService()
