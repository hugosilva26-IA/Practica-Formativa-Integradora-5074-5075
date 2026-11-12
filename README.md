# Práctica Formativa Integradora: integridad de datos y HDFS

Repositorio de la práctica de **Sistemas de Big Data (Módulo 5074)** y **Almacenamiento y Gestión de Datos (Módulo 5075)**.

## Estructura del repositorio

```text
.
├── Dockerfile
├── docker-compose.yml
├── config
├── datos/
│   ├── telemetria_envios.csv
│   └── telemetria_limpia.csv
├── scripts/
│   └── limpiar_telemetria.py
└── evidencias/
    ├── 01_hashes_sha256.png
    ├── 02_jps_servicios.png
    ├── 03_hdfs_comandos_fsck.png
    └── 04_webui_hdfs_browse.png
```

## 1. Integridad del dataset (Módulo 5075)

Se calculó SHA-256 sobre los bytes de cada CSV. El original se conserva y el script `scripts/limpiar_telemetria.py` genera `datos/telemetria_limpia.csv`, eliminando filas duplicadas, registros con valores nulos en los campos críticos, pesos no positivos, temperaturas superiores a 50 °C y estados de envío no reconocidos.

| Archivo | Momento | SHA-256 |
|---|---|---|
| `datos/telemetria_envios.csv` | Original, antes de depurar | `4471C18A0284B3AA5B32A0713E691E3C7FCADAE402F105E901C7C57F49474911` |
| `datos/telemetria_limpia.csv` | Resultado, después de depurar | `23FE3D0B4801E8D90FE7BD79004F79C74058FA79C6DE0A62D0964CE616F42513` |

Para repetir la limpieza y obtener ambos hashes:

```bash
python -m pip install pandas
python scripts/limpiar_telemetria.py
```

La firma SHA-256 cambia porque el CSV depurado contiene bytes distintos del original. La captura del cálculo está en [01_hashes_sha256.png](evidencias/01_hashes_sha256.png).

## 2. Despliegue y exploración HDFS (Módulo 5074)

El entorno se construye con Docker Compose. El Dockerfile añade un JDK 8 porque la imagen base de Hadoop incluye Java de ejecución, pero no la herramienta de diagnóstico `jps`. Compose inicia NameNode, dos DataNodes, ResourceManager y NodeManager. Los puertos publicados en el equipo anfitrión son **9870** (Web UI del NameNode) y **8088** (Web UI de YARN); el puerto RPC de HDFS, **8020**, se usa en la red interna de Compose.

```bash
docker compose up -d --build
docker compose ps
```

Cada daemon se ejecuta en un contenedor distinto. Para comprobar el NameNode y los DataNodes con `jps`:

```bash
docker compose exec namenode jps
docker compose exec datanode1 jps
docker compose exec datanode2 jps
```

En cada salida aparece el proceso Hadoop correspondiente y el proceso temporal `Jps`. La evidencia solicitada está en [02_jps_servicios.png](evidencias/02_jps_servicios.png).

El directorio local `datos/` se monta como `/workspace` en el NameNode. Estos comandos cargan el CSV depurado, lo listan y revisan sus bloques y ubicaciones:

```bash
docker compose exec namenode hdfs dfs -mkdir -p /empresa/logistica/input
docker compose exec namenode hdfs dfs -put /workspace/telemetria_limpia.csv /empresa/logistica/input/
docker compose exec namenode hdfs dfs -ls /empresa/logistica/input/
docker compose exec namenode hdfs fsck /empresa/logistica/input/telemetria_limpia.csv -files -blocks -locations
```

La configuración de esta práctica establece un factor de replicación de **2**. La evidencia de `put`, `ls` y `fsck` está en [03_hdfs_comandos_fsck.png](evidencias/03_hdfs_comandos_fsck.png). La Web UI del NameNode está disponible en [http://localhost:9870](http://localhost:9870); desde **Utilities → Browse the file system** se puede localizar `/empresa/logistica/input/telemetria_limpia.csv`. Captura: [04_webui_hdfs_browse.png](evidencias/04_webui_hdfs_browse.png).

## 3. Análisis crítico: tolerancia a fallos en HDFS

HDFS divide los archivos en bloques y guarda varias réplicas de cada bloque en DataNodes distintos. Si un DataNode deja de responder, el NameNode lo detecta al dejar de recibir sus *heartbeats*. Mientras quede una réplica legible, los clientes pueden seguir leyendo el bloque desde otro DataNode. El NameNode identifica los bloques cuya cantidad de réplicas cayó por debajo del factor configurado y ordena nuevas copias cuando hay DataNodes disponibles.

La replicación ayuda frente a la pérdida de un nodo, y los *checksums* permiten detectar bloques dañados durante la lectura. Si una réplica no pasa la comprobación, el cliente puede leer una copia válida y HDFS puede volver a replicar el bloque. La tolerancia depende de que sobreviva al menos una réplica y de que los nodos y sus discos no fallen todos a la vez; la replicación no sustituye a las copias de seguridad. La alta disponibilidad del propio NameNode requiere una configuración adicional.

En esta práctica hay dos DataNodes y el factor de replicación está configurado en 2. Si uno falla, la copia restante permite conservar y leer los datos, pero no queda otro DataNode disponible para restaurar dos réplicas hasta que se incorpore uno. En un clúster de producción, los nodos suelen distribuirse entre distintos hosts y racks para reducir el riesgo de fallos correlacionados.

## 4. Evidencias gráficas

### 01. Hashes SHA-256 antes y después de la depuración

![Cálculo de hashes SHA-256](evidencias/01_hashes_sha256.png)

### 02. Procesos Hadoop con `jps`

![Salida de jps dentro del contenedor](evidencias/02_jps_servicios.png)

### 03. Carga y revisión de bloques HDFS

![Comandos HDFS y salida de fsck](evidencias/03_hdfs_comandos_fsck.png)
![](evidencias/03_1_hdfs_comandos_fsck.png)

### 04. Explorador HDFS de la Web UI

![Archivo en el explorador del NameNode](evidencias/04_webui_hdfs_browse.png)
