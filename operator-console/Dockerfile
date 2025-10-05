# Operator Console (Nginx only, quick fix: no Node build)
# - Vue 빌드( npm install / npm run build )를 제거
# - nginx.conf 적용 + 플레이스홀더 index.html 제공
# - gRPC-Web 프록시는 nginx.conf로 처리

FROM nginx:alpine

# 기본 서버 블록 제거
RUN rm /etc/nginx/conf.d/default.conf

# 프로젝트 내 설정 적용
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 간단한 플레이스홀더 UI (필요 시 실제 빌드 아티팩트로 대체)
RUN mkdir -p /usr/share/nginx/html
RUN printf '<!doctype html><html><head><meta charset="utf-8"><title>Operator Console</title><meta name="viewport" content="width=device-width, initial-scale=1"></head><body style="font-family:sans-serif;padding:24px;"><h1>Operator Console</h1><p>UI build artifacts not present. Nginx + gRPC-Web proxy are running.</p><p>Place your built <code>dist/</code> here or switch to the multi-stage Node build (see README note).</p></body></html>' > /usr/share/nginx/html/index.html

# 포트 노출 (compose에서 매핑됨)
EXPOSE 9988 

CMD ["nginx", "-g", "daemon off;"]
