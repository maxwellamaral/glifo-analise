<template>
  <div class="view">

    <!-- Nenhum candidato selecionado -->
    <div v-if="!store.selected" class="no-selection">
      <div class="no-sel-icon">🔬</div>
      <h2>Nenhum candidato selecionado</h2>
      <p class="muted">
        Acesse a aba <strong>Candidatos</strong>, selecione uma entrada
        e volte aqui para ver o detalhamento técnico completo.
      </p>
      <router-link to="/candidates" class="btn-primary">Ir para Candidatos</router-link>
    </div>

    <template v-else>

      <!-- ── Cabeçalho ──────────────────────────────────────────────── -->
      <div class="view-header">
        <div class="title-row">
          <h2>
            Detalhamento — Candidato #{{ store.selected.rank }}
            <span class="chip" :class="modeClass">{{ store.selected.reading_mode }}</span>
            <span class="chip chip-cov" :class="coverageTierClass">{{ coverageTierLabel }}</span>
          </h2>
          <div class="header-actions">
            <router-link to="/candidates" class="btn-ghost">← Candidatos</router-link>
            <router-link to="/visualization" class="btn-ghost">Visualização →</router-link>
            <router-link to="/model3d" class="btn-ghost">Modelo 3D →</router-link>
          </div>
        </div>
        <p class="subtitle muted">
          Grade
          <strong>{{ store.selected.resolution[0] }}×{{ store.selected.resolution[1] }}</strong>
          @ <strong>{{ store.selected.spacing_mm }} mm/pino</strong> —
          {{ store.selected.cell_w_mm?.toFixed(1) }} × {{ store.selected.cell_h_mm?.toFixed(1) }} mm —
          {{ store.selected.coverage_pct?.toFixed(1) }}% cobertura
        </p>
      </div>

      <!-- Carregando detalhes -->
      <div v-if="loading" class="card mt-1 muted">Carregando detalhes…</div>
      <div v-else-if="error" class="card mt-1 error">{{ error }}</div>

      <template v-else-if="detail">

        <!-- ── Score global ─────────────────────────────────────────── -->
        <div class="score-bar mt-1">
          <div class="score-item" :class="detail.iso_all_pass ? 'pass' : 'warn'">
            <span class="score-val">{{ detail.iso_pass_count }}/{{ detail.iso_total_count }}</span>
            <span class="score-lbl">Critérios ISO</span>
          </div>
          <div class="score-item" :class="coverageTierClass">
            <span class="score-val">{{ detail.coverage_pct?.toFixed(1) }}%</span>
            <span class="score-lbl">Cobertura</span>
          </div>
          <div class="score-item" :class="seqOkClass">
            <span class="score-val">{{ detail.seq_capacity_computed }}</span>
            <span class="score-lbl">Glifos/tira</span>
          </div>
          <div class="score-item info">
            <span class="score-val">#{{ detail.area_rank_in_tier }}/{{ detail.total_in_tier }}</span>
            <span class="score-lbl">Rank econômico ({{ detail.coverage_tier }})</span>
          </div>
          <div class="score-item info">
            <span class="score-val">{{ detail.cell_area_mm2?.toFixed(0) }} mm²</span>
            <span class="score-lbl">Área da célula</span>
          </div>
        </div>

        <!-- ── Layout de duas colunas ───────────────────────────────── -->
        <div class="two-col mt-1">

          <!-- Coluna esquerda -->
          <div class="col-left">

            <!-- Dimensões Físicas -->
            <section class="card section">
              <h3>📐 Dimensões Físicas</h3>
              <table class="info-table">
                <tbody>
                  <tr><th>Resolução declarada</th><td>{{ detail.resolution[0] }}×{{ detail.resolution[1] }} pinos</td></tr>
                  <tr><th>Espaçamento (pitch)</th><td>{{ detail.spacing_mm }} mm</td></tr>
                  <tr><th>Diâmetro do pino ∅</th><td>1,5 mm (ISO 11548-2)</td></tr>
                  <tr><th>Gap entre pinos</th><td :class="detail.gap_mm >= 1.0 ? 'ok' : 'fail'">{{ detail.gap_mm }} mm</td></tr>
                  <tr><th>Razão espaç/diâm</th><td :class="detail.spacing_diameter_ratio >= 1.5 ? 'ok' : 'fail'">{{ detail.spacing_diameter_ratio }}×</td></tr>
                  <tr><th>Largura da célula (W)</th><td>{{ detail.cell_w_mm?.toFixed(1) }} mm</td></tr>
                  <tr><th>Altura da célula (H)</th><td>{{ detail.cell_h_mm?.toFixed(1) }} mm</td></tr>
                  <tr><th>Relação de aspecto W/H</th><td :class="detail.aspect_ratio <= 2.5 ? 'ok' : 'fail'">{{ detail.aspect_ratio?.toFixed(2) }}×</td></tr>
                  <tr><th>Área da célula</th><td>{{ detail.cell_area_mm2?.toFixed(1) }} mm²</td></tr>
                  <tr><th>Pinos totais (declarados)</th><td>{{ detail.total_pins_declared }}</td></tr>
                </tbody>
              </table>
            </section>

            <!-- Análise de Leitura Sequencial -->
            <section class="card section mt-1">
              <h3>🤲 Leitura Sequencial</h3>
              <table class="info-table">
                <tbody>
                  <tr><th>Modo de leitura</th>
                    <td><span class="chip-inline" :class="modeClass">{{ detail.reading_mode }}</span></td>
                  </tr>
                  <tr><th>Envergadura da mão</th><td>180 mm</td></tr>
                  <tr><th>Gap entre células (tira)</th><td>3,0 mm</td></tr>
                  <tr><th>Glifos/tira (K máx)</th>
                    <td :class="detail.seq_capacity_computed >= 4 ? 'ok' : 'fail'">
                      {{ detail.seq_capacity_computed }} glifos
                    </td>
                  </tr>
                  <tr><th>Faixa recomendada</th><td class="muted">4–6 glifos</td></tr>
                </tbody>
              </table>

              <div class="strip-widths mt-1">
                <div class="sw-title muted">Largura física da tira (mm)</div>
                <div class="sw-row">
                  <div
                    v-for="(w, n) in detail.strip_widths_mm"
                    :key="n"
                    class="sw-cell"
                    :class="{ 'sw-ok': parseInt(n) <= detail.seq_capacity_computed }"
                  >
                    <span class="sw-n">{{ n }} glifos</span>
                    <span class="sw-w">{{ w }} mm</span>
                  </div>
                </div>
              </div>
            </section>

          </div><!-- /col-left -->

          <!-- Coluna direita -->
          <div class="col-right">

            <!-- Conformidade ISO 11548-2 -->
            <section class="card section">
              <h3>📋 Conformidade ISO 11548-2 / Psicofísica</h3>

              <template v-for="cat in isoCategories" :key="cat">
                <div class="iso-category">{{ cat }}</div>
                <ul class="iso-list">
                  <li
                    v-for="c in detail.iso_criteria.filter((x: any) => x.category === cat)"
                    :key="c.criterion"
                    :class="c.passed ? 'pass-row' : 'fail-row'"
                  >
                    <span class="iso-icon">{{ c.passed ? '✔' : '✘' }}</span>
                    <div class="iso-text">
                      <strong>{{ c.criterion }}</strong>
                      <span class="iso-detail muted">{{ c.detail }}</span>
                    </div>
                  </li>
                </ul>
              </template>

              <div class="iso-summary" :class="detail.iso_all_pass ? 'iso-pass' : 'iso-warn'">
                {{ detail.iso_all_pass
                  ? `✔ Todos os ${detail.iso_total_count} critérios aprovados`
                  : `⚠ ${detail.iso_total_count - detail.iso_pass_count} critério(s) não satisfeito(s)` }}
              </div>
            </section>

            <!-- Análise Econômica -->
            <section class="card section mt-1">
              <h3>💡 Análise Econômica & Comparativa</h3>
              <p class="muted small">
                Ranking por menor área de célula dentro do mesmo tier de cobertura
                — menor área = menor número de pinos e menor custo de fabricação.
              </p>
              <table class="info-table">
                <tbody>
                  <tr><th>Tier de cobertura</th>
                    <td><span class="chip-inline" :class="coverageTierClass">{{ coverageTierLabel }} ({{ detail.coverage_pct?.toFixed(1) }}%)</span></td>
                  </tr>
                  <tr><th>Rank econômico no tier</th>
                    <td>
                      <span :class="detail.area_rank_in_tier === 1 ? 'ok' : ''">
                        {{ detail.area_rank_in_tier }}º de {{ detail.total_in_tier }}
                        {{ detail.area_rank_in_tier === 1 ? '⭐ menor área' : '' }}
                      </span>
                    </td>
                  </tr>
                  <tr><th>Área da célula</th><td>{{ detail.cell_area_mm2?.toFixed(1) }} mm²</td></tr>
                  <tr><th>Pinos por célula</th><td>{{ detail.total_pins_declared }}</td></tr>
                </tbody>
              </table>

              <div class="econ-note mt-1">
                <div
                  v-if="detail.area_rank_in_tier === 1"
                  class="note-box note-best"
                >
                  ⭐ Este é o candidato de <strong>menor área e menor custo</strong>
                  com {{ detail.coverage_tier === 'total' ? '100%' : detail.coverage_pct.toFixed(1)+'%' }}
                  de cobertura. Ideal para o primeiro protótipo.
                </div>
                <div v-else class="note-box note-info">
                  Há {{ detail.area_rank_in_tier - 1 }} candidato(s) com
                  mesma cobertura e área menor — verifique se a resolução
                  menor ainda atende à percepção tátil necessária.
                </div>
              </div>
            </section>

          </div><!-- /col-right -->
        </div><!-- /two-col -->

        <!-- ── Notas de Fabricação ──────────────────────────────────── -->
        <section class="card section mt-1">
          <h3>🔧 Notas de Fabricação para Dispositivo Tátil Dinâmico</h3>
          <ul class="fab-notes">
            <li v-for="(note, i) in detail.fabrication_notes" :key="i">{{ note }}</li>
          </ul>
          <div class="ref-params mt-1">
            <div class="rp-title muted">Parâmetros de referência do pino (ISO 11548-2)</div>
            <div class="rp-grid">
              <div class="rp-item"><span class="rp-val">0,6 mm</span><span class="rp-lbl">Altura mínima ativa</span></div>
              <div class="rp-item"><span class="rp-val">1,5 mm</span><span class="rp-lbl">Diâmetro (∅)</span></div>
              <div class="rp-item"><span class="rp-val">{{ detail.spacing_mm }} mm</span><span class="rp-lbl">Pitch selecionado</span></div>
              <div class="rp-item"><span class="rp-val">{{ detail.gap_mm }} mm</span><span class="rp-lbl">Gap entre pinos</span></div>
              <div class="rp-item"><span class="rp-val">2,0 mm</span><span class="rp-lbl">Espessura da base</span></div>
              <div class="rp-item"><span class="rp-val">{{ detail.total_pins_declared }}</span><span class="rp-lbl">Pinos / célula</span></div>
            </div>
          </div>
        </section>

      </template><!-- /detail -->

    </template><!-- /selected -->

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useCandidatesStore } from '@/stores/candidates'

