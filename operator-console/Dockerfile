# syntax=docker/dockerfile:1.6

#############################################
# Stage 1: Builder (Node + protoc toolchain)
#############################################
FROM node:20-bookworm-slim AS operator-console-builder

# 기본 유틸 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl unzip ca-certificates git which && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Node 의존성 설치 (캐시 사용)
COPY operator-console/package*.json ./
RUN --mount=type=cache,target=/root/.npm (npm ci || npm install)

# 소스 및 proto 복사
COPY operator-console/ ./
COPY proto /proto

# ===== protoc & grpc-web 설치 =====
# protoc (내장 js 코드생성기 포함)
ARG PROTOC_VERSION="26.1"
RUN curl -sSL -o /tmp/protoc.zip \
      "https://github.com/protocolbuffers/protobuf/releases/download/v${PROTOC_VERSION}/protoc-${PROTOC_VERSION}-linux-x86_64.zip" \
    && unzip -q /tmp/protoc.zip -d /usr/local \
    && rm /tmp/protoc.zip

# gRPC-Web 플러그인
ARG GRPC_WEB_VERSION="1.5.0"
RUN curl -sSL -o /usr/local/bin/protoc-gen-grpc-web \
      "https://github.com/grpc/grpc-web/releases/download/${GRPC_WEB_VERSION}/protoc-gen-grpc-web-${GRPC_WEB_VERSION}-linux-x86_64" \
    && chmod +x /usr/local/bin/protoc-gen-grpc-web

# JS 런타임 라이브러리 (google-protobuf) 설치
ARG GOOGLE_PROTOBUF_VERSION="3.21.2"
RUN npm install google-protobuf@${GOOGLE_PROTOBUF_VERSION}

# ===== 코드 생성 =====
# ⚠️ 주의: --plugin=protoc-gen-js=... 사용 금지!
# JS 생성기는 protoc 내장이라 --js_out 만 쓰면 됩니다.
# gRPC-Web은 PATH 에 있는 protoc-gen-grpc-web 바이너리를 사용합니다.
RUN mkdir -p src/proto && \
    protoc -I /proto /proto/semantos.proto \
      --js_out=import_style=commonjs,binary:src/proto \
      --grpc-web_out=import_style=typescript,mode=grpcwebtext:src/proto

# ===== 프론트엔드 빌드 =====
RUN --mount=type=cache,target=/root/.npm/_cacache (npm run build --if-present)

#############################################
# Stage 2: Runtime (Nginx)
#############################################
FROM nginx:1.27-bookworm AS operator-console

# Nginx 설정
COPY operator-console/nginx.conf /etc/nginx/conf.d/default.conf

# 정적 산출물 배포
COPY --from=operator-console-builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

