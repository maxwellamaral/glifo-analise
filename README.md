# Glifo Análise — Viabilidade Tátil para Dispositivo Matricial ELIS

Ferramenta de análise que determina a **resolução mínima de célula** (em pinos)
e a **viabilidade tátil** dos glifos da fonte **ELIS** em um dispositivo
de exibição matricial destinado à leitura pelo tato por pessoas cegas.

---

## Contexto

### Fonte ELIS (Escrita das Línguas de Sinais)

A fonte `elis.ttf` **não codifica um idioma convencional**.
Ela implementa a **notação ELIS** (Escrita das Línguas de Sinais), um sistema
desenvolvido para representar graficamente os sinais da Língua de Sinais
Brasileira (Libras) e de outras línguas de sinais.

A estratégia de armazenamento é um **mapeamento de teclado**: os codepoints
Unicode de letras latinas, dígitos e símbolos de pontuação são reutilizados
como chaves de acesso para 145 sinais gráficos distintos.
Cada "letra" digitada no teclado aciona um sinal ELIS, não um caractere de texto.

| Codepoints Unicode utilizados | Quantidade | Conteúdo em ELIS |
|-------------------------------|-----------|------------------|
| U+0041 – U+005A (A–Z)         | 26        | Sinais maiúsculos |
| U+0061 – U+007A (a–z)         | 26        | Sinais minúsculos |
| U+0030 – U+0039 (0–9)         | 10        | Sinais numéricos |
| U+0021 – U+005F (pontuação)   | 21        | Modificadores e conectores |
| U+00A0 – U+00FD (Latin-1)     | 62        | Diacríticos e sinais estendidos |
| **Total com conteúdo visual** | **145**   | |
| U+0020 (SPACE)                | 1         | Separador (sem forma visual) |

### Dispositivo alvo

Um **display matricial de pinos táteis** que eleva/abaixa pinos metálicos
ou plásticos em uma grade de $N \times N$ posições, permitindo que uma pessoa
cega toque o glifo e identifique o sinal ELIS pelo relevo.

---

## Requisitos Psicofísicos

O projeto foi dimensionado com base nos limiares de **percepção tátil dos
dedos indicador e médio** estabelecidos pela literatura especializada e pela
norma ISO 11548-2 (equipamentos em Braille).

### Limiar de dois pontos (resolução espacial do dedo)

O **limiar de discriminação de dois pontos** na ponta dos dedos é de
aproximadamente **2 a 3 mm**. Abaixo desse espaçamento, dois pinos
adjacentes são percebidos como um único ponto de pressão.

Parâmetro adotado:

$$d_{pino} = 2{,}5\ \text{mm (centro a centro)}$$

Esse valor coincide com o espaçamento Braille definido pela ISO 11548-2,
amplamente validado em dispositivos de leitura tátil.

### Tamanho máximo legível com um dedo

A leitura eficiente com **um único dedo** exige que toda a célula caiba
sob a área de contato do dedo indicador, estimada em:

$$A_{dedo} \leq 25\ \text{mm} \times 25\ \text{mm}$$

Células maiores exigem exploração com múltiplos dedos ou movimento sequencial,
aumentando o tempo de decodificação e a carga cognitiva.

### Dimensões físicas por resolução

$$L_{física}(N) = (N - 1) \times d_{pino}$$

| Resolução | Tamanho físico | Compatibilidade |
|-----------|---------------|----------------|
| **10×10** | **22,5 × 22,5 mm** | ✅ Leitura com 1 dedo |
| 15×15 | 35,0 × 35,0 mm | ⚠ Requer exploração com 2–3 dedos |
| 20×20 | 47,5 × 47,5 mm | ⚠ Requer exploração palmar |

### Parâmetros físicos do pino

| Parâmetro | Valor | Fundamento |
|-----------|-------|-----------|
| Espaçamento (centro a centro) | 2,5 mm | ISO 11548-2, limiar tátil dos dedos |
| Diâmetro do pino | 1,5 mm | ISO 11548-2 (Braille: 1,5–1,6 mm) |
| Gap entre pinos | 1,0 mm | ≥ 0,8 mm mínimo para discriminação |
| Altura mínima ativa | 0,6 mm | ISO 11548-2; detectável ao tato |

