from datetime import datetime, timezone

from app.enums import ProductMatchType, VisionConfidence
from app.models import Product, UnknownProduct, VisionInteraction
from app.unknown_product_service import create_unknown_product
from app.product_service import find_product_matches
from app.inventory_service import (
    InsufficientInventoryError,
    InventoryItemNotFoundError,
    process_inventory_movement_with_event,
)
from app.schemas import (
    ProductMatchRequest,
    VisionEventInput,
    VisionInteractionRequest,
    VisionProductInput,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

class VisionInteractionAlreadyProcessedError(Exception):
    pass


def get_vision_interaction_by_external_id(
    db: Session,
    interaction_id: str,
) -> VisionInteraction | None:
    return db.scalar(
        select(VisionInteraction).where(
            VisionInteraction.interaction_id == interaction_id
        )
    )


def create_vision_interaction(
    db: Session,
    interaction_id: str,
    timestamp: datetime,
) -> VisionInteraction:
    existing_interaction = get_vision_interaction_by_external_id(
        db,
        interaction_id,
    )

    if existing_interaction is not None:
        raise VisionInteractionAlreadyProcessedError(
            f"A interação {interaction_id} já foi processada."
        )

    if (
        timestamp.tzinfo is not None
        and timestamp.utcoffset() is not None
    ):
        timestamp = timestamp.astimezone(
            timezone.utc
        ).replace(tzinfo=None)

    interaction = VisionInteraction(
        interaction_id=interaction_id,
        timestamp=timestamp,
    )

    db.add(interaction)
    db.flush()

    return interaction


def find_product_for_vision(
    db: Session,
    vision_product: VisionProductInput | None,
) -> Product | None:
    if vision_product is None:
        return None

    if vision_product.name is None:
        return None

    match_request = ProductMatchRequest(
        name=vision_product.name,
        brand=vision_product.brand,
    )

    match_type, exact_match, candidates = find_product_matches(
        db,
        match_request,
    )

    if match_type == ProductMatchType.EXACT:
        return exact_match

    if (
        match_type == ProductMatchType.SINGLE_CANDIDATE
        and vision_product.brand is None
        and len(candidates) == 1
    ):
        return candidates[0]

    return None


def can_process_vision_event_automatically(
    vision_event: VisionEventInput,
    matched_product: Product | None,
) -> bool:
    if vision_event.requires_confirmation:
        return False

    if matched_product is None:
        return False

    if vision_event.confidence != VisionConfidence.HIGH:
        return False

    return True


def create_pending_from_vision_event(
    db: Session,
    vision_event: VisionEventInput,
    timestamp: datetime,
    vision_interaction_id: int,
) -> UnknownProduct:
    product_data = vision_event.product

    detected_name = None
    detected_brand = None
    detected_category = None

    if product_data is not None:
        detected_name = product_data.name
        detected_brand = product_data.brand
        detected_category = product_data.category

    return create_unknown_product(
        db,
        image_path=None,
        movement_type=vision_event.movement_type,
        quantity=vision_event.quantity,
        detected_at=timestamp,
        detected_name=detected_name,
        detected_brand=detected_brand,
        detected_category=detected_category,
        confidence=vision_event.confidence,
        vision_interaction_id=vision_interaction_id,
    )


def process_single_vision_event(
    db: Session,
    vision_event: VisionEventInput,
    timestamp: datetime,
    vision_interaction_id: int,
):
    matched_product = find_product_for_vision(
        db,
        vision_event.product,
    )

    if can_process_vision_event_automatically(
        vision_event,
        matched_product,
    ):
        try:
            inventory_item, event = (
                process_inventory_movement_with_event(
                    db,
                    product_id=matched_product.id,
                    movement_type=vision_event.movement_type,
                    quantity=vision_event.quantity,
                    event_timestamp=timestamp,
                    vision_interaction_id=vision_interaction_id,
                )
            )

            return {
                "status": "processed",
                "product_id": matched_product.id,
                "inventory_item": inventory_item,
                "event": event,
                "pending": None,
            }

        except (
            InventoryItemNotFoundError,
            InsufficientInventoryError,
        ):
            pass

    pending = create_pending_from_vision_event(
        db,
        vision_event,
        timestamp,
        vision_interaction_id,
    )

    return {
        "status": "pending",
        "product_id": (
            matched_product.id
            if matched_product is not None
            else None
        ),
        "inventory_item": None,
        "event": None,
        "pending": pending,
    }


def process_vision_interaction(
    db: Session,
    interaction_data: VisionInteractionRequest,
):
    interaction = create_vision_interaction(
        db,
        interaction_id=interaction_data.interaction_id,
        timestamp=interaction_data.timestamp,
    )

    results = []

    for vision_event in interaction_data.events:
        result = process_single_vision_event(
            db,
            vision_event,
            interaction_data.timestamp,
            interaction.id,
        )

        results.append(result)

    return interaction, results