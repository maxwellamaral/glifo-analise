<template>
  <div class="view">
    <h2>Modelo 3D</h2>

    <div v-if="!candidates.selected" class="card muted mt-1">
      Selecione um candidato na aba <strong>Candidatos</strong> primeiro.
    </div>

    <template v-else>
      <div class="card mt-1 controls">
        <label>Sequência: <input v-model="sequence" class="inp inp-elis" /></label>
        <label>Formato:
          <select v-model="fmt" class="inp">
            <option value="3mf">3MF</option>
            <option value="stl">STL</option>
          </select>
        </label>
        <label class="checkbox-label">
          <input type="checkbox" v-model="fullTest" />
          Teste completo (todos os pinos)
        </label>
        <button class="btn-primary" :disabled="model3d.generating" @click="gen">
          {{ model3d.generating ? 'Gerando...' : 'Gerar Modelo' }}
        </button>
      </div>

      <div v-if="model3d.error" class="card error-panel mt-1">{{ model3d.error }}</div>

      <!-- Arquivo gerado + viewer -->
      <div v-if="model3d.currentFile" class="card mt-1">
        <div class="row">
          <span class="file-name">{{ model3d.currentFile }}</span>
          <a :href="model3d.currentFile" download class="btn-sm">Download</a>
        </div>
        <iframe
          v-if="model3d.currentFile?.endsWith('.3mf') || model3d.currentFile?.endsWith('.stl')"
          :src="viewerSrc"
          class="viewer-frame"
          allowfullscreen
        />
      </div>

      <!-- Lista de arquivos existentes -->
      <div v-if="model3d.files.length" class="card mt-1">
        <h3>Arquivos gerados</h3>
        <ul class="file-list">
          <li
            v-for="f in model3d.files"
            :key="f"
            class="file-item"
            :class="{ active: model3d.currentFile?.endsWith(f) }"
            @click="loadFile(f)"
          >
            {{ f }}
          </li>
        </ul>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useCandidatesStore } from '@/stores/candidates'
import { useModel3DStore } from '@/stores/model3d'

const candidates = useCandidatesStore()
const model3d = useModel3DStore()

const sequence = ref('tqlDà')
const fmt = ref<'3mf' | 'stl'>('3mf')
const fullTest = ref(false)

const viewerSrc = computed(() => {
  if (!model3d.currentFile) return ''
  const fileUrl = encodeURIComponent(model3d.currentFile)
  return `/static/viewer3d.html?file=${fileUrl}`
})

async function gen() {
  if (!candidates.selected) return
  await model3d.generate(candidates.selected, sequence.value, fmt.value, fullTest.value)
}

function loadFile(name: string) {
  model3d.currentFile = `/output/${name}`
}

onMounted(() => model3d.fetchFiles())
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
h3 { margin: 0 0 .5rem; font-size: 1rem; }
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
.checkbox-label { gap: .5rem; cursor: pointer; }
.inp { background: var(--bg); color: var(--text); border: 1px solid var(--accent); border-radius: 4px; padding: .25rem .5rem; }
.inp-elis { font-family: 'ELIS', monospace; font-size: 1.15rem; letter-spacing: .05em; min-width: 12ch; }
.btn-primary { background: var(--primary); color: #fff; border: none; border-radius: 6px; padding: .4rem 1rem; cursor: pointer; }
.btn-primary:disabled { opacity: .5; cursor: not-allowed; }

.error-panel { border-color: #f66; color: #f66; }

.row { display: flex; align-items: center; justify-content: space-between; margin-bottom: .75rem; }
.file-name { font-family: monospace; font-size: .9rem; color: var(--muted); word-break: break-all; }

.viewer-frame {
  width: 100%;
  height: 480px;
  border: none;
  border-radius: 4px;
  margin-top: .5rem;
  background: #000;
}

.file-list { list-style: none; padding: 0; margin: 0; }
.file-item {
  padding: .4rem .6rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: .85rem;
  cursor: pointer;
  color: var(--muted);
}
.file-item:hover, .file-item.active { background: var(--accent); color: var(--text); }

.btn-sm {
  background: var(--accent); color: var(--text);
  border: none; border-radius: 4px;
  padding: .3rem .7rem; cursor: pointer;
  text-decoration: none; font-size: .85rem;
}
</style>
