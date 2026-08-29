from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import (
    InventoryMovementType,
    ProductCategory,
    UnknownProductStatus,
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


class UnknownProduct(Base):
    __tablename__ = "unknown_products"

    __table_args__ = (
        CheckConstraint(
            "length(trim(image_path)) > 0",
            name="ck_unknown_products_image_path_not_blank",
        ),
        CheckConstraint(
            "length(image_path) <= 500",
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

    image_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
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