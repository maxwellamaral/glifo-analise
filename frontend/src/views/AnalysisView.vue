<template>
  <div class="view">
    <h2>Análise de Resolução</h2>
    <p class="muted">Executa a análise completa de todas as combinações de grade e espaçamento.</p>

    <!-- Controle + status -->
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

    <!-- Painel de parâmetros colapsável -->
    <div class="card params-card">
      <button class="params-toggle" @click="paramsOpen = !paramsOpen">
        <span>⚙ Parâmetros de Análise</span>
        <span class="toggle-arrow" :class="{ open: paramsOpen }">▶</span>
      </button>

      <!-- Resumo quando colapsado -->
      <div v-if="!paramsOpen && local" class="params-summary">
        <span>Espaç.: {{ local.pin_spacing_candidates.join(', ') }} mm</span>
        <span>Dens.: {{ local.density_min }}–{{ local.density_max }}</span>
        <span>Cobert.: ≥{{ local.min_coverage_pct }}%</span>
        <span>Seq. mín.: {{ local.seq_glyph_min }}</span>
      </div>

      <div v-if="paramsOpen && local" class="params-body">

        <!-- Seção: Espaçamento entre pinos -->
        <section class="param-section">
          <h4>Espaçamentos Testados (mm)</h4>
          <p class="hint">Separados por vírgula. Valores padrão: 2.5, 3.0, 3.5</p>
          <input
            type="text"
            class="param-input wide"
            :value="local.pin_spacing_candidates.join(', ')"
            @change="updateSpacings(($event.target as HTMLInputElement).value)"
          />
        </section>

        <!-- Seção: Limiares Psicofísicos -->
        <section class="param-section">
          <h4>Limiares Psicofísicos</h4>
          <div class="param-grid">
            <label>
              <span>Densidade mínima</span>
              <div class="range-row">
                <input type="range" min="0" max="0.5" step="0.01" v-model.number="local.density_min" />
                <input type="number" min="0" max="0.5" step="0.01" v-model.number="local.density_min" class="param-number" />
              </div>
            </label>
            <label>
              <span>Densidade máxima</span>
              <div class="range-row">
                <input type="range" min="0.1" max="1" step="0.01" v-model.number="local.density_max" />
                <input type="number" min="0.1" max="1" step="0.01" v-model.number="local.density_max" class="param-number" />
              </div>
            </label>
            <label>
              <span>Complexidade de borda mín.</span>
              <div class="range-row">
                <input type="range" min="0" max="0.5" step="0.01" v-model.number="local.edge_complexity_min" />
                <input type="number" min="0" max="0.5" step="0.01" v-model.number="local.edge_complexity_min" class="param-number" />
              </div>
            </label>
            <label>
              <span>IoU mínimo (fidelidade estrutural)</span>
              <div class="range-row">
                <input type="range" min="0" max="1" step="0.01" v-model.number="local.iou_min" />
                <input type="number" min="0" max="1" step="0.01" v-model.number="local.iou_min" class="param-number" />
              </div>
            </label>
          </div>
        </section>

        <!-- Seção: Limites de Dedo -->
        <section class="param-section">
          <h4>Limites de Toque</h4>
          <div class="param-grid">
            <label>
              <span>Máx. área 1 dedo (mm)</span>
              <div class="range-row">
                <input type="range" min="5" max="60" step="0.5" v-model.number="local.max_finger_area_mm" />
                <input type="number" min="5" max="60" step="0.5" v-model.number="local.max_finger_area_mm" class="param-number" />
              </div>
            </label>
            <label>
              <span>Máx. área multi-dedo (mm)</span>
              <div class="range-row">
                <input type="range" min="20" max="120" step="1" v-model.number="local.max_multi_finger_mm" />
                <input type="number" min="20" max="120" step="1" v-model.number="local.max_multi_finger_mm" class="param-number" />
              </div>
            </label>
          </div>
        </section>

        <!-- Seção: Filtro de Candidatos -->
        <section class="param-section">
          <h4>Filtro de Candidatos</h4>
          <div class="param-grid">
            <label>
              <span>Sequência mínima de glifos</span>
              <div class="range-row">
                <input type="range" min="1" max="10" step="1" v-model.number="local.seq_glyph_min" />
                <input type="number" min="1" max="10" step="1" v-model.number="local.seq_glyph_min" class="param-number" />
              </div>
            </label>
            <label>
              <span>Cobertura mínima do repertório (%)</span>
              <div class="range-row">
                <input type="range" min="50" max="100" step="1" v-model.number="local.min_coverage_pct" />
                <input type="number" min="50" max="100" step="1" v-model.number="local.min_coverage_pct" class="param-number" />
              </div>
            </label>
          </div>
        </section>

        <div class="params-actions">
          <button class="btn-ghost" @click="resetDefaults">↩ Restaurar Padrões</button>
        </div>
      </div>
    </div>

    <!-- Log -->
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
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useAnalysisStore, type AnalysisParams } from '@/stores/analysis'

