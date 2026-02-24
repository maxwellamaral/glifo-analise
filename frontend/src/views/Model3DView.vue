<template>
  <div class="view">
    <h2>Modelo 3D</h2>

    <div v-if="!candidates.selected" class="card muted mt-1">
      Selecione um candidato na aba <strong>Candidatos</strong> primeiro.
    </div>

    <template v-else>
      <div class="card mt-1 controls">
        <label class="label-seq">Sequência:
          <input v-model="sequence" class="inp inp-elis" />
          <button class="btn-picker" title="Mapa de glifos ELIS" @click="showPicker = true">⌨</button>
        </label>
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
            :key="f.name"
            class="file-item"
            :class="{ active: model3d.currentFile?.endsWith(f.name) }"
            @click="loadFile(f.name)"
            @mouseenter="showTooltip(f, $event)"
            @mouseleave="hideTooltip"
          >
            <span class="file-item-name">{{ f.name }}</span>
            <button
              class="file-delete-btn"
              title="Excluir arquivo"
              @click.stop="confirmDeleteFile(f.name)"
            >&#x1F5D1;</button>
          </li>
        </ul>
      </div>
    </template>

    <!-- Mapa de glifos ELIS -->
    <GlyphPickerModal v-if="showPicker" v-model="sequence" @close="showPicker = false" />

    <!-- Tooltip de metadados do arquivo -->
    <Teleport to="body">
      <div v-if="tooltipFile" class="file-tooltip" :style="tooltipStyle">
        <!-- Seção: arquivo -->
        <div class="tt-section-title">Arquivo</div>
        <div class="tt-row"><span class="tt-label">Nome</span><span class="tt-val">{{ tooltipFile.name }}</span></div>
        <div class="tt-row"><span class="tt-label">Formato</span><span class="tt-val">{{ tooltipFile.format }}</span></div>
        <div class="tt-row"><span class="tt-label">Tamanho</span><span class="tt-val">{{ formatSize(tooltipFile.size) }}</span></div>
        <div class="tt-row"><span class="tt-label">Modificado</span><span class="tt-val">{{ formatDate(tooltipFile.modified) }}</span></div>

        <!-- Seção: física da célula -->
        <template v-if="tooltipFile.physics">
          <div class="tt-divider"></div>
          <div class="tt-section-title">Física da Célula</div>
          <div class="tt-row"><span class="tt-label">Resolução</span><span class="tt-val">{{ tooltipFile.physics.resolution }}</span></div>
          <div class="tt-row"><span class="tt-label">Espaçamento</span><span class="tt-val">{{ tooltipFile.physics.spacing_mm.toFixed(1) }} mm</span></div>
          <div class="tt-row"><span class="tt-label">Célula W×H</span><span class="tt-val">{{ tooltipFile.physics.cell_w_mm.toFixed(1) }} × {{ tooltipFile.physics.cell_h_mm.toFixed(1) }} mm</span></div>
          <div class="tt-row"><span class="tt-label">Gap</span><span class="tt-val">{{ tooltipFile.physics.gap_mm.toFixed(1) }} mm</span></div>
          <div class="tt-row"><span class="tt-label">Aspecto</span><span class="tt-val">{{ tooltipFile.physics.aspect_ratio?.toFixed(2) }}×</span></div>
          <div class="tt-row"><span class="tt-label">Modo</span><span class="tt-val tt-mode" :data-mode="tooltipFile.physics.reading_mode">{{ tooltipFile.physics.reading_mode }}</span></div>
          <div class="tt-row"><span class="tt-label">Glifos/tira</span><span class="tt-val">{{ tooltipFile.physics.seq_capacity }}</span></div>

          <!-- Seção: ISO 11548-2 -->
          <div class="tt-divider"></div>
          <div class="tt-section-title">ISO 11548-2</div>
          <div v-for="c in tooltipFile.physics.iso" :key="c.label" class="tt-iso-row">
            <span class="tt-iso-badge" :class="c.ok ? 'ok' : 'fail'">{{ c.ok ? '✓' : '✗' }}</span>
            <span class="tt-iso-label">{{ c.label }}</span>
            <span class="tt-iso-detail">{{ c.detail }}</span>
          </div>
        </template>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useCandidatesStore } from '@/stores/candidates'
