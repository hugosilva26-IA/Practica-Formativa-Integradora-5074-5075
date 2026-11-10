# `jps` pertenece al JDK; la imagen oficial de Hadoop trae solo el JRE.
# Tomamos el JDK 8 de la imagen oficial de Eclipse Temurin y lo añadimos
# a la imagen oficial de Hadoop, manteniendo Hadoop 3.4.0 como base.
FROM eclipse-temurin:8-jdk AS jdk

FROM apache/hadoop:3.4.0

COPY --from=jdk /opt/java/openjdk /opt/jdk

ENV JAVA_HOME=/opt/jdk
ENV PATH="/opt/jdk/bin:${PATH}"