const store = useAnalysisStore()
const logEl = ref<HTMLElement | null>(null)
const paramsOpen = ref(false)
const local = ref<AnalysisParams | null>(null)

onMounted(async () => {
  await store.fetchStatus()
  await store.fetchDefaults()
  if (store.params) local.value = { ...store.params, pin_spacing_candidates: [...store.params.pin_spacing_candidates] }
})

const statusClass = computed(() => ({
  'badge-idle':    store.status === 'idle',
  'badge-running': store.status === 'running',
  'badge-done':    store.status === 'done',
  'badge-error':   store.status === 'error',
}))

watch(() => store.logs.length, async () => {
  await nextTick()
  if (logEl.value) logEl.value.scrollTop = logEl.value.scrollHeight
})

function updateSpacings(raw: string) {
  if (!local.value) return
  const vals = raw.split(',').map(v => parseFloat(v.trim())).filter(v => !isNaN(v) && v > 0)
  if (vals.length) local.value.pin_spacing_candidates = vals
}

async function resetDefaults() {
  await store.fetchDefaults()
  if (store.params) local.value = { ...store.params, pin_spacing_candidates: [...store.params.pin_spacing_candidates] }
}

async function run() {
  await store.runAnalysis(local.value ?? undefined)
}
</script>

<style scoped>
.view { max-width: 860px; }
h2 { margin: 0 0 .5rem; }
.muted  { color: var(--muted); font-size: .9rem; }
.ml-1   { margin-left: .5rem; }

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

/* ---------- Botões ---------- */
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

.btn-ghost {
  background: transparent;
  border: 1px solid var(--accent);
  color: var(--muted);
  border-radius: 6px;
  padding: .35rem .85rem;
  cursor: pointer;
  font-size: .85rem;
  transition: border-color .2s, color .2s;
}
.btn-ghost:hover { border-color: var(--primary); color: var(--primary); }

/* ---------- Badge ---------- */
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

/* ---------- Barra de progresso ---------- */
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

/* ---------- Painel de parâmetros ---------- */
.params-card { padding: 0; }

.params-toggle {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: .85rem 1rem;
  background: transparent;
  border: none;
  color: var(--fg, #ddd);
  font-size: .95rem;
  font-weight: 600;
  cursor: pointer;
  text-align: left;
}
.params-toggle:hover { color: var(--primary); }

.toggle-arrow {
  display: inline-block;
  transition: transform .2s;
  font-size: .75rem;
  color: var(--muted);
}
.toggle-arrow.open { transform: rotate(90deg); }

.params-summary {
  display: flex;
  gap: 1.5rem;
  padding: 0 1rem .75rem;
  font-size: .82rem;
  color: var(--muted);
  flex-wrap: wrap;
}

.params-body {
  padding: 0 1rem 1rem;
  border-top: 1px solid var(--accent);
}

.param-section {
  margin-top: 1rem;
}
.param-section h4 {
  margin: 0 0 .25rem;
  font-size: .85rem;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: var(--primary);
}
.hint {
  font-size: .78rem;
  color: var(--muted);
  margin: 0 0 .4rem;
}

.param-input.wide {
  width: 100%;
  background: var(--accent);
  border: 1px solid #444;
  border-radius: 4px;
  color: var(--fg, #ddd);
  padding: .35rem .6rem;
  font-size: .9rem;
  box-sizing: border-box;
}

.param-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: .75rem;
}
@media (max-width: 600px) { .param-grid { grid-template-columns: 1fr; } }

.param-grid label {
  display: flex;
  flex-direction: column;
  gap: .3rem;
  font-size: .85rem;
  color: var(--fg, #ddd);
}
.param-grid label span { color: var(--muted); font-size: .78rem; }

.range-row {
  display: flex;
  align-items: center;
  gap: .5rem;
}
.range-row input[type="range"] {
  flex: 1;
  accent-color: var(--primary);
}
.param-number {
  width: 5.5rem;
  background: var(--accent);
  border: 1px solid #444;
  border-radius: 4px;
  color: var(--fg, #ddd);
  padding: .2rem .4rem;
  font-size: .85rem;
  text-align: right;
}

.params-actions {
  margin-top: 1rem;
  display: flex;
  justify-content: flex-end;
}

/* ---------- Log ---------- */
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

