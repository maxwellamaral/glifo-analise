<template>
  <Teleport to="body">
    <div class="overlay" @click.self="$emit('close')" @keydown.escape="$emit('close')">
      <div class="modal" role="dialog" aria-modal="true" aria-label="Mapa de Glifos ELIS">

        <!-- Cabeçalho -->
        <div class="modal-header">
          <span class="modal-title">Mapa de Glifos ELIS</span>
          <button class="btn-close" title="Fechar (Esc)" @click="$emit('close')">✕</button>
        </div>

        <!-- Sequência atual + controles -->
        <div class="seq-bar">
          <span class="seq-label">Sequência:</span>
          <span class="seq-display">
            <span v-if="!localSeq" class="seq-empty">— vazia —</span>
            <span v-else class="seq-chars">{{ localSeq }}</span>
          </span>
          <button class="btn-ghost-sm" title="Apagar último glifo" @click="removeLast" :disabled="!localSeq">⌫</button>
          <button class="btn-ghost-sm btn-danger" title="Limpar sequência" @click="localSeq = ''" :disabled="!localSeq">✕</button>
          <button class="btn-confirm" @click="confirm">Confirmar</button>
        </div>

        <!-- Abas de grupo -->
        <div class="group-tabs">
          <button
            v-for="g in groups"
            :key="g"
            class="group-tab"
            :class="{ active: activeGroup === g }"
            @click="activeGroup = g"
          >{{ g }}</button>
        </div>

        <!-- Corpo: grid + preview -->
        <div class="modal-body">
          <!-- Grid de glifos -->
          <div class="glyph-grid" v-if="!loading">
            <button
              v-for="g in filteredGlyphs"
              :key="g.codepoint"
              class="glyph-cell"
              :title="`U+${g.codepoint.toString(16).toUpperCase().padStart(4,'0')} · ${g.group}`"
              @click="append(g.char)"
              @mouseenter="hovered = g"
              @mouseleave="hovered = null"
            >{{ g.char }}</button>
          </div>
          <div v-else class="loading-msg">Carregando glifos…</div>

          <!-- Painel de prévia (lado direito) -->
          <div class="preview-panel">
            <div class="preview-glyph">
              <span v-if="hovered" class="glyph-preview-char">{{ hovered.char }}</span>
              <span v-else class="preview-placeholder">↖ passe o mouse<br>sobre um glifo</span>
            </div>
            <div v-if="hovered" class="preview-info">
              <div class="preview-cp">U+{{ hovered.codepoint.toString(16).toUpperCase().padStart(4,'0') }}</div>
              <div class="preview-group">{{ hovered.group }}</div>
            </div>
          </div>
        </div>

        <!-- Rodapé -->
        <div class="modal-footer">
          <span class="footer-hint">Clique em um glifo para inserir na sequência</span>
          <span class="glyph-count">{{ filteredGlyphs.length }} glifos</span>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import axios from 'axios'

interface GlyphInfo {
  codepoint: number
  char: string
  group: string
}

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{
  (e: 'update:modelValue', val: string): void
  (e: 'close'): void
}>()

const localSeq = ref(props.modelValue)
const glyphs = ref<GlyphInfo[]>([])
const loading = ref(true)
const hovered = ref<GlyphInfo | null>(null)
const activeGroup = ref('Todos')

const groups = computed(() => {
  const seen = new Set<string>()
  glyphs.value.forEach(g => seen.add(g.group))
  return ['Todos', ...Array.from(seen)]
})

const filteredGlyphs = computed(() =>
  activeGroup.value === 'Todos'
    ? glyphs.value
    : glyphs.value.filter(g => g.group === activeGroup.value)
)

watch(() => props.modelValue, v => { localSeq.value = v })

onMounted(async () => {
  try {
    const r = await axios.get<GlyphInfo[]>('/api/analysis/glyphs')
    glyphs.value = r.data
  } finally {
    loading.value = false
  }

  // Permite fechar com Escape mesmo sem foco no modal
  window.addEventListener('keydown', onKey)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
})

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}

function append(ch: string) {
  localSeq.value += ch
  emit('update:modelValue', localSeq.value)
}

function removeLast() {
  // Glifos ELIS podem ser multi-byte (surrogates), usa spread para segurança
  const chars = [...localSeq.value]
  chars.pop()
  localSeq.value = chars.join('')
  emit('update:modelValue', localSeq.value)
}

function confirm() {
  emit('update:modelValue', localSeq.value)
  emit('close')
}
</script>

<style scoped>
@font-face {
  font-family: 'ELIS';
  src: url('/static/elis.ttf') format('truetype');
  font-weight: normal;
  font-style: normal;
}

/* ---------- Overlay ---------- */
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, .70);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

/* ---------- Modal ---------- */
.modal {
  background: var(--surface);
  border: 1px solid var(--accent);
  border-radius: 10px;
  width: min(780px, 96vw);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 8px 40px rgba(0,0,0,.6);
}