const store = useCandidatesStore()
const router = useRouter()

interface IsoCheck  { criterion: string; category: string; passed: boolean; detail: string }
interface Detail    {
  rank: number
  resolution: [number, number]
  spacing_mm: number
  cell_w_mm: number
  cell_h_mm: number
  reading_mode: string
  seq_capacity: number
  seq_capacity_computed: number
  coverage_pct: number
  gap_mm: number
  spacing_diameter_ratio: number
  aspect_ratio: number
  cell_area_mm2: number
  total_pins_declared: number
  strip_widths_mm: Record<string, number>
  coverage_tier: 'total' | 'alta' | 'boa'
  area_rank_in_tier: number
  total_in_tier: number
  iso_criteria: IsoCheck[]
  iso_pass_count: number
  iso_total_count: number
  iso_all_pass: boolean
  fabrication_notes: string[]
}

const detail  = ref<Detail | null>(null)
const loading = ref(false)
const error   = ref<string | null>(null)

async function fetchDetail(rank: number) {
  loading.value = true
  error.value = null
  detail.value = null
  try {
    const r = await axios.get<Detail>(`/api/candidates/detail/${rank}`)
    detail.value = r.data
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Erro ao carregar detalhes.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (!store.list.length) store.fetch()
  if (store.selected) fetchDetail(store.selected.rank)
})

