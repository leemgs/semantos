# SemantOS Reproducibility Scaffold (Reproducibility Kit)

논문 **Design** 섹션의 5개 컴포넌트를 각각 컨테이너로 기동하고, **Evaluation·Setup**에 명시된 6가지 워크로드를 재현할 수 있는 최소 실행 스캐폴드입니다.
UI는 `operator-console`(웹 대시보드)로 제공되며, 클릭만으로 **Telemetry → KB → Reasoner → Safety** 제어 루프를 검증할 수 있습니다.
본 스캐폴드는 논문 **재현**을 위한 데모입니다. 실제 커널/eBPF/드라이버 조작은 포함하지 않으며, 인터페이스·흐름을 동일하게 유지해 **실서비스 컴포넌트**로 교체하기 쉽게 설계되어 있습니다.
---

## 🔗 빠른 시작 (Quickstart)

```bash
# 0) 권장 사전 준비
# - Docker 24+ / Docker Compose v2+
# - 7000~7003, 9988 포트가 비어있을 것

# 1) 전체 빌드 & 기동 & 로그 테일
./manual.sh

# 2) 웹 콘솔 접속
#   로컬:  http://localhost:9988/
#   원격:  http://<호스트 IP>:9988/

# 3) (선택) 워크로드 실행
./workloads/run_workload.sh            # 6개 전체 실행 (web/oltp/streaming/sensor/hpc_ml/audio)
./workloads/run_workload.sh streaming  # 단일 워크로드만 실행
```

---

## 🧱 구성 요소(5) & 포트

| 컴포넌트               | 포트   | 설명                                                               |
| ------------------ | ---- | ---------------------------------------------------------------- |
| `telemetry-agent`  | 7000 | 텔레메트리 스냅샷 발생 → KB 로그 → Reasoner 추천 요청 → Safety 적용 호출             |
| `kb-service`       | 7001 | 간단한 규칙 기반 retrieval(의존관계/힌트 모사)                                  |
| `reasoner`         | 7002 | KB 힌트 + 텔레메트리 기반 `TuningRecommendation{…, uncertainty_score}` 생성 |
| `safety-runtime`   | 7003 | `u ≥ τ(0.55)`이면 자동 롤백, 아니면 canary→ramp→full 적용                   |
| `operator-console` | 9988 | 웹 대시보드(UI). Health/Simulate/Manual Recommend & Apply             |

> **통신 방식:** 데모는 **HTTP/JSON(REST)** 로 상호 호출합니다.
> **gRPC 전환 경로:** `proto/semantos.proto`에 메시지/RPC 스키마가 포함되어 있습니다(현재는 REST로 모사).

---

## 🧪 워크로드 실행 (6)

`workloads/run_workload.sh`로 논문 Evaluation·Setup의 6가지 워크로드를 실행합니다.

* 전체 실행

  ```bash
  ./workloads/run_workload.sh
  ```
* 단일 실행

  ```bash
  ./workloads/run_workload.sh web
  ./workloads/run_workload.sh oltp
  ./workloads/run_workload.sh streaming
  ./workloads/run_workload.sh sensor
  ./workloads/run_workload.sh hpc_ml
  ./workloads/run_workload.sh audio
  ```

스크립트는 `telemetry-agent`의 `/simulate_once` 엔드포인트를 호출하여 **스냅샷 → 추천 → 세이프티 적용/롤백** 흐름을 연쇄적으로 실행합니다.

---

## 🖥️ Operator Console (웹 UI)

접속: `http://localhost:9988/` (또는 서버 IP)

UI에는 3개의 카드가 있습니다.

1. **Health** — `Check services` 클릭 시 각 서비스 `/health` 응답을 JSON으로 표시
2. **Simulate Telemetry** — 워크로드 선택 후 `Emit snapshot → rec → safety` 클릭:

   * 텔레메트리 → KB → Reasoner → Safety → 결과 로그(JSON)
3. **Manual Recommend/Apply** — `RQ latency (ms)` 값을 바꾸며

   * `Get recommendation` → Reasoner 추천(불확실도 포함) 확인
   * `Apply via safety` → τ=0.55 기준으로 적용/롤백 결과 확인

> UI 스크립트는 `operator-console/static/app.js`에서 로드됩니다.
> 실패 시에도 로그 영역에 상태/에러가 텍스트로 표시되도록 방어 코드를 포함합니다.

---

## 📦 디렉터리 구조(요약)

```
.
├─ docker-compose.yml
├─ manual.sh
├─ README.md                 # (이 파일 예시)
├─ proto/
│  └─ semantos.proto         # 논문 정의 gRPC 메시지/RPC 스키마 (데모는 REST로 모사)
├─ workloads/
│  └─ run_workload.sh        # 6 워크로드 실행 스크립트
├─ telemetry-agent/          # FastAPI 서비스 + Dockerfile
├─ kb-service/               # FastAPI 서비스 + Dockerfile
├─ reasoner/                 # FastAPI 서비스 + Dockerfile
├─ safety-runtime/           # FastAPI 서비스 + Dockerfile
└─ operator-console/
   ├─ app.py                 # FastAPI + HTML 템플릿(외부 app.js 로드)
   ├─ static/
   │  ├─ app.js              # UI 로직(Health/Simulate/Manual)
   │  └─ .keep
   └─ Dockerfile
```

---

## ⚙️ 환경 변수(컴포즈에서 주입)

`operator-console` → 내부 프록시 대상:

* `TELEMETRY_URL` = `http://telemetry-agent:7000`
* `KB_URL`        = `http://kb-service:7001`
* `REASONER_URL`  = `http://reasoner:7002`
* `SAFETY_URL`    = `http://safety-runtime:7003`

---

## 🔍 헬스체크/디버깅

* 브라우저/터미널에서 직접 확인:

  ```bash
  curl -s http://localhost:9988/api/telemetry/health
  curl -s http://localhost:9988/api/kb/health
  curl -s http://localhost:9988/api/reasoner/health
  curl -s http://localhost:9988/api/safety/health
  ```
* 컨테이너 로그:

  ```bash
  docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
  docker logs operator-console --tail=200
  ```

---

## 🧯 트러블슈팅

* **UI 버튼 눌러도 반응 없음**

  * 개발자도구(F12) Console에서 에러 확인
  * 강력 새로고침(Ctrl+F5) 또는 시크릿 모드로 재시도
  * `docker compose build operator-console && docker compose up -d operator-console`

* **정적 폴더(static) 오류**

  * `operator-console/static/.keep` 포함됨 + `app.py`에서 폴더 자동 생성
  * 그래도 오류면 컨테이너 재빌드

* **포트 충돌**

  * `9988`, `7000~7003` 포트를 다른 서비스가 점유 중인지 확인
  * 필요 시 `docker-compose.yml`에서 포트 수정

---

## 📄 라이선스

Apache-2.0 (필요 시 프로젝트 정책에 맞게 변경하십시오)

