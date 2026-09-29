import pytest
from fastapi import HTTPException

from app.api.v1.endpoints import cards as cards_endpoints
from app.schemas.card import AnswerCardListItem, QuestionCardListItem


class TestListQuestions:
    async def test_success(self):
        result = await cards_endpoints.list_questions()
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(q, QuestionCardListItem) for q in result)


class TestGetQuestion:
    async def test_success(self):
        item = cards_endpoints.card_service.list_questions()[0]
        question = await cards_endpoints.get_question(item.id)
        assert question.id == item.id

    async def test_not_found(self):
        with pytest.raises(HTTPException) as exc:
            await cards_endpoints.get_question("does-not-exist")
        assert exc.value.status_code == 404


class TestListAnswers:
    async def test_success(self):
        result = await cards_endpoints.list_answers()
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(a, AnswerCardListItem) for a in result)


class TestGetAnswer:
    async def test_success(self):
        item = cards_endpoints.card_service.list_answers()[0]
        answer = await cards_endpoints.get_answer(item.id)
        assert answer.id == item.id

    async def test_not_found(self):
        with pytest.raises(HTTPException) as exc:
            await cards_endpoints.get_answer("does-not-exist")
        assert exc.value.status_code == 404