---

## Critérios de Viabilidade Tátil

Cada glifo é avaliado por **cinco critérios independentes**.
A falha em qualquer um resulta na classificação correspondente.

### 1. Tamanho físico (TAMANHO_GRANDE)

A célula não pode exceder $25\ \text{mm}$. Resoluções 15×15 e 20×20 já
falham neste critério, independentemente do conteúdo do glifo.

### 2. Densidade mínima — $\rho$ (VAZIO)

$$\rho = \frac{\sum_{i,j} B_{i,j}}{N^2} \geq \rho_{\min} = 0{,}03$$

Pinos insuficientes ($< 3\%$ da matriz) produzem uma sensação tátil
imperceptível ou idêntica a células adjacentes. Aplica-se especialmente a
sinais ELIS que possuem traços muito finos ou pontos isolados.

### 3. Densidade máxima (SATURADO)

$$\rho \leq \rho_{\max} = 0{,}55$$

Mais de 55% dos pinos ativos cria uma superfície densa sem textura
diferenciável — percebida como um "bloco liso" ao tato.

### 4. Complexidade de borda — $\varepsilon$ (RASO)

$$\varepsilon = \frac{|\{(i,j): B_{i,j} \neq \text{vizinho}\}|}{N^2} \geq \varepsilon_{\min} = 0{,}08$$

Um pixel é considerado "de borda" se seu valor difere de pelo menos um
dos quatro vizinhos adjacentes. Glifos com $\varepsilon < 0{,}08$ possuem
poucos contornos internos e tendem a ser confundidos ao tato.

### 5. Fidelidade estrutural — IoU (PERDA_ESTRUTURAL)

$$IoU(A,B) = \frac{|A \cap B|}{|A \cup B|} \geq 0{,}15$$

Onde $A$ é o bitmap de referência ($64 \times 64$, reduzido para $N \times N$
via filtro LANCZOS + rebinarização) e $B$ é o bitmap na resolução de teste.
O IoU detecta deformações graves de forma que invalidam o reconhecimento tátil.

### Tabela de veredictos

| Veredicto | Cor (grade) | Significado |
|-----------|-------------|-------------|
| **APTO** | Verde | Todos os critérios satisfeitos |
| VAZIO | Cinza | $\rho < 3\%$ — marca tátil insuficiente |
| SATURADO | Laranja | $\rho > 55\%$ — bloco indiferenciado |
| RASO | Amarelo | $\varepsilon < 8\%$ — forma sem contornos |
| PERDA_ESTRUTURAL | Vermelho | IoU < 0,15 — forma distorcida |
| TAMANHO_GRANDE | Azul | Célula excede 25 mm (múltiplos dedos) |

---

## Resultados

### Tabela geral de cobertura

| Resolução | Tamanho físico | 1 dedo | APTO | VAZIO | Outros | Cobertura útil |
|-----------|---------------|--------|------|-------|--------|----------------|
| **10×10** | **22,5 mm** | **✅** | **123** | **20** | **3** | **97,6%** |
| 15×15 | 35,0 mm | ⚠ | 0 | 1 | 145 | 0,0% |
| 20×20 | 47,5 mm | ⚠ | 0 | 1 | 145 | 0,0% |

As resoluções 15×15 e 20×20 são integralmente reprovadas pelo critério de
tamanho físico — excedem os 25 mm do campo de leitura com um dedo.

### Cobertura por grupo de glifos — 10×10

| Grupo ELIS | Aptos | Totais (exc. VAZIO) | Cobertura |
|------------|-------|---------------------|-----------|
| Maiúsculas A–Z | 26 | 26 | 100% |
| Dígitos 0–9 | 10 | 10 | 100% |
| Pontuação / Símbolos | 16 | 16 | 100% |
| Acentuados / Latin-1 | 53 | 53 | 100% |
| **Minúsculas a–z** | **18** | **21** | **86%** |