import { useModel3DStore, type Model3DFileInfo } from '@/stores/model3d'
import GlyphPickerModal from '@/components/GlyphPickerModal.vue'

const candidates = useCandidatesStore()
const model3d = useModel3DStore()

const sequence = ref('tqlDà')
const showPicker = ref(false)
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

// ── Tooltip ──────────────────────────────────────────────────────────────
const tooltipFile = ref<Model3DFileInfo | null>(null)
const tooltipStyle = ref<Record<string, string>>({})

function showTooltip(f: Model3DFileInfo, e: MouseEvent) {
  tooltipFile.value = f
  tooltipStyle.value = { top: `${e.clientY + 14}px`, left: `${e.clientX + 14}px` }
}
function hideTooltip() { tooltipFile.value = null }

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}
function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('pt-BR')
}

async function confirmDeleteFile(name: string) {
  if (!confirm(`Excluir "${name}"?`)) return
  await model3d.deleteFile(name)
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
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: .4rem .6rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: .85rem;
  cursor: pointer;
  color: var(--muted);
  gap: .5rem;
  transition: background .12s, color .12s;
}
.file-item:hover, .file-item.active { background: var(--accent); color: var(--text); }
.file-item-name { flex: 1; word-break: break-all; }
.file-delete-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: .85rem;
  padding: .1rem .3rem;
  border-radius: 3px;
  opacity: .45;
  transition: opacity .15s, background .15s;
  flex-shrink: 0;
  line-height: 1;
}
.file-delete-btn:hover { opacity: 1; background: rgba(255, 80, 80, .25); }

/* ── Tooltip ───────────────────────────────────────────────────── */
.file-tooltip {
  position: fixed;
  z-index: 99999;
  background: var(--surface);
  border: 1px solid var(--accent);
  border-radius: 6px;
  padding: .65rem .9rem;
  font-size: .78rem;
  pointer-events: none;
  box-shadow: 0 4px 18px rgba(0,0,0,.45);
  min-width: 300px;
  max-width: 380px;
}
.tt-section-title {
  font-size: .7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--primary);
  margin-bottom: .3rem;
  margin-top: .1rem;
}
.tt-divider { border-top: 1px solid var(--accent); margin: .45rem 0 .4rem; }
.tt-row { display: flex; gap: .5rem; margin-bottom: .2rem; align-items: baseline; }
.tt-label { color: var(--muted); min-width: 90px; flex-shrink: 0; }
.tt-val { color: var(--text); word-break: break-all; }
.tt-mode[data-mode="1-dedo"]       { color: #4caf50; }
.tt-mode[data-mode="multi-dedo"]   { color: #ff9800; }
.tt-mode[data-mode="fora-de-alcance"] { color: #f44336; }
.tt-iso-row {
  display: flex;
  align-items: center;
  gap: .35rem;
  margin-bottom: .18rem;
}
.tt-iso-badge {
  font-size: .75rem;
  font-weight: 700;
  min-width: 1.1rem;
  text-align: center;
}
.tt-iso-badge.ok   { color: #4caf50; }
.tt-iso-badge.fail { color: #f44336; }
.tt-iso-label { color: var(--muted); flex: 1; }
.tt-iso-detail { color: var(--text); white-space: nowrap; }

.btn-sm {
  background: var(--accent); color: var(--text);
  border: none; border-radius: 4px;
  padding: .3rem .7rem; cursor: pointer;
  text-decoration: none; font-size: .85rem;
}
.label-seq { display: flex; align-items: center; gap: .4rem; }
.btn-picker {
  background: var(--accent); color: var(--text);
  border: 1px solid var(--accent); border-radius: 4px;
  padding: .22rem .5rem; cursor: pointer; font-size: .9rem;
  line-height: 1; transition: border-color .15s;
}
.btn-picker:hover { border-color: var(--primary); color: var(--primary); }
</style>
