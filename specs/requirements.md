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

### RF-07 — Interface gráfica (GUI — NiceGUI)
- RF-07.1: Painel **Configurações** — editar todos os parâmetros psicofísicos,
  grupos de glifos ELiS e parâmetros de análise por sessão (sem alterar código-fonte).
- RF-07.2: Painel **Análise** — disparar análise completa com log em streaming
  linha a linha; mostrar barra de progresso.
- RF-07.3: Painel **Candidatos** — tabela interativa filtrável/ordenável; clicar em
  linha seleciona candidato.
- RF-07.4: Painel **Visualização** — galeria inline de PNGs gerados (grade e preview
  3D); clique para ampliar.
- RF-07.5: Painel **Modelo 3D** — escolha de candidato, sequência de glifos, formato
  (STL/3MF), geração de teste completo e download direto no browser.
- RF-07.6: GUI e CLI compartilham o mesmo núcleo de lógica — sem duplicação de código.

---

## Requisitos Não Funcionais

| ID | Categoria | Descrição |
|----|-----------|-----------|
| RNF-01 | Desempenho | Análise completa (todos os candidatos × espaçamentos) deve concluir em < 60 s em hardware moderno. |
| RNF-02 | Desempenho | Cache de resolução efetiva (`_EFF_RES_CACHE`) mantido entre chamadas na mesma sessão. |
| RNF-03 | Usabilidade | GUI deve abrir automaticamente no browser padrão em `http://localhost:8080`. |
| RNF-04 | Usabilidade | CLI deve continuar funcionando de forma idêntica à versão anterior (100% backwards-compatible). |
| RNF-05 | Manutenibilidade | Nenhuma lógica de análise dentro de arquivos GUI ou CLI — apenas chamadas ao núcleo. |
| RNF-06 | Manutenibilidade | Cobertura de testes ≥ 80% no núcleo (`analysis/`, `output/`, `models.py`, `config.py`). |
| RNF-07 | Portabilidade | Suporte a Linux, macOS e WSL2 (Windows via WSL). |
| RNF-08 | Padrões | Python 3.10+ com type hints; docstrings Google Style; `uv` como gerenciador de pacotes. |
| RNF-09 | Segurança | GUI sem autenticação (uso local); não expor em redes públicas. |
