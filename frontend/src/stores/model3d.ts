import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export interface Model3DFileInfo {
  name: string
  size: number
  modified: string
  format: string
}

export const useModel3DStore = defineStore('model3d', () => {
  const files = ref<Model3DFileInfo[]>([])
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

  async function deleteFile(name: string) {
    await axios.delete(`/api/model3d/files/${encodeURIComponent(name)}`)
    files.value = files.value.filter(f => f.name !== name)
    if (currentFile.value?.endsWith(name)) currentFile.value = null
  }

  return { files, currentFile, generating, error, fetchFiles, generate, deleteFile }
})
