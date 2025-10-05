# Operator Console (Debian-base NGINX with grpc_web built-in)
FROM nginx:1.27-bookworm

# 기본 서버블록 제거 후 우리의 설정 적용
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 정적 파일(빌드 산출물)이 있다면 /usr/share/nginx/html/ 로 복사
# (현재는 외부에서 넣는다고 가정. 필요 시 아래 주석 해제)
# COPY dist/ /usr/share/nginx/html/

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]

