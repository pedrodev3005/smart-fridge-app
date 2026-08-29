from app.database import SessionLocal
from app.nutrition_service import (
    NutritionAlreadyExistsError,
    NutritionProductNotFoundError,
    create_nutrition,
)
from app.schemas import NutritionCreateRequest


NUTRITION_SEED: list[tuple[int, dict]] = [
    (
        2,
        {
            "reference_amount": 100,
            "reference_unit": "g",
            "energy_kcal": 64,
            "carbohydrates_g": 15.7,
            "protein_g": 0.29,
            "total_fat_g": 0.49,
            "fiber_g": 2.07,
            "sodium_mg": 0.66,
            "source_name": "TBCA",
            "source_reference": "BRC0023C",
        },
    ),
]


def seed_nutrition() -> None:
    db = SessionLocal()

    try:
        for product_id, nutrition_values in NUTRITION_SEED:
            nutrition_data = NutritionCreateRequest(
                **nutrition_values
            )

            try:
                create_nutrition(
                    db,
                    product_id=product_id,
                    nutrition_data=nutrition_data,
                )

            except NutritionAlreadyExistsError:
                print(
                    f"Produto {product_id}: "
                    "informações nutricionais já cadastradas."
                )

            except NutritionProductNotFoundError as exc:
                print(exc)

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_nutrition()