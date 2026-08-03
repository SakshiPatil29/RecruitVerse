def get_top_candidates(
        candidates,
        n):

    if n <= 0:

        return []

    return candidates[:n]

def filter_by_score(
        candidates,
        min_score):

    filtered = []

    for candidate in candidates:

        if candidate[
            "final_score"
        ] >= min_score:

            filtered.append(
                candidate
            )

    return filtered

def filter_by_skill(
        candidates,
        skill):

    filtered = []

    for candidate in candidates:

        skills = [

            s.lower()

            for s in candidate[
                "matched_skills"
            ]
        ]

        if skill.lower() in skills:

            filtered.append(
                candidate
            )

    return filtered