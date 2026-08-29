from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums import ProductCategory


class ProductBase(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    brand: str | None = Field(
        default=None,
        max_length=100,
    )

    category: ProductCategory = ProductCategory.UNCATEGORIZED

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

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, value):
        if value is None:
            return ProductCategory.UNCATEGORIZED

        if isinstance(value, str) and not value.strip():
            return ProductCategory.UNCATEGORIZED

        return value


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int