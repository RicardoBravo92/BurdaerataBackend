from fastapi import APIRouter, HTTPException, status

from app.schemas.card import (
    AnswerCardListItem,
    AnswerCardRead,
    QuestionCardListItem,
    QuestionCardRead,
)
from app.services.card_service import card_service

router = APIRouter()


@router.get("/questions", response_model=list[QuestionCardListItem])
async def list_questions() -> list[QuestionCardListItem]:
    questions = card_service.list_questions()
    return [QuestionCardListItem(id=q.id, blank_count=q.blank_count) for q in questions]


@router.get("/questions/{card_id}", response_model=QuestionCardRead)
async def get_question(card_id: str) -> QuestionCardRead:
    question = card_service.get_question_by_id(card_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question card not found"
        )
    return QuestionCardRead(id=question.id, text=question.text, blank_count=question.blank_count)


@router.get("/answers", response_model=list[AnswerCardListItem])
async def list_answers() -> list[AnswerCardListItem]:
    answers = card_service.list_answers()
    return [AnswerCardListItem(id=a.id) for a in answers]


@router.get("/answers/{card_id}", response_model=AnswerCardRead)
async def get_answer(card_id: str) -> AnswerCardRead:
    answer = card_service.get_answer_by_id(card_id)
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Answer card not found"
        )
    return AnswerCardRead(id=answer.id, text=answer.text)