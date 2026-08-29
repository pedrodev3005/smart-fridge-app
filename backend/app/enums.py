from enum import Enum


class ProductCategory(str, Enum):
    BEVERAGES = "Bebidas"
    DAIRY = "Laticínios"
    FRUITS = "Frutas"
    VEGETABLES = "Verduras e legumes"
    MEAT = "Carnes"
    EGGS = "Ovos"
    COLD_CUTS = "Frios e embutidos"
    SWEETS = "Doces"
    CONDIMENTS = "Molhos e condimentos"
    OTHER = "Outros"
    UNCATEGORIZED = "Não categorizado"


class ProductMatchType(str, Enum):
    EXACT = "exact"
    SINGLE_CANDIDATE = "single_candidate"
    MULTIPLE_CANDIDATES = "multiple_candidates"
    NONE = "none"


class InventoryMovementType(str, Enum):
    ENTRY = "entry"
    EXIT = "exit"