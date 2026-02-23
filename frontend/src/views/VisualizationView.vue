<template>
  <div class="view">
    <h2>Visualização</h2>

    <div v-if="!candidates.selected" class="card muted mt-1">
      Selecione um candidato na aba <strong>Candidatos</strong> primeiro.
    </div>

    <template v-else>
      <div class="card mt-1 controls">
        <label>Sequência: <input v-model="sequence" class="inp inp-elis" /></label>
        <label>Tipo:
          <select v-model="visType" class="inp">
            <option value="strip">Tira completa</option>
            <option value="cells">Por glifo</option>
            <option value="grid">Grade diagnóstico</option>
          </select>
        </label>
        <button class="btn-primary" :disabled="loading" @click="generate">
          {{ loading ? 'Gerando...' : 'Gerar' }}
        </button>
      </div>

      <div v-if="error" class="card error-panel mt-1">{{ error }}</div>

      <!-- Strip / Grid: arquivo único -->
      <div v-if="result?.file" class="card mt-1 img-card">
        <img :src="result.file" class="preview-img" alt="Preview" />
        <a :href="result.file" download class="btn-sm dl-btn">Download</a>
      </div>

      <!-- Cells: múltiplos arquivos -->
      <div v-if="result?.files?.length" class="card mt-1">
        <div class="cells-grid">
          <div v-for="f in result.files" :key="f" class="cell-item">
            <img :src="f" class="cell-img" :title="f" alt="" />
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'
import { useCandidatesStore } from '@/stores/candidates'

const candidates = useCandidatesStore()
const sequence = ref('tqlDà')
const visType = ref<'strip' | 'cells' | 'grid'>('strip')
const loading = ref(false)
const error = ref<string | null>(null)
const result = ref<{ file?: string; files?: string[] } | null>(null)

async function generate() {
  if (!candidates.selected) return
  loading.value = true
  error.value = null
  result.value = null
  try {
    const r = await axios.post('/api/visualization/generate', {
      type: visType.value,
      candidate: candidates.selected,
      sequence: sequence.value,
    })
    result.value = r.data
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
@font-face {
  font-family: 'ELIS';
  src: url('/static/elis.ttf') format('truetype');
  font-weight: normal;
  font-style: normal;
}

.view { max-width: 900px; }
h2 { margin: 0 0 .5rem; }
.mt-1 { margin-top: 1rem; }
.muted { color: var(--muted); font-size: .9rem; }

.card {
  background: var(--surface);
  border: 1px solid var(--accent);
  border-radius: 8px;
  padding: 1rem;
}

.controls { display: flex; gap: 1rem; align-items: center; flex-wrap: wrap; }
.controls label { display: flex; align-items: center; gap: .4rem; font-size: .9rem; }
.inp { background: var(--bg); color: var(--text); border: 1px solid var(--accent); border-radius: 4px; padding: .25rem .5rem; }
.inp-elis { font-family: 'ELIS', monospace; font-size: 1.15rem; letter-spacing: .05em; min-width: 12ch; }
.btn-primary { background: var(--primary); color: #fff; border: none; border-radius: 6px; padding: .4rem 1rem; cursor: pointer; }
.btn-primary:disabled { opacity: .5; cursor: not-allowed; }

.error-panel { border-color: #f66; color: #f66; }

.img-card { text-align: center; }
.preview-img { max-width: 100%; border-radius: 4px; }
.dl-btn { display: inline-block; margin-top: .5rem; }

.cells-grid { display: flex; flex-wrap: wrap; gap: .5rem; }
.cell-img { width: 120px; height: auto; border-radius: 4px; }

.btn-sm {
  background: var(--accent); color: var(--text);
  border: none; border-radius: 4px;
  padding: .2rem .6rem; cursor: pointer; text-decoration: none; font-size: .85rem;
}
</style>
