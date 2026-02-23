<template>
  <div class="view">
    <h2>Análise de Resolução</h2>
    <p class="muted">Executa a análise completa de todas as combinações de grade e espaçamento.</p>

    <div class="card">
      <div class="row">
        <div>
          <span class="badge" :class="statusClass">{{ store.status }}</span>
          <span v-if="store.taskId" class="muted ml-1">ID: {{ store.taskId }}</span>
        </div>
        <button class="btn-primary" :disabled="store.status === 'running'" @click="run">
          {{ store.status === 'running' ? 'Analisando...' : 'Iniciar Análise' }}
        </button>
      </div>

      <div v-if="store.status === 'running' || store.progress > 0" class="progress-wrap">
        <div class="progress-bar" :style="{ width: store.progress + '%' }"></div>
        <span class="progress-label">{{ store.progress.toFixed(1) }}%</span>
      </div>
    </div>

    <div v-if="store.logs.length" class="card log-panel">
      <div class="log-scroll" ref="logEl">
        <div v-for="(msg, i) in store.logs" :key="i" class="log-line">
          <span class="log-pct">{{ msg.pct.toFixed(1) }}%</span>
          <span>{{ msg.line }}</span>
        </div>
      </div>
    </div>

    <div v-if="store.error" class="card error-panel">
      <strong>Erro:</strong> {{ store.error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useAnalysisStore } from '@/stores/analysis'

const store = useAnalysisStore()
const logEl = ref<HTMLElement | null>(null)

const statusClass = computed(() => ({
  'badge-idle': store.status === 'idle',
  'badge-running': store.status === 'running',
  'badge-done': store.status === 'done',
  'badge-error': store.status === 'error',
}))

watch(() => store.logs.length, async () => {
  await nextTick()
  if (logEl.value) logEl.value.scrollTop = logEl.value.scrollHeight
})

async function run() {
  await store.runAnalysis()
}
</script>

<style scoped>
.view { max-width: 860px; }
h2 { margin: 0 0 .5rem; }
.muted { color: var(--muted); font-size: .9rem; }
.ml-1 { margin-left: .5rem; }

.card {
  background: var(--surface);
  border: 1px solid var(--accent);
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.btn-primary {
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: .5rem 1.2rem;
  cursor: pointer;
  font-size: .95rem;
}
.btn-primary:disabled { opacity: .5; cursor: not-allowed; }

.badge {
  display: inline-block;
  padding: .2rem .6rem;
  border-radius: 4px;
  font-size: .8rem;
  font-weight: 600;
}
.badge-idle    { background: #333; color: #aaa; }
.badge-running { background: #1a4080; color: #6cf; }
.badge-done    { background: #1a4020; color: #6f6; }
.badge-error   { background: #401a1a; color: #f66; }

.progress-wrap {
  position: relative;
  height: 18px;
  background: var(--accent);
  border-radius: 9px;
  overflow: hidden;
  margin-top: .75rem;
}
.progress-bar {
  height: 100%;
  background: var(--primary);
  transition: width .3s;
}
.progress-label {
  position: absolute;
  right: 8px;
  top: 0;
  line-height: 18px;
  font-size: .75rem;
  color: #fff;
}

.log-panel { max-height: 300px; padding: 0; }
.log-scroll {
  height: 300px;
  overflow-y: auto;
  padding: .75rem;
  font-family: monospace;
  font-size: .8rem;
}
.log-line { display: flex; gap: .75rem; padding: .1rem 0; }
.log-pct  { color: var(--primary); min-width: 4rem; text-align: right; }

.error-panel { border-color: #f66; color: #f66; }
</style>
