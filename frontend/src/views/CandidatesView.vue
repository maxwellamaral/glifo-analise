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

    <div v-else class="table-wrap mt-1">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Resolução</th>
            <th>Espaç.</th>
            <th>Cobert.</th>
            <th>Modo</th>
            <th>Sequências</th>
            <th>Ação</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="c in store.list"
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
        </tbody>
      </table>
    </div>

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
import { onMounted } from 'vue'
import { useCandidatesStore } from '@/stores/candidates'

const store = useCandidatesStore()
onMounted(() => store.fetch())
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

.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: .5rem .75rem; text-align: left; border-bottom: 1px solid var(--accent); font-size: .9rem; }
th { color: var(--muted); font-weight: 600; }
tr.selected td { background: rgba(233,69,96,.1); }
tr:hover td { background: rgba(255,255,255,.03); cursor: pointer; }

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
