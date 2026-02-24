import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export type TaskStatus = 'idle' | 'running' | 'done' | 'error'

export interface LogMessage {
  line: string
  pct: number
}

export interface AnalysisParams {
  pin_spacing_candidates: number[]
  density_min: number
  density_max: number
  edge_complexity_min: number
  iou_min: number
  max_finger_area_mm: number
  max_multi_finger_mm: number
  seq_glyph_min: number
  min_coverage_pct: number
}

export const useAnalysisStore = defineStore('analysis', () => {
  const status = ref<TaskStatus>('idle')
  const taskId = ref<string | null>(null)
  const error = ref<string | null>(null)
  const logs = ref<LogMessage[]>([])
  const progress = ref(0)
  const params = ref<AnalysisParams | null>(null)
  let ws: WebSocket | null = null

  async function fetchStatus() {
    const r = await axios.get('/api/analysis/status')
    status.value = r.data.status
    taskId.value = r.data.task_id
    error.value = r.data.error
  }

  async function fetchDefaults() {
    const r = await axios.get('/api/analysis/params/defaults')
    params.value = r.data
  }

  function connectWS() {
    if (ws) ws.close()
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    ws = new WebSocket(`${proto}//${location.host}/api/ws/progress`)
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data)
      if ('pct' in msg) {
        logs.value.push({ line: msg.line ?? '', pct: msg.pct })
        progress.value = msg.pct
      }
      if (msg.type === 'done') {
        status.value = 'done'
      }
      if (msg.type === 'error') {
        status.value = 'error'
        error.value = msg.line
      }
    }
    ws.onclose = () => { ws = null }
  }

  async function runAnalysis(customParams?: AnalysisParams) {
    logs.value = []
    progress.value = 0
    error.value = null
    connectWS()
    const body = customParams ?? params.value ?? undefined
    const r = await axios.post('/api/analysis/run', body ?? null)
    status.value = r.data.status
    taskId.value = r.data.task_id
  }

  return { status, taskId, error, logs, progress, params, fetchStatus, fetchDefaults, runAnalysis }
})
