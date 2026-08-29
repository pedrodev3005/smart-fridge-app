from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums import (
    InventoryMovementType,
    ProductCategory,
    ProductMatchType,
)


class ProductIdentity(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    brand: str | None = Field(
        default=None,
        max_length=100,
    )

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value):
        if not isinstance(value, str):
            return value

        return " ".join(value.split())

    @field_validator("brand", mode="before")
    @classmethod
    def normalize_brand(cls, value):
        if value is None:
            return None

        if not isinstance(value, str):
            return value

        normalized = " ".join(value.split())

        if not normalized:
            return None

        return normalized


class ProductBase(ProductIdentity):
    category: ProductCategory = ProductCategory.UNCATEGORIZED

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, value):
        if value is None:
            return ProductCategory.UNCATEGORIZED

        if isinstance(value, str) and not value.strip():
            return ProductCategory.UNCATEGORIZED

        return value


class ProductCreate(ProductBase):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "Iogurte Natural",
                "brand": "Nestlé",
                "category": "Laticínios",
            }
        },
    )


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ProductMatchRequest(ProductIdentity):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "Suco de Uva",
                "brand": "Quinta do Morgado",
            }
        },
    )


class ProductMatchResponse(BaseModel):
    match_type: ProductMatchType
    exact_match: ProductResponse | None = None
    candidates: list[ProductResponse] = Field(default_factory=list)


class InventoryMovementRequest(BaseModel):
    product_id: int = Field(
        ge=1,
        strict=True,
    )

    movement_type: InventoryMovementType

    quantity: int = Field(
        ge=1,
        strict=True,
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "product_id": 2,
                "movement_type": "entry",
                "quantity": 3,
            }
        },
    )