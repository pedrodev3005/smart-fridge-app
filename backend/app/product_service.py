import unicodedata
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Product
from app.schemas import ProductCreate
from app.enums import ProductMatchType
from app.schemas import ProductCreate, ProductMatchRequest


def normalize_for_match(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = " ".join(value.split()).casefold()
    normalized = unicodedata.normalize("NFKD", normalized)

    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )


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


def get_product_by_id(
    db: Session,
    product_id: int,
) -> Product | None:
    return db.get(Product, product_id)


def find_product_matches(
    db: Session,
    match_data: ProductMatchRequest,
) -> tuple[ProductMatchType, Product | None, list[Product]]:
    products = db.scalars(select(Product)).all()

    target_name = normalize_for_match(match_data.name)
    target_brand = normalize_for_match(match_data.brand)

    same_name_products = [
        product
        for product in products
        if normalize_for_match(product.name) == target_name
    ]

    if not same_name_products:
        return ProductMatchType.NONE, None, []

    same_name_products.sort(
        key=lambda product: (
            normalize_for_match(product.brand) or "",
            product.id,
        )
    )

    if target_brand is not None:
        exact_match = next(
            (
                product
                for product in same_name_products
                if normalize_for_match(product.brand) == target_brand
            ),
            None,
        )

        if exact_match is not None:
            return ProductMatchType.EXACT, exact_match, []

    if len(same_name_products) == 1:
        return (
            ProductMatchType.SINGLE_CANDIDATE,
            None,
            same_name_products,
        )

    return (
        ProductMatchType.MULTIPLE_CANDIDATES,
        None,
        same_name_products,
    )