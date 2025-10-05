# =========================
# Builder: Node + Vite + protoc
# =========================
FROM node:20-alpine AS builder

# protoc, curl 설치 (protoc은 alpine 패키지 이름이 protobuf)
RUN apk add --no-cache protobuf curl

WORKDIR /app

# 1) 패키지 설치(캐시 활용)
COPY operator-console/package*.json ./
# CI 환경에 package-lock이 없을 수도 있어 대비
RUN --mount=type=cache,target=/root/.npm (npm ci || npm install)

# 2) 소스 반영
COPY operator-console/ ./

# 3) proto 복사 (리포지토리 루트의 proto/ → /proto)
COPY proto /proto

# 4) gRPC-Web 플러그인 설치 (사전 컴파일 바이너리 다운로드)
#   최신 릴리스는 필요시 버전을 바꾸세요(아래는 1.5.0 예시)
RUN curl -L -o /usr/local/bin/protoc-gen-grpc-web \
      https://github.com/grpc/grpc-web/releases/download/1.5.0/protoc-gen-grpc-web-1.5.0-linux-x86_64 \
 && chmod +x /usr/local/bin/protoc-gen-grpc-web

# 5) gRPC-Web JS/TS 스텁 생성
#   - JS(message) + d.ts : semantos_pb.js / semantos_pb.d.ts
#   - TS(client)        : semantos_grpc_web_pb.ts
#   산출물을 Vite가 import할 경로로 생성: src/proto/
RUN mkdir -p src/proto && \
    protoc -I /proto /proto/semantos.proto \
      --js_out=import_style=commonjs:src/proto \
      --grpc-web_out=import_style=typescript,mode=grpcwebtext:src/proto

# 6) 런타임 의존성 (grpc-web, google-protobuf)이 없으면 추가 설치
#    package.json에 이미 있다면 이 단계는 스킵해도 됩니다.
RUN npm install grpc-web google-protobuf

# 7) 정식 빌드
RUN npm run build


# =========================
# Runtime: Nginx로 정적 서빙 + gRPC-Web 프록시(Nginx 설정)
# =========================
FROM nginx:1.27-bookworm AS runtime

# 기본 conf 제거 후 우리 conf 반영
RUN rm -f /etc/nginx/conf.d/default.conf
COPY operator-console/nginx.conf /etc/nginx/conf.d/default.conf

# 빌드 산출물 복사
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]

