<template>
  <div class="view">
    <h2>Visualização</h2>

    <div v-if="!candidates.selected" class="card muted mt-1">
      Selecione um candidato na aba <strong>Candidatos</strong> primeiro.
    </div>

    <template v-else>
      <div class="card mt-1 controls">
        <label class="label-seq">Sequência:
          <input v-model="sequence" class="inp inp-elis" />
          <button class="btn-picker" title="Mapa de glifos ELIS" @click="showPicker = true">⌨</button>
        </label>
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

      <!-- Strip / Grid: visualizador completo -->
      <div v-if="result?.file" class="card mt-1 viewer-card" :class="{ fullscreen: isFullscreen }">
        <!-- Barra de ferramentas -->
        <div class="viewer-toolbar">
          <div class="toolbar-group">
            <button class="tool-btn" title="Diminuir zoom (−)" @click="zoomStep(-1)">−</button>
            <span class="zoom-label" @click="resetZoom" title="Clique para redefinir">{{ zoomPct }}%</span>
            <button class="tool-btn" title="Aumentar zoom (+)" @click="zoomStep(1)">+</button>
          </div>
          <div class="toolbar-group">
            <button class="tool-btn" title="Ajustar à tela" @click="fitToView">⊡</button>
            <button class="tool-btn" title="Tamanho real (100%)" @click="resetZoom">1:1</button>
            <button class="tool-btn" title="Girar 90°" @click="rotate90">↻</button>
          </div>
          <div class="toolbar-group">
            <button class="tool-btn" :title="isFullscreen ? 'Sair da tela cheia (Esc)' : 'Tela cheia'" @click="toggleFullscreen">{{ isFullscreen ? '⤡' : '⤢' }}</button>
            <a :href="result.file" download class="tool-btn tool-link" title="Download">⬇</a>
          </div>
        </div>

        <!-- Área de visualização -->
        <div
          ref="viewportEl"
          class="viewer-viewport"
          :class="{ grabbing: isDragging }"
          @wheel.prevent="onWheel"
          @mousedown="startDrag"
          @mousemove="onDrag"
          @mouseup="endDrag"
          @mouseleave="endDrag"
          @dblclick="fitToView"
        >
          <img
            ref="imgEl"
            :src="result.file"
            class="viewer-img"
            :style="imgStyle"
            alt="Preview"
            draggable="false"
            @load="fitToView"
          />
        </div>

        <!-- Dica de uso -->
        <p class="viewer-hint">Scroll para zoom · Arrastar para mover · Duplo clique para ajustar</p>
      </div>

      <!-- Cells: grade de thumbnails com lightbox ao clicar -->
      <div v-if="result?.files?.length" class="card mt-1">
        <div class="cells-grid">
          <div
            v-for="f in result.files"
            :key="f"
            class="cell-item"
            @click="openLightbox(f)"
            title="Clique para ampliar"
          >
            <img :src="f" class="cell-img" alt="" draggable="false" />
          </div>
        </div>
      </div>

      <!-- Arquivos PNG gerados -->
      <div class="card mt-1 files-panel">
        <div class="files-header" @click="visFilesOpen = !visFilesOpen">
          <span class="files-title">Arquivos gerados ({{ visFiles.length }})</span>
          <span class="files-toggle">{{ visFilesOpen ? '&#x25B2;' : '&#x25BC;' }}</span>
        </div>
        <ul v-if="visFilesOpen" class="vis-file-list">
          <li
            v-for="f in visFiles"
            :key="f.name"
            class="vis-file-item"
            :class="{ active: result?.file === '/output/' + f.name }"
            @click="loadVisFile(f.name)"
            @mouseenter="showVisTooltip(f, $event)"
            @mouseleave="hideVisTooltip"
          >
            <span class="file-item-name">{{ f.name }}</span>
            <button
              class="file-delete-btn"
              title="Excluir arquivo"
              @click.stop="confirmDeleteVisFile(f.name)"
            >&#x1F5D1;</button>
          </li>
        </ul>
      </div>
    </template>

    <!-- Mapa de glifos ELIS -->
    <GlyphPickerModal v-if="showPicker" v-model="sequence" @close="showPicker = false" />

    <!-- Lightbox para células individuais -->
    <Teleport to="body">
      <div v-if="lightboxSrc" class="lightbox-overlay" @click.self="closeLightbox">
        <div class="lightbox-box">
          <button class="lightbox-close" @click="closeLightbox">✕</button>
          <img :src="lightboxSrc" class="lightbox-img" alt="" />
          <a :href="lightboxSrc" download class="btn-sm lb-dl">⬇ Download</a>
        </div>
      </div>
    </Teleport>

    <!-- Tooltip de metadados de arquivo PNG -->
    <Teleport to="body">
      <div v-if="tooltipVis" class="file-tooltip" :style="tooltipVisStyle">
        <!-- Seção: arquivo -->
        <div class="tt-section-title">Arquivo</div>
        <div class="tt-row"><span class="tt-label">Nome</span><span class="tt-val">{{ tooltipVis.name }}</span></div>
        <div class="tt-row"><span class="tt-label">Tipo</span><span class="tt-val">{{ parseVisFileType(tooltipVis.name) }}</span></div>
        <div class="tt-row"><span class="tt-label">Tamanho</span><span class="tt-val">{{ formatVisSize(tooltipVis.size) }}</span></div>
        <div class="tt-row"><span class="tt-label">Modificado</span><span class="tt-val">{{ formatVisDate(tooltipVis.modified) }}</span></div>

        <!-- Seção: física da célula -->
        <template v-if="tooltipVis.physics">
          <div class="tt-divider"></div>
          <div class="tt-section-title">Física da Célula</div>
          <div class="tt-row"><span class="tt-label">Resolução</span><span class="tt-val">{{ tooltipVis.physics.resolution }}</span></div>
          <div class="tt-row"><span class="tt-label">Espaçamento</span><span class="tt-val">{{ tooltipVis.physics.spacing_mm.toFixed(1) }} mm</span></div>
          <div class="tt-row"><span class="tt-label">Célula W×H</span><span class="tt-val">{{ tooltipVis.physics.cell_w_mm.toFixed(1) }} × {{ tooltipVis.physics.cell_h_mm.toFixed(1) }} mm</span></div>
          <div class="tt-row"><span class="tt-label">Gap</span><span class="tt-val">{{ tooltipVis.physics.gap_mm.toFixed(1) }} mm</span></div>
          <div class="tt-row"><span class="tt-label">Aspecto</span><span class="tt-val">{{ tooltipVis.physics.aspect_ratio?.toFixed(2) }}×</span></div>
          <div class="tt-row"><span class="tt-label">Modo</span><span class="tt-val tt-mode" :data-mode="tooltipVis.physics.reading_mode">{{ tooltipVis.physics.reading_mode }}</span></div>
          <div class="tt-row"><span class="tt-label">Glifos/tira</span><span class="tt-val">{{ tooltipVis.physics.seq_capacity }}</span></div>

          <!-- Seção: ISO 11548-2 -->
          <div class="tt-divider"></div>
          <div class="tt-section-title">ISO 11548-2</div>
          <div v-for="c in tooltipVis.physics.iso" :key="c.label" class="tt-iso-row">
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
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useCandidatesStore } from '@/stores/candidates'
import GlyphPickerModal from '@/components/GlyphPickerModal.vue'

