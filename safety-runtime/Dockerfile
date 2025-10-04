# --- 1단계: 빌드 스테이지 ---
FROM golang:1.22-alpine AS builder

# 작업 디렉토리 설정
WORKDIR /app

# Go 모듈 및 소스코드 복사
COPY go.mod go.sum ./
# 모듈 다운로드
RUN go mod download

# 소스코드 복사
COPY cmd/ /app/cmd/

# 애플리케이션 빌드
# CGO_ENABLED=0은 정적 링크를 보장하여 Alpine Linux에서 실행 가능하게 합니다.
RUN CGO_ENABLED=0 go build -o /safety-runtime ./cmd/safety-runtime.go

# --- 2단계: 실행 스테이지 ---
# 가볍고 안전한 실행 환경을 위해 Scratch(완전히 비어 있는) 또는 Alpine을 사용합니다.
FROM alpine:latest

# Safety Runtime이 커널 매개변수(/proc/sys)를 변경하려면 루트 권한이 필요합니다.
# 실제 프로덕션 환경에서는 Drop Capabilities를 사용하여 권한을 최소화하는 것이 좋습니다.

# 작업 디렉토리 설정
WORKDIR /

# 빌드 스테이지에서 컴파일된 바이너리를 복사
COPY --from=builder /safety-runtime /safety-runtime

# gRPC 리스닝 포트 노출 (선택 사항이지만 문서화를 위해 추가)
EXPOSE 50051

# 애플리케이션 실행
# 컨테이너 실행 시 main 함수가 시작되며 gRPC 서버가 구동됩니다.
CMD ["/safety-runtime"]