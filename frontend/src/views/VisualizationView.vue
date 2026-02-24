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
    </template>

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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useCandidatesStore } from '@/stores/candidates'

const candidates = useCandidatesStore()
const sequence = ref('tqlDà')
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

onMounted(() => window.addEventListener('keydown', onKeyDown))
onUnmounted(() => window.removeEventListener('keydown', onKeyDown))

// ── Lightbox (cells) ─────────────────────────────────────────────────────
const lightboxSrc = ref<string | null>(null)

function openLightbox(src: string) {
  lightboxSrc.value = src
}
function closeLightbox() {
  lightboxSrc.value = null
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
</style>
