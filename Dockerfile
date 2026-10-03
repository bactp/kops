# KOPS platform image: API + dashboard + the scenario catalogue. Built with `scripts/build-image.sh`.
FROM python:3.12-slim
ARG KUBECTL_VERSION=v1.35.9
RUN apt-get update && apt-get install -y --no-install-recommends openssh-client curl ca-certificates bash \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL -o /usr/local/bin/kubectl "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" \
    && chmod 0755 /usr/local/bin/kubectl
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .
COPY scenarios ./scenarios
COPY schemas ./schemas
COPY catalog ./catalog
COPY web ./web
ENV KOPS_ROOT=/app KOPS_BIN=/usr/local/bin KOPS_SCENARIOS_DIR=/app/scenarios KOPS_WEB_DIR=/app/web \
    KOPS_CATALOG_FILE=/app/catalog/available.txt KOPS_WORK_DIR=/var/run/kops KOPS_DB_URL=sqlite:////data/kops.db \
    PYTHONUNBUFFERED=1
RUN useradd -u 10001 -m kops && mkdir -p /data /var/run/kops && chown -R kops /data /var/run/kops
USER 10001
EXPOSE 8000
CMD ["kops", "serve", "--host", "0.0.0.0", "--port", "8000"]
