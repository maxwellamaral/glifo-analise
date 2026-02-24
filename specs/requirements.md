# Requisitos — glifo-analise

## Contexto

Ferramenta de análise de viabilidade tátil para a fonte ELIS (Escrita das Línguas de
Sinais) destinada a dispositivos matriciais de pinos retráteis. Visa determinar quais
glifos são reproduzíveis respeitando limiares psicofísicos táteis (ISO 11548-2).

---

## Requisitos Funcionais

### RF-01 — Análise de resolução
- RF-01.1: Carregar font TTF (elis.ttf) e extrair todos os codepoints mapeados.
- RF-01.2: Para cada resolução M×N candidata e espaçamento de pinos configurável,
  renderizar bitmaps e aplicar critérios de aptidão tátil.
- RF-01.3: Produzir relatório de cobertura (nº de glifos aptos / total) por resolução.
- RF-01.4: Calcular dimensão física da célula (mm) e classificar modo de leitura
  (1-dedo / multi-dedo / fora-de-alcance).
- RF-01.5: Calcular capacidade sequencial (glifos/tira) dentro da envergadura da mão.

### RF-02 — Gerenciamento de candidatos
- RF-02.1: Filtrar e ranquear candidatos viáveis com base em cobertura, capacidade
  sequencial e espaçamento.
- RF-02.2: Identificar o melhor candidato sequencial e o melhor candidato econômico
  (menor área física com cobertura ≥ limiar configurável).
- RF-02.3: Persistir lista de candidatos em JSON para reutilização entre sessões.

### RF-03 — Verificação de conformidade ISO 11548-2
- RF-03.1: Avaliar cada candidato contra 9 critérios psicofísicos (espaçamento, gap,
  razão espaç/diâm, tamanho 1-dedo, tamanho multi-dedo, aspecto, seq. capacity,
  cobertura ≥ 95%, cobertura ≥ 100%).
- RF-03.2: Emitir veredicto APROVADO / ATENÇÃO por candidato.

### RF-04 — Geração de grade visual
- RF-04.1: Gerar imagem PNG da grade de glifos para uma resolução/espaçamento dados.

### RF-05 — Geração de modelo 3D
- RF-05.1: Gerar arquivo STL ou 3MF de tira tátil com glifos da sequência informada.
- RF-05.2: Gerar modelo de teste completo (todos os pinos levantados) na resolução
  declarada do hardware.
- RF-05.3: Junto a cada modelo 3D, gerar PNG de preview (vista superior) com painel
  de dados técnicos.

### RF-06 — Interface de linha de comando (CLI)
- RF-06.1: Executar análise completa sem interação (`uv run glifo-analise`).
- RF-06.2: Modo `--list`: exibir e selecionar candidatos da sessão anterior.
- RF-06.3: Apresentar tabela de candidatos, fichas detalhadas com relatório ISO e
  oferecer geração de modelos 3D ao final.

### RF-07 — Interface gráfica (GUI — Vue 3 + FastAPI)
- RF-07.1: Aba **Análise** — disparar análise completa; exibir log linha a linha via
  WebSocket com barra de progresso em tempo real.
- RF-07.2: Aba **Candidatos** — tabela interativa filtrável/ordenável; clicar em linha
  seleciona um candidato e exibe ficha ISO detalhada.
- RF-07.3: Aba **Visualização** — galeria inline de PNGs gerados (grade + preview tátil);
  botão para gerar nova imagem a partir de um candidato (tira completa, células individuais
  ou grade diagnóstica); clique para ampliar. Campo "Sequência" acompanhado de botão de
  acesso ao Mapa de Glifos ELIS (RF-07.8). Painel colapsável **"Arquivos gerados"** lista
  todos os PNGs existentes em `output/`; clicar em um arquivo carrega-o diretamente no
  visualizador; tooltip ao passar o mouse exibe nome, tipo (tira/células/grade),
  tamanho e data de modificação; botão de exclusão individual com confirmação.
  Endpoints: `GET /api/visualization/files` e `DELETE /api/visualization/files/{filename}`.
- RF-07.4: Aba **Modelo 3D** — escolha de candidato, sequência de glifos (fonte ELIS),
  formato (STL/3MF), checkbox "teste completo"; visualizador Three.js interativo embutido;
  download direto do arquivo gerado. Campo "Sequência" acompanhado de botão de acesso
  ao Mapa de Glifos ELIS (RF-07.8). Lista de arquivos gerados exibe metadados (formato,
  tamanho, data) em tooltip ao passar o mouse; botão de exclusão individual com
  confirmação. Endpoints: `GET /api/model3d/files` (retorna objetos com
  `name/size/modified/format`) e `DELETE /api/model3d/files/{filename}`.
- RF-07.5: GUI e CLI compartilham o mesmo núcleo de lógica — sem duplicação de código.
- RF-07.6: O backend FastAPI serve a SPA Vue (arquivos estáticos compilados em
  `frontend/dist/`) na rota `/`; rotas de API prefixadas em `/api/`.