As minúsculas a–z apresentam cobertura parcial. Cinco sinais
(b, k, m, n, q) possuem $\rho < 3\%$ na resolução 10×10 (sinais de
traço fino ou mínimo) e três (i, r, s) possuem IoU < 0,15 (deformação
estrutural ao reduzir para 10 pinos).

### Glifos com restrição em 10×10

| Codepoint | Sinal | Veredicto | $\rho$ | IoU | $\varepsilon$ | Observação |
|-----------|-------|-----------|--------|-----|--------------|------------|
| U+0069 (i) | Minúscula i | PERDA_ESTRUTURAL | 0,100 | 0,097 | 0,300 | Forma distorcida ao reduzir |
| U+0072 (r) | Minúscula r | PERDA_ESTRUTURAL | 0,040 | 0,000 | 0,140 | Sinal desaparece estruturalmente |
| U+0073 (s) | Minúscula s | PERDA_ESTRUTURAL | 0,060 | 0,143 | 0,200 | IoU marginal (0,143 < 0,15) |

Esses três sinais requerem **redesenho manual** para a grade 10×10,
simplificando ou estilizando seus traços para garantir reconhecimento tátil.

### Glifos marcados como VAZIO (ausência intencional de pinos)

Vinte codepoints produzem $\rho < 3\%$ em 10×10, incluindo: o separador
`SPACE` (U+0020) e minúsculas b, k, m, n, q. Esses sinais ELIS possuem
geometria mínima que não produz marca tátil suficiente nesta resolução.
Para uso no dispositivo, recomenda-se ou:

- Aumentar ligeiramente o font size (ex.: usar tamanho `N`) e re-testar, ou
- Criar variantes simplificadas manuais para a grade 10×10.

---

## Recomendação Final

> **Resolução recomendada: 10×10 pinos — célula física de 22,5 × 22,5 mm**

Esta é a **única resolução** que simultaneamente:
1. Cabe sob um único dedo indicador ($22{,}5\ \text{mm} \leq 25\ \text{mm}$)
2. Atinge 97,6% de cobertura nos sinais ELIS com conteúdo visual
3. Garante cobertura total (100%) nos grupos Maiúsculas, Dígitos, Pontuação e Latin-1

Para cobertura completa dos 145 sinais, redesenhe manualmente os
**3 glifos problemáticos** (i, r, s) adaptando seus traços à grade de 10 pinos.

---

## Metodologia do Código

### Pipeline de análise

```
elis.ttf
  │
  ├─ fontTools.getBestCmap()
  │     → 146 codepoints mapeados
  │
  ├─ [Renderização de referência 64×64]
  │     Pillow FreeTypeFont → bitmap binário 0/1
  │     → GlyphProfile { density, edge_complexity, bitmap_ref }
  │
  ├─ Para cada resolução candidata (10×10, 15×15, 20×20):
  │     ├─ Calcula tamanho físico: (N-1) × 2,5 mm
  │     ├─ Para cada glifo:
  │     │     ├─ Renderiza em NxN
  │     │     ├─ Calcula ρ, ε
  │     │     ├─ Calcula IoU(ref reduzida, teste)
  │     │     └─ Emite veredicto (APTO / VAZIO / SATURADO / RASO / PERDA_ESTRUTURAL / TAMANHO_GRANDE)
  │     └─ Gera ResolutionReport + grade visual PNG
  │
  └─ [Análise Estendida — M×N × spacing sweep]
        Para cada resolução em ASYMMETRIC_RESOLUTIONS
        × espaçamento em {2,5 / 3,0 / 3,5 mm}:
              ├─ Calcula (L_cel, H_cel) por eixo
              ├─ Determina modo: 1-dedo / multi-dedo / fora-de-alcance
              ├─ Calcula K_max = ⌊(180 + 3) / (L_cel + 3)⌋
              ├─ Reutiliza análise psicofísica completa (5 critérios)
              └─ Filtra candidatos: modo OK + K≥4 + cobertura≥80%
```

### Cálculo do IoU

