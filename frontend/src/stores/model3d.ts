import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export const useModel3DStore = defineStore('model3d', () => {
  const files = ref<string[]>([])
  const currentFile = ref<string | null>(null)
  const generating = ref(false)
  const error = ref<string | null>(null)

  async function fetchFiles() {
    const r = await axios.get('/api/model3d/files')
    files.value = r.data
  }

  async function generate(candidate: object, sequence: string, fmt: '3mf' | 'stl' = '3mf', fullTest = false) {
    generating.value = true
    error.value = null
    try {
      const r = await axios.post('/api/model3d/generate', { candidate, sequence, fmt, full_test: fullTest })
      currentFile.value = r.data.file
      await fetchFiles()
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      generating.value = false
    }
  }

  return { files, currentFile, generating, error, fetchFiles, generate }
})
