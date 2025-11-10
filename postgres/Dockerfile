# Use official PostgreSQL image as base
FROM postgres:latest

# Set environment variables (optional if using .env)
ENV POSTGRES_USER=myuser
ENV POSTGRES_PASSWORD=mypassword
ENV POSTGRES_DB=mydb

# Copy initialization scripts (optional)
# Any .sql or .sh scripts in /docker-entrypoint-initdb.d/ will run on first startup
COPY ./init-scripts/ /docker-entrypoint-initdb.d/

# Expose PostgreSQL port
EXPOSE 5432
