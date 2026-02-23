<template>
  <div class="view">
    <div class="view-header">
      <h2>Candidatos Viáveis</h2>
      <button class="btn-primary" @click="store.fetch()">Atualizar</button>
    </div>

    <div v-if="store.loading" class="muted mt-1">Carregando...</div>

    <div v-else-if="!store.list.length" class="card muted mt-1">
      Nenhum candidato encontrado. Execute a análise primeiro.
    </div>

    <template v-else>
      <!-- Barra de filtro -->
      <div class="filter-bar mt-1">
        <span class="filter-icon">⌕</span>
        <input
          v-model="filterText"
          class="filter-input"
          placeholder="Filtrar candidatos... (ex: 13×13, 1-dedo, 100%)"
          type="search"
        />
        <span v-if="filterText" class="filter-count muted">
          {{ filtered.length }} de {{ store.list.length }}
        </span>
      </div>

      <div class="table-wrap mt-1">
        <table>
          <thead>
            <tr>
              <th @click="setSort('rank')" class="sortable">
                # <span :class="sortIconClass('rank')">{{ sortIcon('rank') }}</span>
              </th>
              <th @click="setSort('resolution')" class="sortable">
                Resolução <span :class="sortIconClass('resolution')">{{ sortIcon('resolution') }}</span>
              </th>
              <th @click="setSort('spacing_mm')" class="sortable">
                Espaç. <span :class="sortIconClass('spacing_mm')">{{ sortIcon('spacing_mm') }}</span>
              </th>
              <th @click="setSort('coverage_pct')" class="sortable">
                Cobert. <span :class="sortIconClass('coverage_pct')">{{ sortIcon('coverage_pct') }}</span>
              </th>
              <th @click="setSort('reading_mode')" class="sortable">
                Modo <span :class="sortIconClass('reading_mode')">{{ sortIcon('reading_mode') }}</span>
              </th>
              <th @click="setSort('seq_capacity')" class="sortable">
                Sequências <span :class="sortIconClass('seq_capacity')">{{ sortIcon('seq_capacity') }}</span>
              </th>
              <th>Ação</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="c in filtered"
              :key="c.rank"
              :class="{ selected: store.selected?.rank === c.rank }"
              @click="store.select(c)"
            >
              <td>{{ c.rank }}</td>
              <td>{{ c.resolution[0] }}×{{ c.resolution[1] }}</td>
              <td>{{ c.spacing_mm }} mm</td>
              <td>{{ c.coverage_pct.toFixed(1) }}%</td>
              <td>{{ c.reading_mode }}</td>
              <td>{{ c.seq_capacity }}</td>
              <td><button class="btn-sm" @click.stop="store.select(c)">Selecionar</button></td>
            </tr>
            <tr v-if="!filtered.length">
              <td colspan="7" class="muted" style="text-align:center; padding: 1rem;">
                Nenhum resultado para "{{ filterText }}"
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- Detalhe ISO do selecionado -->
    <div v-if="store.selected" class="card mt-1 detail">
      <h3>Candidato #{{ store.selected.rank }} — Grade {{ store.selected.resolution[0] }}×{{ store.selected.resolution[1] }} @ {{ store.selected.spacing_mm }}mm</h3>
      <p>Célula: {{ store.selected.cell_w_mm?.toFixed(1) }}×{{ store.selected.cell_h_mm?.toFixed(1) }} mm</p>
      <div v-if="store.selected.iso_criteria?.length">
        <strong>Critérios ISO</strong>
        <ul class="iso-list">
          <li v-for="c in store.selected.iso_criteria" :key="c.criterion">
            <span :class="c.passed ? 'ok' : 'fail'">{{ c.passed ? '✔' : '✘' }}</span>
            <strong>{{ c.criterion }}:</strong> {{ c.detail }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useCandidatesStore } from '@/stores/candidates'
import type { Candidate } from '@/stores/candidates'

const store = useCandidatesStore()
onMounted(() => store.fetch())

// ── Filtro ────────────────────────────────────────────────────────────────
const filterText = ref('')

// ── Ordenação ─────────────────────────────────────────────────────────────
type SortCol = 'rank' | 'resolution' | 'spacing_mm' | 'coverage_pct' | 'reading_mode' | 'seq_capacity'
type SortDir = 'asc' | 'desc'

