from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Product
from app.schemas import ProductCreate


def normalize_for_match(value: str | None) -> str | None:
    if value is None:
        return None

    return " ".join(value.split()).casefold()


def find_exact_product(
    db: Session,
    product_data: ProductCreate,
) -> Product | None:
    products = db.scalars(select(Product)).all()

    target_name = normalize_for_match(product_data.name)
    target_brand = normalize_for_match(product_data.brand)

    for product in products:
        stored_name = normalize_for_match(product.name)
        stored_brand = normalize_for_match(product.brand)

        if stored_name == target_name and stored_brand == target_brand:
            return product

    return None


def create_product(
    db: Session,
    product_data: ProductCreate,
) -> Product:
    product = Product(
        name=product_data.name,
        brand=product_data.brand,
        category=product_data.category,
    )

    try:
        db.add(product)
        db.commit()
        db.refresh(product)

    except IntegrityError:
        db.rollback()
        raise

    return product


def list_products(db: Session) -> list[Product]:
    return list(
        db.scalars(
            select(Product).order_by(Product.name)
        ).all()
    )