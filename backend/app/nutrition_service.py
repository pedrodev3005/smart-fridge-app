from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Nutrition
from app.product_service import get_product_by_id
from app.schemas import NutritionCreateRequest

def get_nutrition_by_product_id(
    db: Session,
    product_id: int,
) -> Nutrition | None:
    return db.scalar(
        select(Nutrition)
        .options(selectinload(Nutrition.product))
        .where(Nutrition.product_id == product_id)
    )


class NutritionProductNotFoundError(Exception):
    pass


class NutritionAlreadyExistsError(Exception):
    pass


def create_nutrition(
    db: Session,
    product_id: int,
    nutrition_data: NutritionCreateRequest,
) -> Nutrition:
    product = get_product_by_id(
        db,
        product_id,
    )

    if product is None:
        raise NutritionProductNotFoundError(
            f"Produto {product_id} não encontrado."
        )

    existing_nutrition = get_nutrition_by_product_id(
        db,
        product_id,
    )

    if existing_nutrition is not None:
        raise NutritionAlreadyExistsError(
            f"O produto {product_id} já possui informações nutricionais."
        )

    nutrition = Nutrition(
        product_id=product_id,
        **nutrition_data.model_dump(),
    )

    db.add(nutrition)
    db.flush()

    return nutrition