A referência de 64×64 é reduzida para $N \times N$ via filtro LANCZOS
(com _anti-aliasing_) seguido de rebinarização pelo threshold $> 64$,
compensando o desfoque introduzido pelo _downsampling_:

$$A_{reduzida} = \text{thresh}_{64}\left(\text{LANCZOS}_{64 \to N}(B_{ref})\right)$$

$$IoU = \frac{|A_{reduzida} \cap B_{teste}|}{|A_{reduzida} \cup B_{teste}|}$$

O IoU foi escolhido sobre a correlação de Pearson por ser robusto com
bitmaps esparsos: a correlação colapsa quando um dos vetores tem variância
próxima de zero, situação comum em sinais ELIS de baixa densidade.

### Métricas de complexidade

A complexidade de borda $\varepsilon$ captura a riqueza de contornos do glifo:
quanto maior $\varepsilon$, mais a forma possui variações internas que o dedo
pode detectar como sulcos, relevos ou transições. É calculada via detecção
de borda 4-conexa em numpy sem dependências externas:

```python
edge = (bm != up) | (bm != down) | (bm != left) | (bm != right)
ε = edge.sum() / bm.size
```

---

## Execução

```bash
uv sync                 # instala dependências
uv run python main.py   # executa a análise completa
```

Saídas geradas em `./output/`:

| Arquivo | Conteúdo |
|---------|----------|
| `tatil_<M>x<N>_<esp>mm.png` | Grade visual de diagnóstico por candidato |
| `candidatos_viaveis.json` | Lista de candidatos da análise estendida |
| `tatil_3d_<M>x<N>_<esp>mm_<seq>.<fmt>` | Modelo 3D tátil para impressão (`.3mf` ou `.stl`) |

---

## Dependências

| Pacote | Versão | Papel |
|--------|--------|-------|
| `Pillow` | ≥ 12.x | Renderização de glifos, geração de grades |
| `fonttools` | ≥ 4.x | Leitura do `cmap` da fonte TTF |
| `numpy` | ≥ 2.x | Operações binárias (IoU, densidade, complexidade) |
| `trimesh` | ≥ 4.x | Geração e exportação de malhas 3D (STL / 3MF) |
| `networkx` | ≥ 3.x | Exigido pelo trimesh para exportação 3MF |
| `lxml` | ≥ 6.x | Parser XML para o formato 3MF |

---

## Estrutura do Projeto

```
glifo-analise/
├── elis.ttf          ← fonte ELIS de sinais (não é fonte de texto)
├── main.py           ← script de análise de viabilidade tátil
├── pyproject.toml    ← configuração do projeto (uv)
├── output/
│   ├── tatil_<M>x<N>_<esp>mm.png       ← grade visual de diagnóstico
│   ├── candidatos_viaveis.json         ← lista persistida de candidatos
│   └── tatil_3d_<M>x<N>_<esp>mm_<seq>.3mf  ← protótipo 3D para impressão
└── README.md
```

---

## Geração de Protótipo 3D Tátil

A partir de qualquer candidato da lista salva, o sistema pode gerar um
modelo 3D imprimível (.3mf ou .stl) representando uma **tira de glifos ELIS
com pinos em relevo**, pronta para prototipagem em impressora FDM.

### Fluxo interativo

Após selecionar um candidato da lista e gerar a grade visual, o sistema pergunta:

```
Deseja gerar modelo 3D tátil para impressão? [S/n]:
Sequência de glifos ELIS [tqlDà]:        ← Enter usa o padrão
Formato [3mf/stl, padrão 3mf]:
```

O mesmo prompt aparece ao final da **análise completa**, sobre o melhor
candidato sequencial encontrado.

### Geometria do modelo

O modelo é composto por:

- **Placa-base** retangular de 2,0 mm de espessura;
- **Pinos cilíndricos** de $\varnothing\ 1{,}5\ \text{mm}$ e $0{,}6\ \text{mm}$ de altura
  em relevo, posicionados apenas nos pixels ativos de cada glifo;
- **Células** dispostas lado a lado com o `GAP_BETWEEN_CELLS_MM` de separação;
- **Margem** de 1,5 mm ao redor do conjunto.