watch(() => store.selected, (c) => {
  if (c) fetchDetail(c.rank)
})

// ── Classes dinâmicas ──────────────────────────────────────────────────────
const modeClass = computed(() => {
  if (!store.selected) return ''
  return store.selected.reading_mode === '1-dedo' ? 'chip-green'
       : store.selected.reading_mode === 'multi-dedo' ? 'chip-yellow'
       : 'chip-red'
})

const coverageTierClass = computed(() => {
  const pct = (detail.value ?? store.selected)?.coverage_pct ?? 0
  return pct >= 100 ? 'chip-green' : pct >= 95 ? 'chip-yellow' : 'chip-orange'
})

const coverageTierLabel = computed(() => {
  const t = detail.value?.coverage_tier
  return t === 'total' ? '100% cobertura'
       : t === 'alta'  ? '≥ 95% cobertura'
       : '≥ 80% cobertura'
})

const seqOkClass = computed(() => {
  const k = detail.value?.seq_capacity_computed ?? 0
  return k >= 4 ? 'chip-green' : 'chip-red'
})

const isoCategories = computed(() => {
  if (!detail.value) return []
  return [...new Set(detail.value.iso_criteria.map(c => c.category))]
})
</script>

<style scoped>
.no-selection {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  min-height: 60vh;
  text-align: center;
}
.no-sel-icon { font-size: 3rem; }