/* ---------- Cabeçalho ---------- */
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: .75rem 1rem;
  border-bottom: 1px solid var(--accent);
  background: var(--accent);
}
.modal-title {
  font-weight: 700;
  font-size: 1rem;
  color: var(--text);
}
.btn-close {
  background: transparent;
  border: none;
  color: var(--muted);
  font-size: 1rem;
  cursor: pointer;
  padding: .2rem .4rem;
  border-radius: 4px;
  line-height: 1;
}
.btn-close:hover { color: var(--primary); background: rgba(255,255,255,.08); }

/* ---------- Barra de sequência ---------- */
.seq-bar {
  display: flex;
  align-items: center;
  gap: .5rem;
  padding: .6rem 1rem;
  border-bottom: 1px solid var(--accent);
  flex-wrap: wrap;
}
.seq-label {
  font-size: .8rem;
  color: var(--muted);
  white-space: nowrap;
}
.seq-display {
  flex: 1;
  min-width: 10ch;
  background: var(--bg);
  border: 1px solid var(--accent);
  border-radius: 4px;
  padding: .25rem .6rem;
  font-family: 'ELIS', monospace;
  font-size: 1.3rem;
  letter-spacing: .05em;
  color: var(--text);
  min-height: 2rem;
  display: flex;
  align-items: center;
}
.seq-empty { color: var(--muted); font-family: sans-serif; font-size: .8rem; }
.seq-chars { font-family: 'ELIS', monospace; }

.btn-ghost-sm {
  background: transparent;
  border: 1px solid var(--accent);
  color: var(--muted);
  border-radius: 4px;
  padding: .2rem .5rem;
  cursor: pointer;
  font-size: .85rem;
  line-height: 1.2;
}
.btn-ghost-sm:hover { border-color: var(--primary); color: var(--primary); }
.btn-ghost-sm:disabled { opacity: .35; cursor: not-allowed; }
.btn-danger:hover { border-color: #f66; color: #f66; }

.btn-confirm {
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: .3rem .9rem;
  cursor: pointer;
  font-size: .85rem;
  margin-left: .25rem;
}
.btn-confirm:hover { opacity: .88; }

/* ---------- Abas de grupo ---------- */
.group-tabs {
  display: flex;
  gap: .25rem;
  padding: .5rem 1rem .4rem;
  border-bottom: 1px solid var(--accent);
  flex-wrap: wrap;
}
.group-tab {
  background: transparent;
  border: 1px solid var(--accent);
  color: var(--muted);
  border-radius: 4px;
  padding: .2rem .7rem;
  cursor: pointer;
  font-size: .8rem;
  transition: all .15s;
}
.group-tab:hover { border-color: var(--primary); color: var(--text); }
.group-tab.active {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
}

/* ---------- Corpo ---------- */
.modal-body {
  display: flex;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

/* Grid de glifos */
.glyph-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(42px, 1fr));
  gap: 2px;
  padding: .75rem;
  overflow-y: auto;
  align-content: start;
}

.glyph-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  background: var(--bg);
  border: 1px solid #2a2a4a;
  border-radius: 4px;
  font-family: 'ELIS', monospace;
  font-size: 1.4rem;
  color: var(--text);
  cursor: pointer;
  transition: background .1s, border-color .1s, transform .1s;
  padding: 0;
  line-height: 1;
}
.glyph-cell:hover {
  background: var(--accent);
  border-color: var(--primary);
  transform: scale(1.15);
  z-index: 1;
  position: relative;
  box-shadow: 0 2px 8px rgba(0,0,0,.4);
}
.glyph-cell:active {
  background: var(--primary);
  transform: scale(1.08);
}

.loading-msg {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--muted);
  font-size: .9rem;
}

/* Painel de prévia */
.preview-panel {
  width: 140px;
  min-width: 140px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-left: 1px solid var(--accent);
  padding: 1rem .5rem;
  gap: .75rem;
}

.preview-glyph {
  width: 110px;
  height: 110px;
  background: var(--bg);
  border: 1px solid var(--accent);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.glyph-preview-char {
  font-family: 'ELIS', monospace;
  font-size: 5rem;
  color: var(--text);
  line-height: 1;
}
.preview-placeholder {
  font-size: .7rem;
  color: var(--muted);
  text-align: center;
  line-height: 1.5;
}

.preview-info {
  text-align: center;
}
.preview-cp {
  font-family: monospace;
  font-size: .75rem;
  color: var(--primary);
}
.preview-group {
  font-size: .72rem;
  color: var(--muted);
  margin-top: .2rem;
}

/* ---------- Rodapé ---------- */
.modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: .45rem 1rem;
  border-top: 1px solid var(--accent);
  font-size: .75rem;
  color: var(--muted);
}
</style>
