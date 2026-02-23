import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export type TaskStatus = 'idle' | 'running' | 'done' | 'error'

export interface LogMessage {
  line: string
  pct: number
}

export const useAnalysisStore = defineStore('analysis', () => {
  const status = ref<TaskStatus>('idle')
  const taskId = ref<string | null>(null)
  const error = ref<string | null>(null)
  const logs = ref<LogMessage[]>([])
  const progress = ref(0)
  let ws: WebSocket | null = null

  async function fetchStatus() {
    const r = await axios.get('/api/analysis/status')
    status.value = r.data.status
    taskId.value = r.data.task_id
    error.value = r.data.error
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

  async function runAnalysis() {
    logs.value = []
    progress.value = 0
    error.value = null
    connectWS()
    const r = await axios.post('/api/analysis/run')
    status.value = r.data.status
    taskId.value = r.data.task_id
  }

  return { status, taskId, error, logs, progress, fetchStatus, runAnalysis }
})