/* ── Cabeçalho ─────────────────────────────────────────────────────────── */
.title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}
.header-actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.subtitle { margin: 0.25rem 0 0; font-size: 0.9rem; }

/* ── Score bar ──────────────────────────────────────────────────────────── */
.score-bar {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}
.score-item {
  flex: 1 1 120px;
  background: var(--surface);
  border: 1px solid var(--accent);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.2rem;
}
.score-item.pass  { border-color: #4caf50; }
.score-item.warn  { border-color: #ff9800; }
.score-item.info  { border-color: var(--accent); }
.score-item.chip-green { border-color: #4caf50; }
.score-item.chip-yellow{ border-color: #ffc107; }
.score-item.chip-red   { border-color: #f44336; }
.score-item.chip-orange{ border-color: #ff9800; }
.score-val { font-size: 1.4rem; font-weight: 700; color: var(--text); }
.score-lbl { font-size: 0.72rem; color: var(--muted); text-align: center; }

/* ── Chips ──────────────────────────────────────────────────────────────── */
.chip, .chip-inline {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-left: 0.4rem;
  vertical-align: middle;
}
.chip-green  { background: rgba(76,175,80,.22);  color: #81c784; border: 1px solid #4caf50; }
.chip-yellow { background: rgba(255,193,7,.18);  color: #ffd54f; border: 1px solid #ffc107; }
.chip-orange { background: rgba(255,152,0,.18);  color: #ffb74d; border: 1px solid #ff9800; }
.chip-red    { background: rgba(244,67,54,.18);  color: #e57373; border: 1px solid #f44336; }
.chip-cov    { margin-left: 0.2rem; }

/* ── Dois colunas ───────────────────────────────────────────────────────── */
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}
@media (max-width: 900px) {
  .two-col { grid-template-columns: 1fr; }
}
.col-left, .col-right { display: flex; flex-direction: column; }

/* ── Seções / cards ─────────────────────────────────────────────────────── */
.section h3 {
  margin: 0 0 0.75rem;
  font-size: 0.95rem;
  letter-spacing: 0.03em;
  color: var(--text);
}

/* ── Tabela de info ─────────────────────────────────────────────────────── */
.info-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}
.info-table th {
  text-align: left;
  padding: 0.3rem 0.5rem 0.3rem 0;
  color: var(--muted);
  font-weight: 400;
  width: 55%;
}
.info-table td {
  padding: 0.3rem 0;
  font-weight: 600;
}
.ok   { color: #81c784; }
.fail { color: #e57373; }

/* ── ISO list ───────────────────────────────────────────────────────────── */
.iso-category {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--muted);
  padding: 0.55rem 0 0.2rem;
  border-top: 1px solid var(--accent);
  margin-top: 0.4rem;
}
.iso-category:first-child { border-top: none; margin-top: 0; }
.iso-list { list-style: none; margin: 0; padding: 0; }
.iso-list li {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.3rem 0.4rem;
  border-radius: 4px;
  margin-bottom: 0.15rem;
}
.pass-row { background: rgba(76,175,80,.07); }
.fail-row { background: rgba(244,67,54,.10); }
.iso-icon { font-size: 0.9rem; margin-top: 0.05rem; flex-shrink: 0; }
.pass-row .iso-icon { color: #81c784; }
.fail-row .iso-icon { color: #e57373; }
.iso-text { display: flex; flex-direction: column; gap: 0.1rem; font-size: 0.82rem; }
.iso-detail { font-size: 0.75rem; }
.iso-summary {
  margin-top: 0.75rem;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.85rem;
}
.iso-pass { background: rgba(76,175,80,.15); color: #81c784; }
.iso-warn { background: rgba(255,152,0,.15); color: #ffb74d; }

/* ── Strip widths ───────────────────────────────────────────────────────── */
.strip-widths { }
.sw-title { font-size: 0.75rem; margin-bottom: 0.4rem; }
.sw-row { display: flex; gap: 0.4rem; flex-wrap: wrap; }
.sw-cell {
  background: var(--accent);
  border-radius: 6px;
  padding: 0.3rem 0.5rem;
  text-align: center;
  font-size: 0.75rem;
  opacity: 0.5;
  min-width: 64px;
}
.sw-cell.sw-ok { opacity: 1; border: 1px solid #4caf50; }
.sw-n { display: block; color: var(--muted); }
.sw-w { display: block; font-weight: 700; color: var(--text); }

/* ── Economic notes ─────────────────────────────────────────────────────── */
.note-box {
  padding: 0.65rem 0.85rem;
  border-radius: 6px;
  font-size: 0.83rem;
  line-height: 1.5;
}
.note-best { background: rgba(76,175,80,.15); color: #a5d6a7; border: 1px solid #4caf5055; }
.note-info { background: rgba(13,83,174,.2); color: #90caf9; border: 1px solid #1565c055; }

/* ── Notas de fabricação ────────────────────────────────────────────────── */
.fab-notes {
  margin: 0;
  padding: 0 0 0 1.2rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.fab-notes li { font-size: 0.85rem; line-height: 1.5; }

.ref-params { }
.rp-title { font-size: 0.75rem; margin-bottom: 0.5rem; }
.rp-grid { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.rp-item {
  background: var(--accent);
  border-radius: 6px;
  padding: 0.4rem 0.65rem;
  min-width: 90px;
  text-align: center;
}
.rp-val { display: block; font-weight: 700; font-size: 1rem; color: var(--text); }
.rp-lbl { display: block; font-size: 0.68rem; color: var(--muted); margin-top: 0.1rem; }

/* ── Botões ─────────────────────────────────────────────────────────────── */
.btn-ghost {
  color: var(--muted);
  text-decoration: none;
  padding: 0.3rem 0.7rem;
  border-radius: 4px;
  border: 1px solid var(--accent);
  font-size: 0.85rem;
  transition: all 0.2s;
}
.btn-ghost:hover { color: var(--text); border-color: var(--primary); }

.small { font-size: 0.8rem; }
.error { color: #e57373; }
</style>
