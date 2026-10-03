import os
import csv
from datetime import datetime
from collections import Counter

DATA_PATHS = [
    ("real_pdf_dataset", "data/raw_resumes/real/dataset1_pdf_categories"),
    ("synthetic_dataset", "data/raw_resumes/synthetic/synthetic_10000"),
    ("structured_dataset", "data/structured_resumes/dataset1_resume_csv"),
    ("job_descriptions", "data/job_descriptions")
]

OUTPUT_FILE = "data/manifest/dataset_manifest.csv"
SUMMARY_FILE = "data/manifest/dataset_summary.txt"

def get_file_type(filename):
    return os.path.splitext(filename)[1].replace(".", "").lower()

def audit_datasets():
    rows = []
    file_id = 1
    type_counter = Counter()
    source_counter = Counter()

    for source, base_path in DATA_PATHS:
        if not os.path.exists(base_path):
            print(f"Path not found: {base_path}")
            continue

        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file == ".gitkeep":
                    continue

                file_path = os.path.join(root, file)
                file_type = get_file_type(file)
                file_size_kb = round(os.path.getsize(file_path) / 1024, 2)

                rows.append({
                    "file_id": file_id,
                    "file_name": file,
                    "file_type": file_type,
                    "source": source,
                    "file_path": file_path.replace("\\", "/"),
                    "size_kb": file_size_kb,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                type_counter[file_type] += 1
                source_counter[source] += 1
                file_id += 1

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "file_id", "file_name", "file_type", "source",
            "file_path", "size_kb", "created_at"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    with open(SUMMARY_FILE, "w", encoding="utf-8") as file:
        file.write("RecruitVerse Dataset Audit Summary\n")
        file.write("===================================\n\n")
        file.write(f"Total files found: {len(rows)}\n\n")

        file.write("Files by type:\n")
        for file_type, count in type_counter.items():
            file.write(f"- {file_type}: {count}\n")

        file.write("\nFiles by source:\n")
        for source, count in source_counter.items():
            file.write(f"- {source}: {count}\n")

    print("Dataset audit completed.")
    print(f"Total files found: {len(rows)}")
    print(f"Manifest saved at: {OUTPUT_FILE}")
    print(f"Summary saved at: {SUMMARY_FILE}")

if __name__ == "__main__":
    audit_datasets()