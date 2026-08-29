from sqlalchemy import (
    CheckConstraint,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import ProductCategory


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