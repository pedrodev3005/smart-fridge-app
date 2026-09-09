from typing import Annotated

from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, FastAPI, HTTPException, Path, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


from app import models
from app.enums import UnknownProductStatus
from app.event_service import list_events
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
    InventoryMovementRequest,
    InventoryMovementResponse,
    ErrorResponse,
    EventResponse,
    UnknownProductCreateRequest,
    UnknownProductResponse,
    UnknownProductResolveRequest,
    NutritionResponse,
    NutritionCreateRequest,
)
from app.inventory_service import (
    InsufficientInventoryError,
    InvalidInventoryMovementTypeError,
    InvalidInventoryQuantityError,
    InvalidProductIdError,
    InventoryItemNotFoundError,
    InventoryProductNotFoundError,
    list_inventory,
    process_inventory_movement_with_event,
)
from app.unknown_product_service import (
    UnknownProductAlreadyReviewedError,
    UnknownProductNotFoundError,
    create_unknown_product,
    dismiss_unknown_product,
    get_unknown_product_by_id,
    list_unknown_products,
    resolve_unknown_product,
)
from app.nutrition_service import (
    NutritionAlreadyExistsError,
    NutritionProductNotFoundError,
    create_nutrition,
    get_nutrition_by_product_id,
)


Base.metadata.create_all(bind=engine)


app = FastAPI(title="Smart Fridge API")


allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DbSession = Annotated[Session, Depends(get_db)]
ProductId = Annotated[int, Path(ge=1)]
UnknownProductId = Annotated[int, Path(ge=1)]


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
    "/events",
    response_model=list[EventResponse],
)
def get_events(db: DbSession):
    return list_events(db)


@app.post(
    "/unknown-products",
    response_model=UnknownProductResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Dados do produto desconhecido inválidos.",
        },
    },
)
def register_unknown_product(
    unknown_data: UnknownProductCreateRequest,
    db: DbSession,
):
    try:
        unknown_product = create_unknown_product(
            db,
            image_path=unknown_data.image_path,
            movement_type=unknown_data.movement_type,
            quantity=unknown_data.quantity,
        )

        db.commit()
        db.refresh(unknown_product)

        return unknown_product

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Os dados do produto desconhecido violam as restrições do banco.",
        )

    except Exception:
        db.rollback()
        raise


@app.get(
    "/unknown-products",
    response_model=list[UnknownProductResponse],
)
def get_unknown_products(
    db: DbSession,
    status_filter: UnknownProductStatus | None = Query(
        default=None,
        alias="status",
    ),
):
    return list_unknown_products(
        db,
        status=status_filter,
    )


@app.get(
    "/unknown-products/{unknown_product_id}",
    response_model=UnknownProductResponse,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Produto desconhecido não encontrado.",
        },
    },
)
def get_unknown_product(
    unknown_product_id: UnknownProductId,
    db: DbSession,
):
    unknown_product = get_unknown_product_by_id(
        db,
        unknown_product_id,
    )

    if unknown_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Produto desconhecido {unknown_product_id} não encontrado.",
        )

    return unknown_product


@app.post(
    "/unknown-products/{unknown_product_id}/dismiss",
    response_model=UnknownProductResponse,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Produto desconhecido não encontrado.",
        },
        409: {
            "model": ErrorResponse,
            "description": "Produto desconhecido já foi revisado.",
        },
    },
)
def dismiss_unknown_product_review(
    unknown_product_id: UnknownProductId,
    db: DbSession,
):
    try:
        unknown_product = dismiss_unknown_product(
            db,
            unknown_product_id,
        )

        db.commit()
        db.refresh(unknown_product)

        return unknown_product

    except UnknownProductNotFoundError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    except UnknownProductAlreadyReviewedError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A revisão viola uma restrição do banco de dados.",
        )

    except Exception:
        db.rollback()
        raise


@app.post(
    "/unknown-products/{unknown_product_id}/resolve",
    response_model=UnknownProductResponse,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Produto desconhecido ou produto de destino não encontrado.",
        },
        409: {
            "model": ErrorResponse,
            "description": "Produto já revisado ou movimentação incompatível com o inventário.",
        },
    },
)
def resolve_unknown_product_review(
    unknown_product_id: UnknownProductId,
    resolution_data: UnknownProductResolveRequest,
    db: DbSession,
):
    try:
        unknown_product, _inventory_item, _event = resolve_unknown_product(
            db,
            unknown_product_id=unknown_product_id,
            resolved_product_id=resolution_data.resolved_product_id,
            resolved_quantity=resolution_data.resolved_quantity,
        )

        db.commit()

        db.refresh(unknown_product)
        db.refresh(
            unknown_product,
            attribute_names=["resolved_product"],
        )

        return unknown_product

    except UnknownProductNotFoundError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    except UnknownProductAlreadyReviewedError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    except InventoryProductNotFoundError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    except InventoryItemNotFoundError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    except InsufficientInventoryError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A resolução viola uma restrição do banco de dados.",
        )

    except Exception:
        db.rollback()
        raise

    
@app.post(
    "/inventory/movements",
    response_model=InventoryMovementResponse,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Dados de movimentação inválidos.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Produto não encontrado.",
        },
        409: {
            "model": ErrorResponse,
            "description": "Movimentação incompatível com o estado atual do inventário.",
        },
    },
)
def create_inventory_movement(
    movement_data: InventoryMovementRequest,
    db: DbSession,
):
    try:
        inventory_item, _event = process_inventory_movement_with_event(
            db,
            product_id=movement_data.product_id,
            movement_type=movement_data.movement_type,
            quantity=movement_data.quantity,
        )

        final_quantity = (
            inventory_item.quantity
            if inventory_item is not None
            else 0
        )

        db.commit()

        if inventory_item is not None:
            db.refresh(inventory_item)

        inventory_response = (
            InventoryResponse.model_validate(inventory_item)
            if inventory_item is not None
            else None
        )

        return InventoryMovementResponse(
            product_id=movement_data.product_id,
            movement_type=movement_data.movement_type,
            quantity_moved=movement_data.quantity,
            final_quantity=final_quantity,
            inventory_item=inventory_response,
        )

    except InvalidProductIdError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except InvalidInventoryQuantityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except InvalidInventoryMovementTypeError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except InventoryProductNotFoundError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    except InventoryItemNotFoundError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    except InsufficientInventoryError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A movimentação viola uma restrição do banco de dados.",
        )

    except Exception:
        db.rollback()
        raise

    
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


@app.get(
    "/products/{product_id}/nutrition",
    response_model=NutritionResponse,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Informações nutricionais não encontradas.",
        },
    },
)
def get_product_nutrition(
    product_id: ProductId,
    db: DbSession,
):
    product = get_product_by_id(
        db,
        product_id,
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Produto {product_id} não encontrado.",
        )

    nutrition = get_nutrition_by_product_id(
        db,
        product_id,
    )

    if nutrition is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"O produto {product_id} não possui informações nutricionais cadastradas.",
        )

    return nutrition


@app.post(
    "/products/{product_id}/nutrition",
    response_model=NutritionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Produto não encontrado.",
        },
        409: {
            "model": ErrorResponse,
            "description": "Informações nutricionais já cadastradas.",
        },
    },
)
def register_product_nutrition(
    product_id: ProductId,
    nutrition_data: NutritionCreateRequest,
    db: DbSession,
):
    try:
        nutrition = create_nutrition(
            db,
            product_id=product_id,
            nutrition_data=nutrition_data,
        )

        db.commit()
        db.refresh(nutrition)

        return nutrition

    except NutritionProductNotFoundError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except NutritionAlreadyExistsError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    

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