const sortCol = ref<SortCol>('rank')
const sortDir = ref<SortDir>('asc')

function setSort(col: SortCol) {
  if (sortCol.value === col) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortCol.value = col
    sortDir.value = 'asc'
  }
}

// Valor de ordenação por coluna
function sortValue(c: Candidate, col: SortCol): number | string {
  switch (col) {
    case 'rank':         return c.rank
    case 'resolution':   return c.resolution[0] * 1000 + c.resolution[1]
    case 'spacing_mm':   return c.spacing_mm
    case 'coverage_pct': return c.coverage_pct
    case 'reading_mode': return c.reading_mode
    case 'seq_capacity': return c.seq_capacity
  }
}

// ── Lista filtrada + ordenada ─────────────────────────────────────────────
const filtered = computed<Candidate[]>(() => {
  const q = filterText.value.trim().toLowerCase()

  let result = store.list.filter(c => {
    if (!q) return true
    const searchable = [
      String(c.rank),
      `${c.resolution[0]}×${c.resolution[1]}`,
      `${c.resolution[0]}x${c.resolution[1]}`,
      `${c.spacing_mm}`,
      `${c.spacing_mm} mm`,
      `${c.coverage_pct.toFixed(1)}%`,
      c.reading_mode,
      String(c.seq_capacity),
    ].join(' ').toLowerCase()
    return searchable.includes(q)
  })

  const col = sortCol.value
  const dir = sortDir.value
  result = [...result].sort((a, b) => {
    const va = sortValue(a, col)
    const vb = sortValue(b, col)
    if (va < vb) return dir === 'asc' ? -1 : 1
    if (va > vb) return dir === 'asc' ? 1 : -1
    return 0
  })

  return result
})

// ── Indicadores de ordenação (funções utilitárias) ───────────────────────
function sortIcon(col: SortCol): string {
  if (sortCol.value !== col) return '⇅'
  return sortDir.value === 'asc' ? '↑' : '↓'
}

function sortIconClass(col: SortCol): string {
  return sortCol.value === col ? 'sort-icon active' : 'sort-icon inactive'
}
</script>

<style scoped>
.view { max-width: 960px; }
.view-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: .5rem; }
h2 { margin: 0; }
.mt-1 { margin-top: 1rem; }
.muted { color: var(--muted); font-size: .9rem; }

.btn-primary {
  background: var(--primary); color: #fff;
  border: none; border-radius: 6px;
  padding: .4rem .9rem; cursor: pointer;
}

/* Barra de filtro */
.filter-bar {
  display: flex;
  align-items: center;
  gap: .5rem;
  background: var(--surface);
  border: 1px solid var(--accent);
  border-radius: 8px;
  padding: .4rem .75rem;
}
.filter-icon { font-size: 1.2rem; color: var(--muted); user-select: none; }
.filter-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text);
  font-size: .9rem;
}
.filter-input::placeholder { color: var(--muted); }
.filter-input::-webkit-search-cancel-button { cursor: pointer; }
.filter-count { font-size: .8rem; white-space: nowrap; }

/* Tabela */
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: .5rem .75rem; text-align: left; border-bottom: 1px solid var(--accent); font-size: .9rem; }
th { color: var(--muted); font-weight: 600; }
th.sortable { cursor: pointer; user-select: none; white-space: nowrap; }
th.sortable:hover { color: var(--text); }
tr.selected td { background: rgba(233,69,96,.1); }
tr:hover td { background: rgba(255,255,255,.03); cursor: pointer; }

/* Indicador de ordenação */
.sort-icon { margin-left: .3rem; font-size: .75rem; }
.sort-icon.inactive { opacity: .3; }
.sort-icon.active { color: var(--primary); opacity: 1; }

.btn-sm { background: var(--accent); color: var(--text); border: none; border-radius: 4px; padding: .2rem .6rem; cursor: pointer; font-size: .8rem; }

.card {
  background: var(--surface);
  border: 1px solid var(--accent);
  border-radius: 8px;
  padding: 1rem;
}

.detail h3 { margin: 0 0 .5rem; }

.iso-list { list-style: none; padding: 0; margin: .5rem 0 0; }
.iso-list li { display: flex; gap: .5rem; align-items: baseline; padding: .2rem 0; font-size: .85rem; }
.ok   { color: #6f6; font-size: 1rem; }
.fail { color: #f66; font-size: 1rem; }
</style>
