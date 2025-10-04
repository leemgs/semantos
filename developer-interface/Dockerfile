# --- 1단계: 빌드 환경 (Node.js) ---
FROM node:20-alpine as builder

# 작업 디렉토리 설정
WORKDIR /app

# 패키지 파일 복사
COPY package*.json ./

# 종속성 설치
RUN npm install

# 소스 코드 복사
COPY . .

# Vue 애플리케이션 빌드
# VUE_APP_GRPC_WEB_URL 등 환경 변수를 빌드 시 주입할 수 있음.
RUN npm run build


# --- 2단계: 실행 환경 (Nginx) ---
FROM nginx:alpine

# Nginx 설정을 위한 포트 노출 (gRPC-Web Proxy와 Developer Interface 모두를 위해 8080 사용 가정)
EXPOSE 8080

# Nginx 기본 설정 파일 제거
RUN rm /etc/nginx/conf.d/default.conf

# Nginx 설정 파일 추가
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 빌드된 Vue 앱 파일을 Nginx 웹 루트로 복사
COPY --from=builder /app/dist /usr/share/nginx/html

# 컨테이너 시작 시 Nginx 실행
CMD ["nginx", "-g", "daemon off;"]