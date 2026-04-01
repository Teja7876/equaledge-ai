import json
import os

LEGAL_DIR = "data_storage/raw/domains/legal"

METADATA_KEYS = {
    "canonical_id",
    "source_url",
    "issuing_authority",
    "publication_date",
    "last_verified_date",
    "verification_status",
    "source_type"
}


def fix_file(path):

    with open(path, "r") as f:
        data = json.load(f)

    definitions = {}
    metadata = {}

    for key, value in data.items():

        if key in METADATA_KEYS:
            metadata[key] = value
        else:
            definitions[key] = value

    fixed = {
        "definitions": definitions,
        "metadata": metadata
    }

    with open(path, "w") as f:
        json.dump(fixed, f, indent=2)

    print("Fixed:", path)


def main():

    for file in os.listdir(LEGAL_DIR):

        if file.endswith(".json"):

            path = os.path.join(LEGAL_DIR, file)

            try:
                fix_file(path)
            except Exception as e:
                print("Error:", file, e)


if __name__ == "__main__":
    main()
