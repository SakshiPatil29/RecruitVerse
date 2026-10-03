"""
A small, hand-built, hand-labeled candidate set for the evaluation
scripts in this folder.

Why this exists instead of using the real datasets: the Relational 54K /
LiveCareer / synthetic datasets aren't bundled in the repo (they're large
and dropped in locally per the README), so anyone cloning the project
can't reproduce an evaluation without first downloading gigabytes of data.
These 16 candidates are small enough to read in one sitting, cover the
categories used by the evaluation queries below, and includes the exact
"Power BI resume should match a 'data visualization' query" case that
motivated the search fix.

Each candidate has the same shape screening_pipeline.screen_candidates()
and search_candidates.semantic_search() expect: name, skills,
experience_years, raw_text.
"""

CANDIDATES = [
    {
        "name": "Rahul Verma",
        "skills": ["Python", "Pandas", "Statistics", "Tableau", "Excel", "Power BI", "SQL", "NumPy"],
        "experience_years": 3,
        "raw_text": (
            "Data analyst with 3 years of experience building dashboards and reports in "
            "Power BI and Tableau. Strong background in Python, Pandas, NumPy, and SQL for "
            "data cleaning and statistical analysis. Presents insights to stakeholders using "
            "Excel-based reporting and interactive BI dashboards."
        ),
    },
    {
        "name": "Karan Mehta",
        "skills": ["Python", "Statistics", "Tableau", "Excel", "Leadership", "SQL", "Google Analytics"],
        "experience_years": 4,
        "raw_text": (
            "Marketing analyst with 4 years of experience turning campaign data into "
            "actionable insight. Builds Tableau dashboards and Google Analytics reports for "
            "leadership review. Proficient in SQL and Excel for ad-hoc analysis."
        ),
    },
    {
        "name": "Ananya Iyer",
        "skills": ["PySpark", "Python", "Kafka", "Airflow", "Spark", "S3", "AWS", "SQL", "Hadoop"],
        "experience_years": 5,
        "raw_text": (
            "Data engineer with 5 years building large-scale ETL pipelines on Spark and "
            "PySpark, orchestrated with Airflow, streaming through Kafka, and storing on AWS "
            "S3. Experience with the Hadoop ecosystem and SQL-based data warehousing."
        ),
    },
    {
        "name": "Priya Sharma",
        "skills": ["Python", "PostgreSQL", "REST API", "Docker", "Git", "AWS", "SQL", "FastAPI"],
        "experience_years": 3,
        "raw_text": (
            "Backend engineer with 3 years building REST APIs in FastAPI and Python, backed "
            "by PostgreSQL. Containerizes services with Docker, deploys on AWS, and works out "
            "of Git for version control."
        ),
    },
    {
        "name": "Devansh Rao",
        "skills": ["Looker Studio", "SQL", "Python", "Excel", "Statistics"],
        "experience_years": 2,
        "raw_text": (
            "Business intelligence analyst with 2 years of experience building executive "
            "dashboards in Google Looker Studio. Writes SQL for reporting pipelines and uses "
            "Python for statistical summaries shared in Excel."
        ),
    },
    {
        "name": "Sneha Kulkarni",
        "skills": ["React", "JavaScript", "HTML", "CSS", "TypeScript", "Figma", "Tailwind CSS"],
        "experience_years": 3,
        "raw_text": (
            "Frontend engineer with 3 years building responsive web interfaces in React and "
            "TypeScript. Works closely with Figma designs, styles with Tailwind CSS, and "
            "focuses on accessible, pixel-perfect UI."
        ),
    },
    {
        "name": "Arjun Nair",
        "skills": ["AWS", "Docker", "Kubernetes", "Terraform", "CI/CD", "Linux", "Python"],
        "experience_years": 4,
        "raw_text": (
            "DevOps engineer with 4 years managing Kubernetes clusters on AWS, provisioning "
            "infrastructure with Terraform, and building CI/CD pipelines. Strong Linux "
            "administration and Python scripting background."
        ),
    },
    {
        "name": "Meera Pillai",
        "skills": ["Machine Learning", "Python", "TensorFlow", "PyTorch", "Scikit-learn", "Statistics"],
        "experience_years": 4,
        "raw_text": (
            "Machine learning engineer with 4 years developing and deploying models using "
            "TensorFlow, PyTorch, and Scikit-learn. Strong statistics background and Python "
            "for feature engineering and evaluation."
        ),
    },
    {
        "name": "Vikram Singh",
        "skills": ["Java", "Spring Boot", "MySQL", "REST API", "Git", "Microservices"],
        "experience_years": 6,
        "raw_text": (
            "Backend engineer with 6 years building Java microservices on Spring Boot, backed "
            "by MySQL. Designs REST APIs and works in a Git-based CI workflow."
        ),
    },
    {
        "name": "Ishita Bansal",
        "skills": ["Power BI", "DAX", "SQL Server", "Excel", "Data Modeling"],
        "experience_years": 2,
        "raw_text": (
            "BI developer with 2 years building Power BI reports and DAX measures on top of "
            "SQL Server. Handles data modeling and Excel-based ad-hoc analysis for finance "
            "stakeholders."
        ),
    },
    {
        "name": "Rohan Desai",
        "skills": ["Node.js", "Express.js", "MongoDB", "JavaScript", "REST API", "Docker"],
        "experience_years": 3,
        "raw_text": (
            "Backend engineer with 3 years building Node.js and Express.js services backed by "
            "MongoDB. Designs REST APIs and ships them in Docker containers."
        ),
    },
    {
        "name": "Neha Joshi",
        "skills": ["Excel", "VBA", "SQL", "Power BI", "Financial Modeling"],
        "experience_years": 5,
        "raw_text": (
            "Financial analyst with 5 years building Excel/VBA financial models and Power BI "
            "reporting dashboards for leadership. Writes SQL for source data extraction."
        ),
    },
    {
        "name": "Aditya Kapoor",
        "skills": ["Python", "NLP", "spaCy", "Transformers", "Machine Learning"],
        "experience_years": 3,
        "raw_text": (
            "NLP engineer with 3 years building text classification and entity extraction "
            "systems using spaCy and transformer models in Python."
        ),
    },
    {
        "name": "Simran Kaur",
        "skills": ["QlikView", "SQL", "Excel", "Python", "ETL"],
        "experience_years": 3,
        "raw_text": (
            "Reporting analyst with 3 years building QlikView dashboards and ETL pipelines "
            "feeding them. Uses SQL and Excel for validation, Python for automation scripts."
        ),
    },
    {
        "name": "Farhan Ali",
        "skills": ["Angular", "TypeScript", "RxJS", "CSS", "REST API"],
        "experience_years": 2,
        "raw_text": (
            "Frontend engineer with 2 years building Angular applications with RxJS and "
            "TypeScript, consuming REST APIs, styled with CSS."
        ),
    },
    {
        "name": "Ritu Chawla",
        "skills": ["Salesforce", "Apex", "SOQL", "REST API", "Data Migration"],
        "experience_years": 4,
        "raw_text": (
            "Salesforce developer with 4 years writing Apex and SOQL for custom business "
            "logic, integrating via REST APIs, and handling large data migrations."
        ),
    },
]
