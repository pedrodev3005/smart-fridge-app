from datetime import datetime, timezone

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.enums import (
    InventoryMovementType,
    ProductCategory,
    ProductMatchType,
    UnknownProductStatus,
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


class InventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    product: ProductResponse


class ErrorResponse(BaseModel):
    detail: str


class InventoryMovementResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": 2,
                "movement_type": "entry",
                "quantity_moved": 3,
                "final_quantity": 3,
                "inventory_item": {
                    "id": 1,
                    "product_id": 2,
                    "quantity": 3,
                    "product": {
                        "name": "Maçã",
                        "brand": None,
                        "category": "Não categorizado",
                        "id": 2,
                    },
                },
            }
        }
    )
        
    product_id: int = Field(
        ge=1,
        strict=True,
    )

    movement_type: InventoryMovementType

    quantity_moved: int = Field(
        ge=1,
        strict=True,
    )

    final_quantity: int = Field(
        ge=0,
        strict=True,
    )

    inventory_item: InventoryResponse | None = None

    @model_validator(mode="after")
    def validate_inventory_consistency(self):
        if self.final_quantity == 0:
            if self.inventory_item is not None:
                raise ValueError(
                    "inventory_item deve ser nulo quando final_quantity for 0."
                )

            return self

        if self.inventory_item is None:
            raise ValueError(
                "inventory_item é obrigatório quando final_quantity for maior que 0."
            )

        if self.inventory_item.quantity != self.final_quantity:
            raise ValueError(
                "A quantidade do inventory_item deve ser igual a final_quantity."
            )

        if self.inventory_item.product_id != self.product_id:
            raise ValueError(
                "O product_id do inventory_item deve corresponder ao product_id da movimentação."
            )

        return self
    
class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: InventoryMovementType
    product_id: int
    quantity: int
    timestamp: datetime
    product: ProductResponse

    @field_validator("timestamp")
    @classmethod
    def ensure_utc_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value

class UnknownProductCreateRequest(BaseModel):
    image_path: str = Field(
        min_length=1,
        max_length=500,
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
                "image_path": "vision/captures/unknown_001.jpg",
                "movement_type": "entry",
                "quantity": 1,
            }
        },
    )

    @field_validator("image_path")
    @classmethod
    def normalize_image_path(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "O caminho da imagem não pode estar vazio."
            )

        return value
    
class UnknownProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_path: str
    movement_type: InventoryMovementType
    quantity: int
    status: UnknownProductStatus
    detected_at: datetime
    reviewed_at: datetime | None
    resolved_product_id: int | None
    resolved_product: ProductResponse | None

    @field_validator("detected_at", "reviewed_at")
    @classmethod
    def ensure_utc_timezone(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        if value is None:
            return None

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value
    
    @model_validator(mode="after")
    def validate_status_consistency(self):
        if self.status == UnknownProductStatus.PENDING:
            if (
                self.reviewed_at is not None
                or self.resolved_product_id is not None
                or self.resolved_product is not None
            ):
                raise ValueError(
                    "Um produto pendente não pode possuir dados de revisão."
                )

        elif self.status == UnknownProductStatus.RESOLVED:
            if self.reviewed_at is None:
                raise ValueError(
                    "Um produto resolvido deve possuir reviewed_at."
                )

            if (
                self.resolved_product_id is None
                or self.resolved_product is None
            ):
                raise ValueError(
                    "Um produto resolvido deve possuir o produto associado."
                )

            if self.resolved_product.id != self.resolved_product_id:
                raise ValueError(
                    "resolved_product deve corresponder a resolved_product_id."
                )

        elif self.status == UnknownProductStatus.DISMISSED:
            if self.reviewed_at is None:
                raise ValueError(
                    "Um produto descartado deve possuir reviewed_at."
                )

            if (
                self.resolved_product_id is not None
                or self.resolved_product is not None
            ):
                raise ValueError(
                    "Um produto descartado não pode possuir produto associado."
                )

        return self

class UnknownProductResolveRequest(BaseModel):
    resolved_product_id: int = Field(
        ge=1,
        strict=True,
    )
    resolved_quantity: int | None = Field(
        default=None,
        ge=1,
        strict=True,
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "resolved_product_id": 2,
                "resolved_quantity": 1,
            }
        },
    )