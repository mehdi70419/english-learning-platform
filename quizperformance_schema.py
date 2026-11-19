from pydantic import BaseModel


class PublicQuizPerformance(BaseModel):
    number_of_questions : int
    number_of_questions_answered_by_user : int
    number_of_correct_answers_by_user : int
    number_of_incorrect_answers_by_user: int
    number_of_unanswered_questions : int
    percentage_of_correct_answers : float| None
    number_of_true_false_questions : int
    number_of_true_false_questions_answered_by_user : int
    number_of_true_false_questions_answered_by_user_correctly : int
    number_of_true_false_questions_answered_by_user_incorrectly : int
    number_of_multiple_choice_questions : int
    number_of_multiple_choice_questions_answered_by_user : int
    number_of_multiple_choice_questions_answered_by_user_correctly : int
    number_of_multiple_choice_questions_answered_by_user_incorrectly : int
    number_of_fill_in_the_blank_questions : int
    number_of_fill_in_the_blank_questions_answered_by_user : int
    number_of_fill_in_the_blank_questions_answered_by_user_correctly : int
    number_of_fill_in_the_blank_questions_answered_by_user_incorrectly : int