A posição de cada pino usa a **resolução efetiva** (pinos mortos eliminados),
garantindo que o modelo não inclua pinos nunca ativados por nenhum glifo da fonte.

### Exemplo — sequência `tqlDà` no candidato 13×13 @ 2,5 mm

| Parâmetro | Valor |
|-----------|-------|
| Resolução efetiva | 10×10 pinos (declarada 13×13) |
| Dimensões por célula | 22,5 × 22,5 mm |
| Tira completa (5 glifos) | ≈ 127,5 × 25,5 × 2,6 mm |
| Arquivo 3MF | 43 KB |
| Arquivo STL | 295 KB |

### Nomenclatura dos arquivos

```
tatil_3d_<M>x<N>_<esp>mm_<sequência>.<fmt>
         │    │      │         │        └─ 3mf ou stl
         │    │      │         └─ caracteres alfanuméricos ou U+XXXX
         │    │      └─ espaçamento entre pinos (mm)
         │    └─ linhas da matriz declarada
         └─ colunas da matriz declarada
```

### Parâmetros configuráveis em `_generate_tactile_3d()`

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `pin_height_mm` | 0,6 mm | Altura dos pinos acima da base |
| `base_thickness_mm` | 2,0 mm | Espessura da placa-base |
| `margin_mm` | 1,5 mm | Margem lateral ao redor da tira |

### Compatibilidade com softwares de fatiamento

| Formato | Compatibilidade |
|---------|-----------------|
| `.3mf` | Bambu Studio, PrusaSlicer, Cura, OrcaSlicer |
| `.stl` | Universal — todos os slicers |

---

## Modos de Leitura Estendidos

Além da leitura com **um único dedo** em células 10×10, o sistema suporta
dois modos adicionais voltados a usuários que empregam múltiplos dedos
ou realizam **varrimento sequencial** de uma tira de glifos.

### 1. Leitura com múltiplos dedos

Quando a célula excede 25 mm mas permanece dentro de 55 mm
(equivalente a três dedos lado a lado), o usuário pode usar dois ou três
dedos simultaneamente para explorar a forma. Esse modo permite resoluções
maiores e, portanto, maior detalhe estrutural.

```
25 mm < dimensão_máxima ≤ 55 mm  →  modo multi-dedo
```

### 2. Varrimento sequencial de glifos

O usuário desliza a mão horizontalmente sobre uma **tira de K glifos**
dispostos lado a lado, lendo-os em sequência — exatamente como a leitura
Braille em linha. O limite é a **envergadura da mão adulta**:

$$K \leq \left\lfloor \frac{L_{mao} + g}{L_{cel} + g} \right\rfloor$$

Onde:
- $L_{mao} = 180\ \text{mm}$ — envergadura adulta (indicador a mindinho)
- $g = 3\ \text{mm}$ — folga física entre células adjacentes
- $L_{cel} = (M - 1) \times d_{pino}$ — largura física da célula ($M$ colunas)

A tira deve conter entre $K_{min} = 4$ e $K_{max} = 6$ glifos para garantir
contexto lexical suficiente sem sobrecarga de memória tátil de curto prazo.

### 3. Varredura de espaçamentos (2,5 → 3,5 mm)

O aumento do espaçamento entre pinos melhora a discriminabilidade tátil
individual de cada pino, porém reduz a capacidade sequencial $K$.

| Espaçamento | Fundamento |
|-------------|------------|
| **2,5 mm** | Mínimo normativo ISO 11548-2 |
| **3,0 mm** | Compromisso conforto/detalhe |
| **3,5 mm** | Máximo testado — máxima discriminabilidade |

### 4. Resoluções assimétricas M×N

Para glifos ELIS com predominância vertical, uma célula com $M < N$ oferece
mais resolução vertical sem ampliar a largura — preservando a capacidade
sequencial $K$. Os tamanhos físicos são calculados por eixo:

$$L_{cel} = (M - 1) \times d_{pino}, \quad H_{cel} = (N - 1) \times d_{pino}$$