const candidates = useCandidatesStore()
const sequence = ref('tqlDà')
const showPicker = ref(false)
const visType = ref<'strip' | 'cells' | 'grid'>('strip')
const loading = ref(false)
const error = ref<string | null>(null)
const result = ref<{ file?: string; files?: string[] } | null>(null)

// ── Geração ───────────────────────────────────────────────────────────────
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
    // Reset do viewer para nova imagem
    scale.value = 1
    tx.value = 0
    ty.value = 0
    rotation.value = 0
    await nextTick()
    fitToView()
    fetchVisFiles()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

// ── Viewer: estado ────────────────────────────────────────────────────────
const viewportEl = ref<HTMLElement | null>(null)
const imgEl      = ref<HTMLImageElement | null>(null)
const scale      = ref(1)
const tx         = ref(0)   // translate X
const ty         = ref(0)   // translate Y
const rotation   = ref(0)   // graus (múltiplos de 90)
const isDragging = ref(false)
const isFullscreen = ref(false)
let dragStartX = 0
let dragStartY = 0
let dragOriginTx = 0
let dragOriginTy = 0

const ZOOM_MIN = 0.05
const ZOOM_MAX = 20
const ZOOM_STEP = 1.25

const zoomPct = computed(() => Math.round(scale.value * 100))

const imgStyle = computed(() => ({
  transform: `translate(${tx.value}px, ${ty.value}px) scale(${scale.value}) rotate(${rotation.value}deg)`,
  transformOrigin: '0 0',
  cursor: isDragging.value ? 'grabbing' : 'grab',
}))

// ── Viewer: zoom ──────────────────────────────────────────────────────────
function clampScale(s: number) {
  return Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, s))
}

/** Zoom centrado num ponto (px, py) relativo ao viewport */
function zoomAt(factor: number, px: number, py: number) {
  const next = clampScale(scale.value * factor)
  const ratio = next / scale.value
  tx.value = px - ratio * (px - tx.value)
  ty.value = py - ratio * (py - ty.value)
  scale.value = next
}

function zoomStep(dir: 1 | -1) {
  const vp = viewportEl.value
  if (!vp) return
  const cx = vp.clientWidth / 2
  const cy = vp.clientHeight / 2
  zoomAt(dir > 0 ? ZOOM_STEP : 1 / ZOOM_STEP, cx, cy)
}

