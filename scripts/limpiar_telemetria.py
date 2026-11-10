import hashlib
import pandas as pd
from pathlib import Path

# --------------------------------------------------
# 1. Definir las rutas de los archivos
# --------------------------------------------------

# Localizamos la carpeta principal del proyecto
carpeta_proyecto = Path(__file__).resolve().parent.parent

# Archivo original y archivo limpio
archivo_original = carpeta_proyecto / "datos" / "telemetria_envios.csv"
archivo_limpio = carpeta_proyecto / "datos" / "telemetria_limpia.csv"


def calcular_sha256(ruta):
    """Devuelve el SHA-256 del contenido exacto de un archivo."""
    return hashlib.sha256(ruta.read_bytes()).hexdigest().upper()


# --------------------------------------------------
# 2. Leer el CSV original
# --------------------------------------------------

datos = pd.read_csv(archivo_original)

print("SHA-256 original:", calcular_sha256(archivo_original))

print("Registros originales:", len(datos))


# --------------------------------------------------
# 3. Eliminar registros duplicados
# --------------------------------------------------

# Elimina las filas que aparecen repetidas
duplicados = datos.duplicated().sum()

datos = datos.drop_duplicates()

print("Duplicados eliminados:", duplicados)


# --------------------------------------------------
# 4. Eliminar registros con valores nulos
# --------------------------------------------------

# Comprobamos los campos importantes para la práctica:
# peso, temperatura y destino.

nulos = datos[["peso_kg", "temp_celsius", "destino"]].isnull().any(axis=1).sum()

# Eliminamos las filas que tengan algún valor nulo
datos = datos.dropna(subset=["peso_kg", "temp_celsius", "destino"])

print("Registros con nulos eliminados:", nulos)


# --------------------------------------------------
# 5. Eliminar valores fuera de rango
# --------------------------------------------------

# El peso no puede ser negativo ni cero.
# Una temperatura superior a 50 grados se considera
# una lectura anómala para esta práctica.

fuera_rango = (
    (datos["peso_kg"] <= 0) |
    (datos["temp_celsius"] > 50)
)

cantidad_fuera_rango = fuera_rango.sum()

# Conservamos solamente los registros válidos
datos = datos[~fuera_rango]

print("Registros fuera de rango eliminados:", cantidad_fuera_rango)


# --------------------------------------------------
# 6. Eliminar estados no reconocidos
# --------------------------------------------------

# Estados válidos del sistema logístico
estados_validos = [
    "ENTREGADO",
    "EN_TRANSITO",
    "EN_REPARTO",
    "INCIDENCIA_REPARTO"
]

# Identificamos los estados que no están en la lista
estados_invalidos = ~datos["estado_envio"].isin(estados_validos)

cantidad_estados_invalidos = estados_invalidos.sum()

# Eliminamos esos registros
datos = datos[~estados_invalidos]

print("Estados no reconocidos eliminados:", cantidad_estados_invalidos)


# --------------------------------------------------
# 7. Guardar el archivo limpio
# --------------------------------------------------

# Guardamos el resultado sin añadir una columna de índices
datos.to_csv(archivo_limpio, index=False, encoding="utf-8")

print("SHA-256 depurado:", calcular_sha256(archivo_limpio))

print("\nLimpieza finalizada correctamente")
print("Registros finales:", len(datos))
print("Archivo generado:", archivo_limpio)
