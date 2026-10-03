def search_candidate(
        candidates,
        keyword):

    results = []

    for candidate in candidates:

        if keyword.lower() in (
            candidate["resume_name"]
        ).lower():

            results.append(
                candidate
            )

    return results