from datetime import datetime, timezone

from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.enums import (
    InventoryMovementType,
    NutritionReferenceUnit,
    ProductCategory,
    ProductMatchType,
    UnknownProductStatus,
    VisionConfidence,
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


class VisionProductInput(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    brand: str | None = Field(
        default=None,
        max_length=100,
    )

    category: str | None = Field(
        default=None,
        max_length=100,
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator(
        "name",
        "brand",
        "category",
        mode="before",
    )
    @classmethod
    def normalize_text_fields(cls, value):
        if value is None:
            return None

        if not isinstance(value, str):
            return value

        normalized = " ".join(value.split())

        return normalized or None


class VisionEventInput(BaseModel):
    movement_type: InventoryMovementType

    product: VisionProductInput | None = None

    confidence: VisionConfidence = VisionConfidence.NOT_INFORMED

    quantity: int = Field(
        default=1,
        ge=1,
        strict=True,
    )

    requires_confirmation: bool

    model_config = ConfigDict(extra="forbid")


class VisionInteractionRequest(BaseModel):
    interaction_id: str = Field(
        min_length=1,
        max_length=100,
    )

    timestamp: datetime

    events: list[VisionEventInput] = Field(
        min_length=1,
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("interaction_id")
    @classmethod
    def normalize_interaction_id(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "O interaction_id não pode estar vazio."
            )

        return value

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "O timestamp deve incluir o fuso horário."
            )

        return value.astimezone(timezone.utc)


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
    vision_interaction_id: int | None
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
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "image_path": "vision/captures/unknown_001.jpg",
                "movement_type": "entry",
                "quantity": 1,
                "status": "pending",
                "detected_at": "2026-08-29T18:11:03Z",
                "reviewed_at": None,
                "resolved_product_id": None,
                "resolved_product": None,
            }
        },
    )

    id: int
    image_path: str | None
    movement_type: InventoryMovementType
    quantity: int
    vision_interaction_id: int | None

    detected_name: str | None
    detected_brand: str | None
    detected_category: str | None
    confidence: VisionConfidence | None

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


class VisionEventResultResponse(BaseModel):
    status: Literal["processed", "pending"]

    product_id: int | None = None
    inventory_item: InventoryResponse | None = None
    event: EventResponse | None = None
    pending: UnknownProductResponse | None = None

    @model_validator(mode="after")
    def validate_result_consistency(self):
        if self.status == "processed":
            if self.product_id is None:
                raise ValueError(
                    "Um evento processado deve possuir product_id."
                )

            if self.event is None:
                raise ValueError(
                    "Um evento processado deve possuir event."
                )

            if self.pending is not None:
                raise ValueError(
                    "Um evento processado não pode possuir pending."
                )

        elif self.status == "pending":
            if self.pending is None:
                raise ValueError(
                    "Um evento pendente deve possuir pending."
                )

            if self.inventory_item is not None or self.event is not None:
                raise ValueError(
                    "Um evento pendente não pode possuir movimentação processada."
                )

        return self


class VisionInteractionResponse(BaseModel):
    interaction_id: str
    timestamp: datetime
    received_at: datetime
    results: list[VisionEventResultResponse]

    @field_validator("timestamp", "received_at")
    @classmethod
    def ensure_utc_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value


class NutritionBase(BaseModel):
    reference_amount: float = Field(gt=0)
    reference_unit: NutritionReferenceUnit

    energy_kcal: float | None = Field(
        default=None,
        ge=0,
    )
    carbohydrates_g: float | None = Field(
        default=None,
        ge=0,
    )
    protein_g: float | None = Field(
        default=None,
        ge=0,
    )
    total_fat_g: float | None = Field(
        default=None,
        ge=0,
    )
    fiber_g: float | None = Field(
        default=None,
        ge=0,
    )
    sodium_mg: float | None = Field(
        default=None,
        ge=0,
    )

    source_name: str = Field(
        min_length=1,
        max_length=150,
    )
    source_reference: str | None = Field(
        default=None,
        max_length=500,
    )

    @field_validator(
        "reference_amount",
        "energy_kcal",
        "carbohydrates_g",
        "protein_g",
        "total_fat_g",
        "fiber_g",
        "sodium_mg",
        mode="before",
    )
    @classmethod
    def validate_numeric_values(cls, value):
        if value is None:
            return None

        if isinstance(value, bool) or not isinstance(
            value,
            (int, float),
        ):
            raise ValueError(
                "O valor deve ser numérico."
            )

        return value

    @field_validator("source_name")
    @classmethod
    def normalize_source_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "A fonte dos dados não pode estar vazia."
            )

        return value

    @field_validator("source_reference")
    @classmethod
    def normalize_source_reference(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None

    @model_validator(mode="after")
    def validate_has_nutrition_data(self):
        nutrients = (
            self.energy_kcal,
            self.carbohydrates_g,
            self.protein_g,
            self.total_fat_g,
            self.fiber_g,
            self.sodium_mg,
        )

        if all(value is None for value in nutrients):
            raise ValueError(
                "Pelo menos um valor nutricional deve ser informado."
            )

        return self


class NutritionCreateRequest(NutritionBase):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "reference_amount": 100,
                "reference_unit": "g",
                "energy_kcal": 50,
                "carbohydrates_g": 12,
                "protein_g": 1,
                "total_fat_g": 0.5,
                "fiber_g": 2,
                "sodium_mg": 1,
                "source_name": "Fonte nutricional",
                "source_reference": "registro-001",
            }
        },
    )


class NutritionResponse(NutritionBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    product_id: int
    product: ProductResponse