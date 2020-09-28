# Base container
FROM openjdk:11-jre-slim

# First task: insert Fat-JAR package within the container
COPY build/libs/template-service.jar /jar/

# Declare and expose service listening port
EXPOSE 7000/tcp

# Declare entrypoint of that exposed service. In this case, running the inserted JAR package.
ENTRYPOINT ["java", "-jar", "/jar/template-service.jar"]
