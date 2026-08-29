from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.database import Base, engine, get_db
from app.product_service import (
    create_product,
    find_exact_product,
    get_product_by_id,
    list_products,
    find_product_matches,
)
from app.schemas import (
    InventoryResponse,
    ProductCreate,
    ProductMatchRequest,
    ProductMatchResponse,
    ProductResponse,
)
from app.inventory_service import list_inventory


Base.metadata.create_all(bind=engine)


app = FastAPI(title="Smart Fridge API")


DbSession = Annotated[Session, Depends(get_db)]
ProductId = Annotated[int, Path(ge=1)]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get(
    "/inventory",
    response_model=list[InventoryResponse],
)
def get_inventory(db: DbSession):
    return list_inventory(db)


@app.get(
    "/products",
    response_model=list[ProductResponse],
)
def get_products(db: DbSession):
    return list_products(db)



@app.post(
    "/products/match",
    response_model=ProductMatchResponse,
)
def match_products(
    match_data: ProductMatchRequest,
    db: DbSession,
):
    match_type, exact_match, candidates = find_product_matches(
        db,
        match_data,
    )

    return ProductMatchResponse(
        match_type=match_type,
        exact_match=exact_match,
        candidates=candidates,
    )


@app.get(
    "/products/{product_id}",
    response_model=ProductResponse,
)
def get_product(
    product_id: ProductId,
    db: DbSession,
):
    product = get_product_by_id(db, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Produto não encontrado.",
                "product_id": product_id,
            },
        )

    return product


@app.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_product(
    product_data: ProductCreate,
    db: DbSession,
):
    existing_product = find_exact_product(db, product_data)

    if existing_product is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Produto já cadastrado.",
                "product_id": existing_product.id,
                "name": existing_product.name,
                "brand": existing_product.brand,
            },
        )

    try:
        return create_product(db, product_data)

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Os dados do produto violam as restrições do banco.",
        )