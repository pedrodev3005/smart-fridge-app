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