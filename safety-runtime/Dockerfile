# --- 1단계: 빌드 스테이지 ---
FROM golang:1.22-alpine AS builder

# 작업 디렉토리 설정
WORKDIR /app

# (변경) go.mod/go.sum이 레포에 없으므로, 모듈을 빌드 시 생성합니다.
RUN go mod init semantos/safety-runtime

# 소스 코드 복사 (루트 컨텍스트 기준)
COPY safety-runtime/cmd ./cmd

# 외부 의존성이 없으므로 go mod tidy는 선택 사항이지만, 추후 확장성을 고려해 포함
RUN go mod tidy

# 바이너리 빌드
RUN go build -o safety-runtime ./cmd

# --- 2단계: 런타임 스테이지 ---
FROM alpine:latest

# 작업 디렉토리 설정
WORKDIR /app

# 빌드된 바이너리 복사
COPY --from=builder /app/safety-runtime /usr/local/bin/safety-runtime

# gRPC 포트 (시뮬레이션 모드이지만 향후 gRPC 사용 대비)
EXPOSE 50051

# 실행 명령
CMD ["safety-runtime"]
