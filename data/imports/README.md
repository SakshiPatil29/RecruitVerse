# Import data goes here

This folder is where `scripts/ingest_*.py` expect their input files by
default. It's empty in the shipped project (the source datasets are large
and specific to whoever's running the import) — point the scripts here or
pass `--dir`/`--csv` to a different location.

Expected layout:

```
data/imports/
  livecareer_resumes.csv          # ID, Resume_str, Resume_html, Category
  synthetic_resumes.csv           # name, email, phone, education, years_experience,
                                   # primary_skills, secondary_skills, ...
  relational_54k/
    01_people.csv                 # person_id, name, email, phone, linkedin
    03_education.csv              # person_id, institution, program, start_date, location
    04_experience.csv             # person_id, title, firm, start_date, end_date, location
    05_person_skills.csv          # person_id, skill
```

See the README's "Optional — import large real/synthetic datasets" section
for the commands to run against these.
