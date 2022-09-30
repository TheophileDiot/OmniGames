# for arm only
# FROM eclipse-temurin:17

# for amd only
FROM azul/zulu-openjdk:13

# Run as non-root user
RUN groupadd -g 322 lavalink && \
  useradd -r -u 322 -g lavalink lavalink
USER lavalink

WORKDIR /opt/Lavalink

# for arm only
# COPY Lavalink-arm.jar /opt/Lavalink/Lavalink.jar

# for amd only
COPY Lavalink.jar /opt/Lavalink/Lavalink.jar

COPY application.yml /opt/Lavalink/application.yml

ENTRYPOINT ["java", "-Djdk.tls.client.protocols=TLSv1.1,TLSv1.2", "-Xmx6G", "-jar", "Lavalink.jar"]
