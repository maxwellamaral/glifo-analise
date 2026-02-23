import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export interface IsoCheck {
  criterion: string
  passed: boolean
  detail: string
}

export interface Candidate {
  rank: number
  resolution: [number, number]
  spacing_mm: number
  coverage_pct: number
  reading_mode: string
  seq_capacity: number
  cell_w_mm: number
  cell_h_mm: number
  iso_criteria: IsoCheck[]
}

export const useCandidatesStore = defineStore('candidates', () => {
  const list = ref<Candidate[]>([])
  const selected = ref<Candidate | null>(null)
  const loading = ref(false)

  async function fetch() {
    loading.value = true
    try {
      const r = await axios.get('/api/candidates')
      list.value = r.data
    } finally {
      loading.value = false
    }
  }

  function select(c: Candidate) {
    selected.value = c
  }

  return { list, selected, loading, fetch, select }
})
