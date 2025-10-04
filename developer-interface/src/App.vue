<template>
  <div id="app">
    <h1>SemantOS Developer Interface</h1>
    <TuningApproval />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import TuningApproval from './components/TuningApproval.vue';

export default defineComponent({
  name: 'App',
  components: {
    TuningApproval,
  },
});
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 20px;
}
</style>