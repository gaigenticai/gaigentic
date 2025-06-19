# postgres.Dockerfile
FROM postgres:15

RUN apt-get update && apt-get install -y postgresql-server-dev-15 build-essential \
  && git clone --depth 1 https://github.com/pgvector/pgvector.git \
  && cd pgvector && make && make install \
  && cd .. && rm -rf pgvector
