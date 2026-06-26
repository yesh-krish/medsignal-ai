from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.drug import Drug


SEED_DRUGS = [
    {
        "rxcui": "161",
        "input_name": "acetaminophen",
        "normalized_name": "Acetaminophen",
        "synonym": "Paracetamol",
        "tty": "IN",
    },
    {
        "rxcui": "5640",
        "input_name": "ibuprofen",
        "normalized_name": "Ibuprofen",
        "synonym": None,
        "tty": "IN",
    },
    {
        "rxcui": "6809",
        "input_name": "metformin",
        "normalized_name": "Metformin",
        "synonym": None,
        "tty": "IN",
    },
    {
        "rxcui": "83367",
        "input_name": "atorvastatin",
        "normalized_name": "Atorvastatin",
        "synonym": None,
        "tty": "IN",
    },
]


def seed_drugs() -> None:
    with SessionLocal() as db:
        created = 0
        updated = 0

        for seed in SEED_DRUGS:
            drug = db.scalar(select(Drug).where(Drug.rxcui == seed["rxcui"]))
            if drug is None:
                db.add(Drug(**seed))
                created += 1
                continue

            for key, value in seed.items():
                setattr(drug, key, value)
            updated += 1

        db.commit()
        print(f"Seed complete: {created} created, {updated} updated.")


if __name__ == "__main__":
    seed_drugs()