- RF-07.7: Progresso de operações longas (análise, geração 3D) comunicado via WebSocket
  (`/api/ws/progress`), com fallback para polling REST se conexão não disponível.
- RF-07.8: **Mapa de Glifos ELIS** — modal estilo "Mapa de Caracteres" do Windows acessível
  a partir das abas Visualização e Modelo 3D. Exibe exclusivamente os glifos mapeados na
  fonte ELIS, organizados em abas por grupo (Todos / Maiúsculas / Minúsculas / Dígitos /
  Símbolos / Estendidos). Clicar em um glifo insere-o imediatamente no campo "Sequência".
  Painel de prévia lateral exibe o glifo em destaque com codepoint Unicode e grupo.
  Suporta remoção do último glifo (Unicode-safe), limpeza total e confirmação. Fechamento
  via tecla Escape ou clique na sobreposição.
- RF-07.9: **Parâmetros configuráveis de análise** — painel colapsável na aba Análise
  expõe os 9 parâmetros do núcleo Python (resoluções mín/máx de linhas e colunas,
  espaçamento mín/máx, diâmetro de pino, limiar de cobertura, envergadura da mão).
  Permite redefinir valores individualmente; botão "Restaurar padrões" retorna os valores
  ao `GET /api/analysis/params/defaults`. Resumo dos valores ativos exibido quando o
  painel está recolhido.

### RF-08 — Autoria, citação e licença
- RF-08.1: O repositório deve incluir arquivo `LICENSE` com licença MIT e cláusula de
  atribuição obrigatória ao autor original.
- RF-08.2: O repositório deve incluir `CITATION.bib` com entradas BibLaTeX (`@software`)
  e ABNT (`@misc`) para citação acadêmica.
- RF-08.3: O repositório deve incluir `CITATION.cff` (Citation File Format v1.2) para
  detecção automática de citação pelo GitHub.
- RF-08.4: O `README.md` deve conter seções "Autoria e Citação" e "Licença" com
  exemplos de uso nos formatos APA, ABNT e BibLaTeX.
- RF-08.5: A GUI deve exibir rodapé permanente com nome do autor, link e aviso de
  copyright/licença.

---

## Requisitos Não Funcionais

| ID | Categoria | Descrição |
|----|-----------|-----------|
| RNF-01 | Desempenho | Análise completa (todos os candidatos × espaçamentos) deve concluir em < 60 s em hardware moderno. |
| RNF-02 | Desempenho | Cache de resolução efetiva (`_EFF_RES_CACHE`) mantido entre chamadas na mesma sessão. |
| RNF-03 | Usabilidade | GUI deve abrir automaticamente no browser padrão em `http://localhost:8080`. O frontend Vue é servido pelo backend FastAPI. |
| RNF-04 | Usabilidade | CLI deve continuar funcionando de forma idêntica à versão anterior (100% backwards-compatible). |
| RNF-05 | Manutenibilidade | Nenhuma lógica de análise dentro de arquivos GUI ou CLI — apenas chamadas ao núcleo. |
| RNF-06 | Manutenibilidade | Cobertura de testes ≥ 80% no núcleo (`analysis/`, `output/`, `models.py`, `config.py`). |
| RNF-07 | Portabilidade | Suporte a Linux, macOS e WSL2 (Windows via WSL). |
| RNF-08 | Padrões | Python 3.10+ com type hints; docstrings Google Style; `uv` como gerenciador de pacotes. |
| RNF-09 | Segurança | GUI sem autenticação (uso local); não expor em redes públicas. |
| RNF-10 | Licença | Código licenciado sob MIT com cláusula de atribuição; arquivos de citação acadêmica (`CITATION.bib`, `CITATION.cff`) incluídos no repositório. |
| RNF-11 | Usabilidade | Mapa de Glifos ELIS (RF-07.8) deve exibir todos os glifos na fonte ELIS renderizados com `font-family: 'ELIS'`; interação por clique simples sem necessidade de arrastar ou confirmar para inserção imediata. |
| RNF-12 | Usabilidade | Parâmetros de análise (RF-07.9) devem ter valores padrão carregados do backend; qualquer alteração persiste apenas na sessão corrente (sem escrita em disco). |
| RNF-13 | Portabilidade | O sistema deve poder ser executado em container Docker sem necessidade de instalar Python, Node.js ou `uv` no host. A imagem é multi-stage (Node → Python/uv → final), priorizando cache de camadas (`uv sync --no-install-project` antes de copiar o código-fonte). Arquivos gerados são persistidos via volume `./output/`. |
| RNF-08 | Padrões | Python 3.10+ com type hints; docstrings Google Style; `uv` como gerenciador de pacotes. |
| RNF-09 | Segurança | GUI sem autenticação (uso local); não expor em redes públicas. |
