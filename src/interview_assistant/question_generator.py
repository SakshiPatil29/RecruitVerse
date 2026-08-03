import random


def generate_questions(skills):

    questions = []

    for skill in skills:

        questions.append(
            f"Explain {skill}"
        )

    return questions


def get_random_questions(
        questions,
        count=5):

    return random.sample(
        questions,
        count
    )