function onWheel(e: WheelEvent) {
  const vp = viewportEl.value
  if (!vp) return
  const rect = vp.getBoundingClientRect()
  const px = e.clientX - rect.left
  const py = e.clientY - rect.top
  const factor = e.deltaY < 0 ? ZOOM_STEP : 1 / ZOOM_STEP
  zoomAt(factor, px, py)
}

function resetZoom() {
  scale.value = 1
  tx.value = 0
  ty.value = 0
}

function fitToView() {
  const vp  = viewportEl.value
  const img = imgEl.value
  if (!vp || !img) return
  const vpW = vp.clientWidth  - 32
  const vpH = vp.clientHeight - 32
  const natW = img.naturalWidth  || 1
  const natH = img.naturalHeight || 1
  const s = Math.min(vpW / natW, vpH / natH, 1)
  scale.value = s
  tx.value = (vp.clientWidth  - natW * s) / 2
  ty.value = (vp.clientHeight - natH * s) / 2
}

function rotate90() {
  rotation.value = (rotation.value + 90) % 360
}

// ── Viewer: pan ───────────────────────────────────────────────────────────
function startDrag(e: MouseEvent) {
  isDragging.value = true
  dragStartX = e.clientX
  dragStartY = e.clientY
  dragOriginTx = tx.value
  dragOriginTy = ty.value
}

function onDrag(e: MouseEvent) {
  if (!isDragging.value) return
  tx.value = dragOriginTx + (e.clientX - dragStartX)
  ty.value = dragOriginTy + (e.clientY - dragStartY)
}

function endDrag() {
  isDragging.value = false
}

// ── Tela cheia ────────────────────────────────────────────────────────────
function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
  nextTick(() => fitToView())
}

function onKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape' && isFullscreen.value) {
    isFullscreen.value = false
    nextTick(() => fitToView())
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeyDown)
  fetchVisFiles()
})
onUnmounted(() => window.removeEventListener('keydown', onKeyDown))

// ── Lightbox (cells) ─────────────────────────────────────────────────────
const lightboxSrc = ref<string | null>(null)

function openLightbox(src: string) {
  lightboxSrc.value = src
}
function closeLightbox() {
  lightboxSrc.value = null
}

// ── Arquivos PNG existentes ───────────────────────────────────────────────────
interface IsoCheck { label: string; ok: boolean; detail: string }
interface PhysicsData {
  resolution: string; spacing_mm: number
  cell_w_mm: number; cell_h_mm: number; gap_mm: number
  aspect_ratio: number | null; reading_mode: string; seq_capacity: number
  iso: IsoCheck[]
}
interface VisFileInfo { name: string; size: number; modified: string; physics?: PhysicsData }
const visFiles = ref<VisFileInfo[]>([])
const visFilesOpen = ref(false)

async function fetchVisFiles() {
  try {
    const r = await axios.get('/api/visualization/files')
    visFiles.value = r.data
  } catch { /* silencioso */ }
}

function loadVisFile(name: string) {
  result.value = { file: `/output/${name}` }
  scale.value = 1
  tx.value = 0
  ty.value = 0
  rotation.value = 0
  nextTick(() => fitToView())
}

async function confirmDeleteVisFile(name: string) {
  if (!confirm(`Excluir "${name}"?`)) return
  await axios.delete(`/api/visualization/files/${encodeURIComponent(name)}`)
  visFiles.value = visFiles.value.filter(f => f.name !== name)
  if (result.value?.file === `/output/${name}`) result.value = null
}

// ── Tooltip ────────────────────────────────────────────────────────────────
const tooltipVis = ref<VisFileInfo | null>(null)
const tooltipVisStyle = ref<Record<string, string>>({})

function showVisTooltip(f: VisFileInfo, e: MouseEvent) {
  tooltipVis.value = f
  tooltipVisStyle.value = { top: `${e.clientY + 14}px`, left: `${e.clientX + 14}px` }
}
function hideVisTooltip() { tooltipVis.value = null }

function parseVisFileType(name: string): string {
  if (name.includes('strip')) return 'Tira completa'
  if (name.includes('cell') || name.includes('_U')) return 'Células'
  if (name.includes('grid')) return 'Grade diagnóstica'
  return 'Preview'
}
function formatVisSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}
function formatVisDate(iso: string): string {
  return new Date(iso).toLocaleString('pt-BR')
}
</script>

<style scoped>
@font-face {
  font-family: 'ELIS';
  src: url('/static/elis.ttf') format('truetype');
  font-weight: normal;
  font-style: normal;
}

.view { max-width: 960px; }
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