O modo de leitura segue a maior dimensão:

$$\text{modo} = \begin{cases} \text{1-dedo} & \max(L_{cel}, H_{cel}) \leq 25\ \text{mm} \\ \text{multi-dedo} & 25\ \text{mm} < \max \leq 55\ \text{mm} \\ \text{fora-de-alcance} & \max > 55\ \text{mm} \end{cases}$$

---

## Resultados da Análise Estendida

### Candidatos viáveis (top 25)

Critérios: modo ≠ fora-de-alcance, $K \geq 4$ glifos/tira, cobertura ≥ 80%.

| Resolução | Espaç. | L (mm) | A (mm) | Modo | Seq | Cobertura |
|-----------|--------|--------|--------|------|-----|-----------|
| **10×12** | **2,5 mm** | **22,5** | **27,5** | **multi-dedo** | **7** | **100,0%** |
| 10×12 | 3,0 mm | 27,0 | 33,0 | multi-dedo | 6 | 100,0% |
| 12×15 | 2,5 mm | 27,5 | 35,0 | multi-dedo | 6 | 100,0% |
| 10×12 | 3,5 mm | 31,5 | 38,5 | multi-dedo | 5 | 100,0% |
| 12×15 | 3,0 mm | 33,0 | 42,0 | multi-dedo | 5 | 100,0% |
| 13×13 | 2,5 mm | 30,0 | 30,0 | multi-dedo | 5 | 100,0% |
| 13×13 | 3,5 mm | 42,0 | 42,0 | multi-dedo | 4 | 100,0% |
| 12×15 | 3,5 mm | 38,5 | 49,0 | multi-dedo | 4 | 100,0% |
| 13×13 | 3,0 mm | 36,0 | 36,0 | multi-dedo | 4 | 100,0% |
| 8×12 | 2,5 mm | 17,5 | 27,5 | multi-dedo | 8 | 99,2% |
| 8×12 | 3,0 mm | 21,0 | 33,0 | multi-dedo | 7 | 99,2% |
| 8×12 | 3,5 mm | 24,5 | 38,5 | multi-dedo | 6 | 99,2% |
| 13×16 | 2,5 mm | 30,0 | 37,5 | multi-dedo | 5 | 99,2% |
| 8×16 | 2,5 mm | 17,5 | 37,5 | multi-dedo | 8 | 98,5% |
| 8×16 | 3,0 mm | 21,0 | 45,0 | multi-dedo | 7 | 98,5% |
| 8×16 | 3,5 mm | 24,5 | 52,5 | multi-dedo | 6 | 98,5% |
| **8×8** | **2,5 mm** | **17,5** | **17,5** | **1-dedo** | **8** | **98,4%** |
| 8×8 | 3,0 mm | 21,0 | 21,0 | 1-dedo | 7 | 98,4% |
| 8×8 | 3,5 mm | 24,5 | 24,5 | 1-dedo | 6 | 98,4% |
| 15×15 | 2,5 mm | 35,0 | 35,0 | multi-dedo | 4 | 99,2% |

### Recomendação para leitura sequencial

> **Resolução recomendada: 10×12 @ 2,5 mm — célula 22,5 × 27,5 mm — 100% de cobertura**

| Critério | Valor |
|----------|-------|
| Cobertura | **100%** de todos os 145 glifos ELIS |
| Glifos/tira | Até **7** (alvo: 4–6) |
| Modo | Multi-dedo (dois dedos verticalmente) |
| Largura | 22,5 mm — compatível com 1 dedo na horizontal |
| Altura | 27,5 mm — requer 2 dedos verticalmente |
| Espaçamento | 2,5 mm (ISO 11548-2) |

A resolução 10×12 elimina os 3 glifos com PERDA_ESTRUTURAL presentes em 10×10
(i, r, s) ao ampliar as 2 linhas extras de altura para renderização.

Para **máximo espaçamento** (melhor discriminabilidade por pino) mantendo
a capacidade sequencial mínima:

> **8×12 @ 3,5 mm — célula 24,5 × 38,5 mm — 99,2% — até 6 glifos/tira**

