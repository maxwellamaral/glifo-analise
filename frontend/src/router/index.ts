import { createRouter, createWebHistory } from 'vue-router'
import AnalysisView from '@/views/AnalysisView.vue'
import CandidatesView from '@/views/CandidatesView.vue'
import DetailView from '@/views/DetailView.vue'
import VisualizationView from '@/views/VisualizationView.vue'
import Model3DView from '@/views/Model3DView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/analysis' },
    { path: '/analysis', component: AnalysisView, meta: { title: 'Análise' } },
    { path: '/candidates', component: CandidatesView, meta: { title: 'Candidatos' } },
    { path: '/detail', component: DetailView, meta: { title: 'Detalhamento' } },
    { path: '/visualization', component: VisualizationView, meta: { title: 'Visualização' } },
    { path: '/model3d', component: Model3DView, meta: { title: 'Modelo 3D' } },
  ],
})

export default router
