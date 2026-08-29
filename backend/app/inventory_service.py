from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Inventory
from app.product_service import get_product_by_id


def list_inventory(db: Session) -> list[Inventory]:
    return list(
        db.scalars(
            select(Inventory).order_by(Inventory.product_id)
        ).all()
    )


def get_inventory_by_product_id(
    db: Session,
    product_id: int,
) -> Inventory | None:
    return db.scalar(
        select(Inventory).where(
            Inventory.product_id == product_id
        )
    )


class InventoryProductNotFoundError(Exception):
    pass


class InvalidInventoryQuantityError(Exception):
    pass


def add_inventory_entry(
    db: Session,
    product_id: int,
    quantity: int,
) -> Inventory:
    if (
        isinstance(product_id, bool)
        or not isinstance(product_id, int)
        or product_id < 1
    ):
        raise InventoryProductNotFoundError(
            "O ID do produto deve ser um número inteiro maior ou igual a 1."
        )

    if (
        isinstance(quantity, bool)
        or not isinstance(quantity, int)
        or quantity < 1
    ):
        raise InvalidInventoryQuantityError(
            "A quantidade deve ser um número inteiro maior ou igual a 1."
        )

    product = get_product_by_id(db, product_id)

    if product is None:
        raise InventoryProductNotFoundError(
            f"Produto {product_id} não encontrado."
        )

    inventory_item = get_inventory_by_product_id(
        db,
        product_id,
    )

    if inventory_item is None:
        inventory_item = Inventory(
            product_id=product_id,
            quantity=quantity,
        )
        db.add(inventory_item)
    else:
        inventory_item.quantity += quantity

    db.flush()

    return inventory_item