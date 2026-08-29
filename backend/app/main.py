from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.database import Base, engine, get_db
from app.product_service import create_product, find_exact_product
from app.schemas import ProductCreate, ProductResponse


Base.metadata.create_all(bind=engine)


app = FastAPI(title="Smart Fridge API")


DbSession = Annotated[Session, Depends(get_db)]


@app.get("/health")
def health():
    return {"status": "ok"}


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