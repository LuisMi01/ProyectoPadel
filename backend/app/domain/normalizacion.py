"""Normalización de los valores que llegan en los feeds de las tiendas."""

import re
import unicodedata
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher

_SI = {
    "1",
    "true",
    "yes",
    "y",
    "si",
    "sí",
    "in stock",
    "instock",
    "en stock",
    "disponible",
    "available",
    "in_stock",
}
_NO = {
    "0",
    "false",
    "no",
    "n",
    "out of stock",
    "outofstock",
    "agotado",
    "agotada",
    "sin stock",
    "no disponible",
    "unavailable",
    "out_of_stock",
}


def precio(valor: object) -> Decimal | None:
    """«279,95 €», «1.299,00», «279.95», 279.95 -> Decimal con dos decimales; None si no vale."""
    if valor is None or isinstance(valor, bool):
        return None
    if isinstance(valor, int | float | Decimal):
        texto = str(valor)
    else:
        texto = re.sub(r"[^\d.,-]", "", str(valor))
        if "," in texto and "." in texto:
            # El separador decimal es el último que aparece; el otro es de miles.
            miles = "." if texto.rfind(",") > texto.rfind(".") else ","
            texto = texto.replace(miles, "").replace(",", ".")
        elif "," in texto:
            texto = (
                texto.replace(",", ".")
                if re.search(r",\d{1,2}$", texto)
                else texto.replace(",", "")
            )
        elif re.fullmatch(r"\d{1,3}(\.\d{3})+", texto):
            texto = texto.replace(".", "")  # «1.299» es mil doscientos noventa y nueve
    try:
        importe = Decimal(texto).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None
    return importe if importe > 0 else None


def disponible(valor: object) -> bool:
    """Interpreta el stock del feed. Si no viene, se da por disponible (está en el feed)."""
    if valor is None:
        return True
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, int | float):
        return valor > 0
    texto = str(valor).strip().lower()
    if not texto or texto in _SI:
        return True
    if texto in _NO:
        return False
    try:
        return float(texto.replace(",", ".")) > 0
    except ValueError:
        return True


def ean(valor: object) -> str | None:
    """Solo dígitos, en formato EAN-13 cuando se puede (UPC-12 y GTIN-14 con cero inicial)."""
    if valor is None:
        return None
    digitos = re.sub(r"\D", "", str(valor))
    if len(digitos) == 12:
        digitos = "0" + digitos
    elif len(digitos) == 14 and digitos.startswith("0"):
        digitos = digitos[1:]
    return digitos if len(digitos) in (8, 13, 14) else None


# Palabras que llevan casi todos los títulos y no distinguen una pala de otra.
_GENERICAS = {"pala", "palas", "padel", "de", "racket"}


def _palabras(texto: str) -> list[str]:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", sin_tildes.lower()).split()


def texto_comparable(texto: str) -> str:
    """Minúsculas, sin tildes, signos ni palabras genéricas.

    «Pala de pádel BULLPADEL Vertex-04 '25» -> «bullpadel vertex 04 25».
    """
    return " ".join(p for p in _palabras(texto) if p not in _GENERICAS)


# Lo que también venden las tiendas de pádel y no es una pala.
_NO_PALA = {
    "paletero", "paleteros", "mochila", "mochilas", "bolsa", "bolsas", "bolso", "funda", "fundas",
    "protector", "protectores", "grip", "grips", "overgrip", "overgrips", "cinta", "cintas",
    "pelota", "pelotas", "bote", "botes", "zapatilla", "zapatillas", "calcetines", "camiseta",
    "camisetas", "polo", "pantalon", "short", "falda", "vestido", "sudadera", "chaqueta", "gorra",
    "visera", "munequera", "munequeras", "antivibrador", "red", "poste", "recogepelotas",
}  # fmt: skip
_PALA = {"pala", "palas", "racket", "rackets", "raqueta", "raquetas"}


def parece_pala(titulo: str, categoria: str | None = None) -> bool:
    """¿Es una pala? Para no mandar a revisión zapatillas, pelotas o paleteros.

    Si el feed trae categoría, manda ella: tiene que hablar de palas y no de accesorios. Si no la
    trae, se mira la primera palabra del título, que suele ser el tipo de producto («Paletero…»,
    «Zapatillas…»). Ante la duda se deja pasar: una pala perdida es peor que una revisión de más.
    """
    if categoria:
        palabras = set(_palabras(categoria))
        return bool(palabras & _PALA) and not palabras & _NO_PALA
    palabras = _palabras(titulo)
    return not (palabras and palabras[0] in _NO_PALA)


def parecido(a: str, b: str) -> float:
    """Parecido entre dos nombres de producto, de 0 a 1."""
    return SequenceMatcher(None, texto_comparable(a), texto_comparable(b)).ratio()
