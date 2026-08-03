def calculate_score(scores):

    return round(
        sum(scores) / len(scores),
        2
    )


def rate_candidate(score):

    if score >= 9:

        return "Excellent"

    elif score >= 7:

        return "Good"

    elif score >= 5:

        return "Average"

    return "Poor"