/* ── Viewer ────────────────────────────────────────────────────────────── */
.viewer-card { padding: .75rem; }
.viewer-card.fullscreen {
  position: fixed;
  inset: 0;
  z-index: 9999;
  border-radius: 0;
  display: flex;
  flex-direction: column;
  padding: .5rem;
  overflow: hidden;
}

.viewer-toolbar {
  display: flex;
  gap: .5rem;
  align-items: center;
  flex-wrap: wrap;
  padding: .3rem .25rem .5rem;
  border-bottom: 1px solid var(--accent);
  margin-bottom: .5rem;
}
.toolbar-group {
  display: flex;
  align-items: center;
  gap: .2rem;
  padding-right: .6rem;
  border-right: 1px solid var(--accent);
}
.toolbar-group:last-child { border-right: none; }

.tool-btn {
  background: var(--accent);
  color: var(--text);
  border: none;
  border-radius: 4px;
  padding: .25rem .55rem;
  cursor: pointer;
  font-size: .9rem;
  line-height: 1;
  text-decoration: none;
  user-select: none;
  transition: background .15s;
}
.tool-btn:hover { background: #444; }
.tool-link { display: inline-flex; align-items: center; }

.zoom-label {
  font-size: .8rem;
  min-width: 3.5ch;
  text-align: center;
  color: var(--muted);
  cursor: pointer;
  padding: .2rem .3rem;
  border-radius: 3px;
}
.zoom-label:hover { background: var(--accent); color: var(--text); }

.viewer-viewport {
  position: relative;
  width: 100%;
  height: 520px;
  flex: 1 1 0;
  overflow: hidden;
  background: #111;
  border-radius: 6px;
  user-select: none;
}
.viewer-card.fullscreen .viewer-viewport {
  height: auto;
  border-radius: 0;
}
.viewer-viewport.grabbing { cursor: grabbing; }

.viewer-img {
  position: absolute;
  top: 0; left: 0;
  will-change: transform;
  max-width: none;
  image-rendering: pixelated;
}

.viewer-hint {
  margin: .4rem 0 0;
  flex-shrink: 0;
  font-size: .75rem;
  color: var(--muted);
  text-align: center;
}

/* ── Cells ─────────────────────────────────────────────────────────────── */
.cells-grid { display: flex; flex-wrap: wrap; gap: .5rem; }
.cell-item { cursor: zoom-in; border-radius: 4px; overflow: hidden; border: 1px solid var(--accent); transition: border-color .15s; }
.cell-item:hover { border-color: var(--primary); }
.cell-img { width: 120px; height: auto; display: block; }

/* ── Lightbox ──────────────────────────────────────────────────────────── */
.lightbox-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  background: rgba(0,0,0,.85);
  display: flex;
  align-items: center;
  justify-content: center;
}
.lightbox-box {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: .75rem;
  max-width: 90vw;
  max-height: 90vh;
}
.lightbox-close {
  position: absolute;
  top: -.5rem; right: -.5rem;
  background: var(--primary); color: #fff;
  border: none; border-radius: 50%;
  width: 2rem; height: 2rem;
  cursor: pointer; font-size: 1rem;
  display: flex; align-items: center; justify-content: center;
  z-index: 1;
}
.lightbox-img {
  max-width: 90vw;
  max-height: 80vh;
  border-radius: 6px;
  object-fit: contain;
}
.lb-dl { margin-top: .25rem; }

.btn-sm {
  background: var(--accent); color: var(--text);
  border: none; border-radius: 4px;
  padding: .2rem .6rem; cursor: pointer; text-decoration: none; font-size: .85rem;
}
.label-seq { display: flex; align-items: center; gap: .4rem; }
.btn-picker {
  background: var(--accent); color: var(--text);
  border: 1px solid var(--accent); border-radius: 4px;
  padding: .22rem .5rem; cursor: pointer; font-size: .9rem;
  line-height: 1; transition: border-color .15s;
}
.btn-picker:hover { border-color: var(--primary); color: var(--primary); }

/* ── Painel de arquivos gerados ─────────────────────────────────────────── */
.files-panel { padding: .65rem 1rem; }
.files-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
  padding: .1rem 0;
}
.files-title { font-size: .9rem; font-weight: 600; }
.files-toggle { font-size: .75rem; color: var(--muted); }

.vis-file-list { list-style: none; padding: 0; margin: .45rem 0 0; }
.vis-file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: .35rem .5rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: .82rem;
  cursor: pointer;
  color: var(--muted);
  gap: .5rem;
  transition: background .12s, color .12s;
}
.vis-file-item:hover { background: var(--accent); color: var(--text); }
.vis-file-item.active { background: var(--primary); color: #fff; }
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

/* ── Tooltip ─────────────────────────────────────────────────────────── */
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
.tt-mode[data-mode="1-dedo"]          { color: #4caf50; }
.tt-mode[data-mode="multi-dedo"]      { color: #ff9800; }
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
</style>
