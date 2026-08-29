from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.event_service import create_event

from app.enums import InventoryMovementType
from app.models import Inventory
from app.product_service import get_product_by_id


def list_inventory(db: Session) -> list[Inventory]:
    return list(
        db.scalars(
            select(Inventory)
            .options(selectinload(Inventory.product))
            .order_by(Inventory.product_id)
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


class InvalidProductIdError(Exception):
    pass


class InvalidInventoryQuantityError(Exception):
    pass


class InventoryProductNotFoundError(Exception):
    pass


class InventoryItemNotFoundError(Exception):
    pass


class InsufficientInventoryError(Exception):
    pass


class InvalidInventoryMovementTypeError(Exception):
    pass


def _validate_product_id(product_id: int) -> None:
    if (
        isinstance(product_id, bool)
        or not isinstance(product_id, int)
        or product_id < 1
    ):
        raise InvalidProductIdError(
            "O ID do produto deve ser um número inteiro maior ou igual a 1."
        )


def _validate_quantity(quantity: int) -> None:
    if (
        isinstance(quantity, bool)
        or not isinstance(quantity, int)
        or quantity < 1
    ):
        raise InvalidInventoryQuantityError(
            "A quantidade deve ser um número inteiro maior ou igual a 1."
        )


def _validate_movement_type(
    movement_type: InventoryMovementType,
) -> None:
    if not isinstance(
        movement_type,
        InventoryMovementType,
    ):
        raise InvalidInventoryMovementTypeError(
            "O tipo de movimentação deve ser 'entry' ou 'exit'."
        )
    

def add_inventory_entry(
    db: Session,
    product_id: int,
    quantity: int,
) -> Inventory:
    _validate_product_id(product_id)
    _validate_quantity(quantity)

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


def remove_inventory_exit(
    db: Session,
    product_id: int,
    quantity: int,
) -> Inventory | None:
    _validate_product_id(product_id)
    _validate_quantity(quantity)

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
        raise InventoryItemNotFoundError(
            f"Produto {product_id} não está presente no inventário."
        )

    if quantity > inventory_item.quantity:
        raise InsufficientInventoryError(
            (
                f"Quantidade insuficiente para o produto {product_id}. "
                f"Disponível: {inventory_item.quantity}. "
                f"Solicitado: {quantity}."
            )
        )

    if quantity == inventory_item.quantity:
        db.delete(inventory_item)
        db.flush()
        return None

    inventory_item.quantity -= quantity
    db.flush()

    return inventory_item


def process_inventory_movement(
    db: Session,
    product_id: int,
    movement_type: InventoryMovementType,
    quantity: int,
) -> Inventory | None:
    _validate_movement_type(movement_type)

    if movement_type == InventoryMovementType.ENTRY:
        return add_inventory_entry(
            db,
            product_id,
            quantity,
        )

    return remove_inventory_exit(
        db,
        product_id,
        quantity,
    )


def process_inventory_movement_with_event(
    db: Session,
    product_id: int,
    movement_type: InventoryMovementType,
    quantity: int,
    event_timestamp: datetime | None = None,
):
    inventory_item = process_inventory_movement(
        db,
        product_id=product_id,
        movement_type=movement_type,
        quantity=quantity,
    )

    event = create_event(
        db,
        product_id=product_id,
        event_type=movement_type,
        quantity=quantity,
        timestamp=event_timestamp,
    )

    return inventory_item, event