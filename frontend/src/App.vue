<template>
  <div class="app">
    <header class="app-header">
      <span class="app-title">ELIS Glifo Analyser</span>
      <nav class="app-nav">
        <RouterLink to="/analysis">Análise</RouterLink>
        <RouterLink to="/candidates">Candidatos</RouterLink>
        <RouterLink to="/detail">Detalhamento</RouterLink>
        <RouterLink to="/visualization">Visualização</RouterLink>
        <RouterLink to="/model3d">Modelo 3D</RouterLink>
      </nav>
    </header>
    <main class="app-main">
      <RouterView />
    </main>
    <footer class="app-footer">
      <span>
        © 2025–2026
        <a href="https://github.com/maxwellamaral/glifo-analise" target="_blank" rel="noopener"
           title="Repositório do projeto">
          Maxwell Anderson Ielpo do Amaral
        </a>
        — ELIS Glifo Analyser
      </span>
      <span class="footer-license">
        Licença MIT · Uso livre com atribuição ao autor
      </span>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<style>
:root {
  --bg: #1a1a2e;
  --surface: #16213e;
  --accent: #0f3460;
  --primary: #e94560;
  --text: #eaeaea;
  --muted: #888;
}

body {
  background: var(--bg);
  color: var(--text);
  margin: 0;
  font-family: 'Segoe UI', system-ui, sans-serif;
}

.app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  background: var(--surface);
  padding: 0.75rem 1.5rem;
  display: flex;
  align-items: center;
  gap: 2rem;
  border-bottom: 1px solid var(--accent);
}

.app-title {
  font-weight: 700;
  font-size: 1.1rem;
  color: var(--primary);
  letter-spacing: 0.05em;
}

.app-nav {
  display: flex;
  gap: 1rem;
}

.app-nav a {
  color: var(--muted);
  text-decoration: none;
  padding: 0.3rem 0.7rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.app-nav a.router-link-active {
  color: var(--text);
  background: var(--accent);
}

.app-main {
  padding: 1.5rem;
  flex: 1;
}

.app-footer {
  background: var(--surface);
  border-top: 1px solid var(--accent);
  padding: .6rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: .5rem;
  font-size: .78rem;
  color: var(--muted);
}

.app-footer a {
  color: var(--primary);
  text-decoration: none;
}
.app-footer a:hover { text-decoration: underline; }

.footer-license {
  font-size: .73rem;
  opacity: .7;
}
</style>
