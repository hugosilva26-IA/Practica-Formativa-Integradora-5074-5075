# Práctica Formativa Integradora: Consolidación de Almacenamiento, Integridad del Dato y Toma de Contacto con HDFS

Este repositorio contiene la resolución de la práctica integradora para los módulos de **Sistemas de Big Data (5074)** y **Almacenamiento y Gestión de Datos (5075)** del Máster en Inteligencia Artificial y Big Data.



---

##  Estructura del Repositorio

Siguiendo las especificaciones de la entrega, el proyecto se organiza del siguiente modo:

```text
.
├── README.md                 # Informe técnico de la práctica (este documento)
├── scripts/
│   └── limpiar_telemetria.py        # Script en Python para limpieza
├── datos/
│   └── .gitkeep              # Control de versión para la carpeta de datos
└── evidencias/
    ├── 01_hashes_sha256.png       # Verificación de integridad SHA-256 en terminal
    ├── 02_jps_servicios.png       # Procesos Java activos en el contenedor
    ├── 03_hdfs_comandos_fsck.png  # Carga en HDFS, inspección CLI y estado con fsck
    └── 04_webui_hdfs_browse.png   # Exploración del dataset en la Web UI del NameNode
```

---

##  Sección 1: Aseguramiento e Integridad del Dato (Módulo 5075)

Antes de subir cualquier conjunto de datos a producción, debemos garantizar su origen e integridad mediante funciones hash unidireccionales (**SHA-256**).

### 1. Hash del dataset original (`telemetria_envios.csv`)
Calculamos el checksum del fichero crudo recibido con anomalías (duplicados, valores nulos `NaN`, pesos negativos como `-45.50 kg`, temperaturas imposibles como `98.4 ºC` y estados no catalogados):

* **Hash SHA-256 (Original):**  
  `4471C18A028483AA5832A0713E691E3C7FCADAE482F105E981C7C57F49474911`

### 2. Proceso de depuración
Mediante el script `scripts/limpiar_telemetria.py` ejecutamos las siguientes reglas de negocio y limpieza:
1. Eliminación de filas duplicadas.
2. Tratamiento o descartes de nulos en columnas críticas (`peso_kg`, `temp_celsius`, `destino`).
3. Filtrado de outliners/inconsistencias (valores de peso $>0$, temperaturas dentro de rango lógico y estados válidos).

### 3. Hash del dataset depurado (`telemetria_limpia.csv`)
Tras la limpieza, generamos el fichero listo para ingesta y comprobamos cómo la **propiedad de avalancha** de SHA-256 hace que la firma cambie completamente:

* **Hash SHA-256 (Depurado):**  
  `23FE3008480158098FE78079064F79C74858FA79C60E0A6208964CE616F42513`

>  *La captura con los cálculos en PowerShell/Bash se encuentra en `evidencias/01_hashes_sha256.png`.*

---

##  Sección 2: Despliegue de Entorno y HDFS (Módulo 5074)

### 1. Levantar la infraestructura
Desplegamos un entorno de Apache Hadoop 3.4.0 mediante **Docker Compose** que incluye NameNode, DataNodes (`datanode1` y `datanode2`), ResourceManager y NodeManager.

```bash
docker compose up -d
docker exec -it namenode bash
```

### 2. Auditoría de daemons Java (`jps`)
Verificamos dentro del contenedor que los servicios esenciales están arriba ejecutando el comando `jps`.
>  *Evidencia disponible en `evidencias/02_jps_servicios.png`.*

### 3. Operaciones CLI en HDFS
Dentro del NameNode, ejecutamos la secuencia de comandos para ingestar y auditar el dataset:

```bash
# 1. Crear directorio de destino en HDFS
hdfs dfs -mkdir -p /empresa/logistica/input

# 2. Ingestar el dataset saneado desde el volumen montado (/workspace)
hdfs dfs -put /workspace/telemetria_limpia.csv /empresa/logistica/input/

# 3. Listar el contenido del directorio
hdfs dfs -ls /empresa/logistica/input/

# 4. Inspeccionar la cabecera e iniciales del fichero cargado
hdfs dfs -head /empresa/logistica/input/telemetria_limpia.csv

# 5. Auditoría de bloques y réplicas
hdfs fsck /empresa/logistica/input/telemetria_limpia.csv -files -blocks -locations
```



> *Evidencias de la ejecución de comandos y fsck en `evidencias/03_hdfs_comandos_fsck.png`.*  
> *Captura de la navegación Web UI (`http://localhost:9870`) en `evidencias/04_webui_hdfs_browse.png`.*

---

##  Sección 3: Análisis Crítico — Tolerancia a Fallos e Integridad en HDFS

**¿Por qué un fichero en HDFS no se corrompe ni se pierde aunque falle o se apague un DataNode en un clúster de producción?**

La resistencia y tolerancia a fallos de HDFS no es casualidad, sino el pilar sobre el que se diseña el almacenamiento distribuido en Big Data. En primer lugar, esto se debe al **mecanismo de replicación de bloques**. Cuando subimos un archivo a HDFS (por ejemplo, nuestro dataset de telemetría), este se divide en bloques de tamaño fijo (habitualmente 128 MB en producción) y cada bloque se replica de forma transparente en múltiples nodos físicos (definido por el *replication factor*, por defecto 3). Si un DataNode cae o se desconecta de la red, la información sigue estando accesible en las otras réplicas alojadas en nodos distintos dentro o fuera del mismo rack.

En segundo lugar, entra en juego el papel activo del **NameNode** y el sistema de latidos (**Heartbeats**). Los DataNodes envían señales periódicas y reportes de bloques (*Block Reports*) al NameNode. Si este deja de recibir el heartbeat de un DataNode durante un tiempo determinado, lo declara *unhealthy* o muerto. Inmediatamente, el NameNode consulta su mapa de metadatos, detecta qué bloques han perdido nivel de réplica y gestiona de forma autónoma la creación de nuevas copias en otros DataNodes activos, restaurando el factor de réplica deseado sin intervención humana ni interrupción del servicio.

Por último, respecto a la **corrupción de datos** (bit rot o errores de transmisión), HDFS realiza un control continuo de integridad mediante **checksums (CRC-32)**. Cada vez que un cliente lee un bloque de HDFS, verifica silenciosamente que la suma de comprobación coincida con la generada durante la escritura. Si detecta un bloque corrupto en un DataNode, el cliente ignora ese bloque defectuoso, lee la copia sana desde otro DataNode y notifica al NameNode para que elimine el bloque corrupto y regenere uno nuevo.

---

##  Sección 4: Galería de Evidencias Gráficas

| Evidencia | Descripción | Archivo |
| :--- | :--- | :--- |
| **01** | Hashes SHA-256 pre y post depuración | `evidencias/01_hashes_sha256.png` |
| **02** | Salida del comando `jps` (Servicios Hadoop) | `evidencias/02_jps_servicios.png` |
| **03** | Comandos HDFS (`put`, `ls`, `head`) y auditoría `fsck` | `evidencias/03_hdfs_comandos_fsck.png` |
| **04** | Explorador de archivos en NameNode Web UI (`:9870`) | `evidencias/04_webui_hdfs_browse.png` |

---
