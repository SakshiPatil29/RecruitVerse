import os

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

RESUME_FOLDER = os.path.join(
    BASE_DIR,
    "data",
    "parsed_resumes",
    "raw_text"
)


def load_resumes():

    resumes = []

    for file in os.listdir(
            RESUME_FOLDER):

        if file.endswith(".txt"):

            path = os.path.join(
                RESUME_FOLDER,
                file
            )

            with open(
                path,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as f:

                text = f.read()

            resumes.append({

                "resume_name":
                file,

                "text":
                text
            })

    return resumes