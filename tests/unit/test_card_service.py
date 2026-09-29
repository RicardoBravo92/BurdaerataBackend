from app.services.card_service import card_service


def _first_question_with_blank():
    for item in card_service.list_questions():
        if item.blank_count >= 1:
            return card_service.get_question_by_id(item.id)
    raise AssertionError("No question with a blank found in the card pool")


def _first_answer_text():
    return card_service.get_answer_by_id(card_service.list_answers()[0].id).text


def test_question_count_positive():
    assert card_service.question_count > 0


def test_answer_count_positive():
    assert card_service.answer_count > 0


def test_get_question_by_id_missing():
    assert card_service.get_question_by_id("does-not-exist") is None


def test_get_answer_by_id_missing():
    assert card_service.get_answer_by_id("does-not-exist") is None


def test_get_question_text_missing():
    assert card_service.get_question_text("does-not-exist") is None


def test_get_answer_text_missing():
    assert card_service.get_answer_text("does-not-exist") is None


def test_compose_answer_text_replaces_single_blank():
    question = _first_question_with_blank()
    answer_id = card_service.list_answers()[0].id
    answer_text = card_service.get_answer_text(answer_id)

    composed = card_service.compose_answer_text(question.id, [answer_id])

    assert "_____" not in composed
    assert question.text.replace("_____", answer_text, 1) == composed


def test_compose_answer_text_replaces_all_blanks():
    question = _first_question_with_blank()
    answer_ids = [a.id for a in card_service.list_answers()[: question.blank_count]]

    composed = card_service.compose_answer_text(question.id, answer_ids)

    assert "_____" not in composed
    for aid in answer_ids:
        assert card_service.get_answer_text(aid) in composed


def test_compose_answer_text_unknown_question():
    assert card_service.compose_answer_text("does-not-exist", ["a1"]) == ""


def test_compose_answer_text_ignores_missing_answers():
    question = _first_question_with_blank()
    composed = card_service.compose_answer_text(question.id, ["does-not-exist"])
    assert composed == question.text


def test_get_random_answers_no_duplicates():
    answers = card_service.get_random_answers(50)
    ids = [a.id for a in answers]
    assert len(ids) == 50
    assert len(set(ids)) == 50


def test_get_random_answers_above_pool_size():
    answers = card_service.get_random_answers(card_service.answer_count + 100)
    assert len(answers) == card_service.answer_count


def test_get_random_answer_from_pool():
    assert card_service.get_random_answer() in card_service._answers