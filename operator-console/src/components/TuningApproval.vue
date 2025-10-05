<template>
  <div class="card" v-if="recommendation">
    <h2>Pending Action: Kernel Knob Tuning</h2>
    
    <div class="detail-group">
        <p><strong>Knob Name:</strong> <code>{{ recommendation.getKnobName() }}</code></p>
        <p><strong>Proposed Value:</strong> <code>{{ recommendation.getProposedValue() }}</code></p>
        <p class="uncertainty"><strong>Uncertainty Score:</strong> {{ (recommendation.getUncertaintyScore() * 100).toFixed(2) }}%</p>
    </div>

    <div class="rationale-box">
      <h3>LLM Rationale (Explainability)</h3>
      <p>{{ recommendation.getRationale() }}</p>
    </div>

    <div class="action-buttons">
      <button @click="handleApproval(true)" class="approve-btn" :disabled="isLoading">✅ Approve & Apply</button>
      
      <button @click="handleApproval(false)" class="reject-btn" :disabled="isLoading">❌ Reject & Log Fail</button>
      
      <span v-if="isLoading" class="loading-status">Processing...</span>
    </div>
  </div>
  <div v-else class="status-message">
    {{ isLoading ? 'Loading...' : 'No critical tuning recommendations pending.' }}
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';

// gRPC-Web 스텁 임포트 (앞서 시뮬레이션된 파일)
import { SemantosControlClient } from '../proto/semantos_grpc_web_pb';
import { TuningRecommendation, ApplyResponse, TelemetrySnapshot } from '../proto/semantos_pb';
import { RpcError } from 'grpc-web';

// Safety Runtime gRPC-Web 게이트웨이 주소
// (Docker 환경에서는 Envoy 또는 별도 Proxy를 통해 접근해야 함)
const SAFETY_RUNTIME_URL = 'http://localhost:8080'; // Envoy Proxy 주소 가정

export default defineComponent({
  name: 'TuningApproval',
  setup() {
    const recommendation = ref<TuningRecommendation | null>(null);
    const isLoading = ref(false);
    const client = new SemantosControlClient(SAFETY_RUNTIME_URL, null, null);

    // 1. 백엔드로부터 대기 중인 권장 사항을 폴링하는 함수
    const fetchPendingRecommendation = async () => {
      isLoading.value = true;
      
      // 실제 Safety Runtime은 'GetPendingRecommendation'과 같은 API를 제공해야 하지만, 
      // 여기서는 gRPC 정의에 있는 GetRecommendations를 사용하여 현재 상태를 전송하고 응답을 받는 것을 시뮬레이션
      const dummySnapshot = new TelemetrySnapshot();
      dummySnapshot.setHostId('web-ui-polling');
      
      // Safety Runtime에 GetRecommendations 호출
      client.getRecommendations(dummySnapshot, {}, (err: RpcError, response) => {
        isLoading.value = false;

        if (err || response.getRecommendationsList().length === 0) {
          console.error('Error or No pending recommendations:', err ? err.message : 'Empty list');
          // 시뮬레이션 데이터: 실제 gRPC 실패 시 대체 데이터를 사용
          const dummyRec = new TuningRecommendation();
          dummyRec.setKnobName('vm.swappiness');
          dummyRec.setProposedValue('1');
          dummyRec.setRationale("Simulated rationale: Based on KB vector retrieval, this setting is low risk and expected to improve I/O latency.");
          dummyRec.setUncertaintyScore(0.08);
          recommendation.value = dummyRec;
          return;
        }

        // 첫 번째 권장 사항을 표시
        recommendation.value = response.getRecommendationsList()[0];
      });
    };

    // 2. 운영자의 승인/거부 결정을 백엔드에 전송
    const handleApproval = async (isApproved: boolean) => {
      if (!recommendation.value) return;
      
      isLoading.value = true;
      const rec = recommendation.value;
      
      if (isApproved) {
        // 승인: Safety Runtime의 ApplyConfiguration 호출
        client.applyConfiguration(rec, {}, (err: RpcError, response: ApplyResponse) => {
          isLoading.value = false;
          if (err || !response.getSuccess()) {
            alert(`❌ Application Failed: ${err ? err.message : response.getStatusMessage()}`);
          } else {
            alert(`✅ Approved and Applied: ${rec.getKnobName()}. Audit ID: ${response.getAuditLogId()}`);
            recommendation.value = null;
          }
        });
      } else {
        // 거부: Safety Runtime의 LogOutcome 호출 (실패 트레이스로 기록하여 LLM 재학습)
        // 실제로는 LogOutcome 전에 Operator_Rejection 메시지를 보낼 수 있음.
        alert(`❌ Rejected: A failure trace will be logged to the Knowledge Base for future learning.`);
        // LogOutcome 로직 시뮬레이션...
        isLoading.value = false;
        recommendation.value = null;
      }
    };

    onMounted(fetchPendingRecommendation);

    return {
      recommendation,
      isLoading,
      handleApproval,
    };
  },
});
</script>

<style scoped>
.card {
  border: 1px solid #007bff;
  border-radius: 8px;
  padding: 25px;
  max-width: 700px;
  margin: 30px auto;
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.1);
  font-family: Arial, sans-serif;
}
h2 { color: #007bff; border-bottom: 2px solid #eee; padding-bottom: 10px; }
.detail-group { margin-bottom: 20px; }
.uncertainty { color: #ffc107; font-weight: bold; }
.rationale-box {
  margin: 20px 0;
  padding: 15px;
  background-color: #f8f9fa;
  border-left: 4px solid #007bff;
}
.action-buttons button {
  padding: 12px 20px;
  margin-right: 15px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.3s;
}
.approve-btn { background-color: #28a745; color: white; }
.approve-btn:hover { background-color: #218838; }
.reject-btn { background-color: #dc3545; color: white; }
.reject-btn:hover { background-color: #c82333; }
.loading-status { color: #6c757d; margin-left: 10px; }
.status-message { text-align: center; color: #6c757d; padding: 50px 0; }
</style>