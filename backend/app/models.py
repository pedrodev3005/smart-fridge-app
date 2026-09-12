from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import (
    InventoryMovementType,
    NutritionReferenceUnit,
    ProductCategory,
    UnknownProductStatus,
    VisionConfidence,
)


class Product(Base):
    __tablename__ = "products"

    __table_args__ = (
        CheckConstraint(
            "length(trim(name)) >= 2",
            name="ck_products_name_min_length",
        ),
        CheckConstraint(
            "length(name) <= 100",
            name="ck_products_name_max_length",
        ),
        CheckConstraint(
            "brand IS NULL OR length(trim(brand)) > 0",
            name="ck_products_brand_not_blank",
        ),
        CheckConstraint(
            "brand IS NULL OR length(brand) <= 100",
            name="ck_products_brand_max_length",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    brand: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    category: Mapped[ProductCategory] = mapped_column(
        SqlEnum(
            ProductCategory,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
            create_constraint=True,
            name="product_category",
        ),
        nullable=False,
        default=ProductCategory.UNCATEGORIZED,
        server_default=ProductCategory.UNCATEGORIZED.value,
    )


class Inventory(Base):
    __tablename__ = "inventory"

    __table_args__ = (
        CheckConstraint(
            "typeof(quantity) = 'integer' AND quantity >= 1",
            name="ck_inventory_quantity_valid",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey(
            "products.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        unique=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    product: Mapped["Product"] = relationship(
        "Product",
    )


class Event(Base):
    __tablename__ = "events"

    __table_args__ = (
        CheckConstraint(
            "typeof(quantity) = 'integer' AND quantity >= 1",
            name="ck_events_quantity_valid",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    event_type: Mapped[InventoryMovementType] = mapped_column(
        SqlEnum(
            InventoryMovementType,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
            create_constraint=True,
            name="inventory_event_type",
        ),
        nullable=False,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey(
            "products.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    vision_interaction_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "vision_interactions.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )

    product: Mapped["Product"] = relationship(
        "Product",
    )


class VisionInteraction(Base):
    __tablename__ = "vision_interactions"

    __table_args__ = (
        CheckConstraint(
            "length(trim(interaction_id)) > 0",
            name="ck_vision_interactions_id_not_blank",
        ),
        CheckConstraint(
            "length(interaction_id) <= 100",
            name="ck_vision_interactions_id_max_length",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    interaction_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )


class UnknownProduct(Base):
    __tablename__ = "unknown_products"

    __table_args__ = (
        CheckConstraint(
            "image_path IS NULL OR length(trim(image_path)) > 0",
            name="ck_unknown_products_image_path_not_blank",
        ),
        CheckConstraint(
            "image_path IS NULL OR length(image_path) <= 500",
            name="ck_unknown_products_image_path_max_length",
        ),
        CheckConstraint(
            "typeof(quantity) = 'integer' AND quantity >= 1",
            name="ck_unknown_products_quantity_valid",
        ),
        CheckConstraint(
            """
            (
                status = 'pending'
                AND reviewed_at IS NULL
                AND resolved_product_id IS NULL
            )
            OR
            (
                status = 'resolved'
                AND reviewed_at IS NOT NULL
                AND resolved_product_id IS NOT NULL
            )
            OR
            (
                status = 'dismissed'
                AND reviewed_at IS NOT NULL
                AND resolved_product_id IS NULL
            )
            """,
            name="ck_unknown_products_status_consistency",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    image_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    movement_type: Mapped[InventoryMovementType] = mapped_column(
        SqlEnum(
            InventoryMovementType,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
            create_constraint=True,
            name="unknown_product_movement_type",
        ),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    vision_interaction_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "vision_interactions.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    detected_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    detected_brand: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    detected_category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    confidence: Mapped[VisionConfidence | None] = mapped_column(
        SqlEnum(
            VisionConfidence,
            values_callable=lambda enum: [
                item.value for item in enum
            ],
            native_enum=False,
            create_constraint=True,
            name="vision_confidence",
        ),
        nullable=True,
    )

    status: Mapped[UnknownProductStatus] = mapped_column(
        SqlEnum(
            UnknownProductStatus,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
            create_constraint=True,
            name="unknown_product_status",
        ),
        nullable=False,
        default=UnknownProductStatus.PENDING,
        server_default=UnknownProductStatus.PENDING.value,
    )

    detected_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    resolved_product_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "products.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    resolved_product: Mapped["Product | None"] = relationship(
        "Product",
    )


class Nutrition(Base):
    __tablename__ = "nutrition"

    __table_args__ = (
        CheckConstraint(
            """
            typeof(reference_amount) IN ('integer', 'real')
            AND reference_amount > 0
            """,
            name="ck_nutrition_reference_amount_positive",
        ),
        CheckConstraint(
            """
            energy_kcal IS NULL
            OR (
                typeof(energy_kcal) IN ('integer', 'real')
                AND energy_kcal >= 0
            )
            """,
            name="ck_nutrition_energy_non_negative",
        ),
        CheckConstraint(
            """
            carbohydrates_g IS NULL
            OR (
                typeof(carbohydrates_g) IN ('integer', 'real')
                AND carbohydrates_g >= 0
            )
            """,
            name="ck_nutrition_carbohydrates_non_negative",
        ),
        CheckConstraint(
            """
            protein_g IS NULL
            OR (
                typeof(protein_g) IN ('integer', 'real')
                AND protein_g >= 0
            )
            """,
            name="ck_nutrition_protein_non_negative",
        ),
        CheckConstraint(
            """
            total_fat_g IS NULL
            OR (
                typeof(total_fat_g) IN ('integer', 'real')
                AND total_fat_g >= 0
            )
            """,
            name="ck_nutrition_total_fat_non_negative",
        ),
        CheckConstraint(
            """
            fiber_g IS NULL
            OR (
                typeof(fiber_g) IN ('integer', 'real')
                AND fiber_g >= 0
            )
            """,
            name="ck_nutrition_fiber_non_negative",
        ),
        CheckConstraint(
            """
            sodium_mg IS NULL
            OR (
                typeof(sodium_mg) IN ('integer', 'real')
                AND sodium_mg >= 0
            )
            """,
            name="ck_nutrition_sodium_non_negative",
        ),
        CheckConstraint(
            """
            energy_kcal IS NOT NULL
            OR carbohydrates_g IS NOT NULL
            OR protein_g IS NOT NULL
            OR total_fat_g IS NOT NULL
            OR fiber_g IS NOT NULL
            OR sodium_mg IS NOT NULL
            """,
            name="ck_nutrition_has_at_least_one_value",
        ),
        CheckConstraint(
            "length(trim(source_name)) > 0",
            name="ck_nutrition_source_name_not_blank",
        ),
        CheckConstraint(
            "length(source_name) <= 150",
            name="ck_nutrition_source_name_max_length",
        ),
        CheckConstraint(
            "source_reference IS NULL OR length(trim(source_reference)) > 0",
            name="ck_nutrition_source_reference_not_blank",
        ),
        CheckConstraint(
            "source_reference IS NULL OR length(source_reference) <= 500",
            name="ck_nutrition_source_reference_max_length",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    reference_amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    reference_unit: Mapped[NutritionReferenceUnit] = mapped_column(
        SqlEnum(
            NutritionReferenceUnit,
            values_callable=lambda enum: [
                item.value for item in enum
            ],
            native_enum=False,
            create_constraint=True,
            name="nutrition_reference_unit",
        ),
        nullable=False,
    )

    energy_kcal: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    carbohydrates_g: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    protein_g: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    total_fat_g: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    fiber_g: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    sodium_mg: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    source_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    source_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    product: Mapped["Product"] = relationship("Product")