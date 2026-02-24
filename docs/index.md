# Glifo Análise

**Ferramenta de análise de viabilidade tátil para dispositivos matriciais de pinos — fonte ELIS**

---

## O que é?

O **Glifo Análise** determina a **resolução mínima de célula** (em pinos) e a
**viabilidade tátil** dos glifos da fonte **ELIS** em um dispositivo matricial
destinado à leitura pelo tato por pessoas cegas.

A análise é realizada contra os critérios psicofísicos da norma **ISO 11548-2**,
garantindo que cada candidato de resolução seja reproduzível com conforto e
precisão pela ponta dos dedos.

---

## Fonte ELIS

A fonte `elis.ttf` implementa a **notação ELIS** (Escrita das Línguas de Sinais),
um sistema desenvolvido para representar graficamente os sinais da **Língua de
Sinais Brasileira (Libras)** e de outras línguas de sinais.

| Faixa Unicode | Quantidade | Conteúdo |
|---|---|---|
| U+0041–U+005A (A–Z) | 26 | Sinais maiúsculos |
| U+0061–U+007A (a–z) | 26 | Sinais minúsculos |
| U+0030–U+0039 (0–9) | 10 | Sinais numéricos |
| U+0021–U+005F (pontuação) | 21 | Modificadores e conectores |
| U+00A0–U+00FD (Latin-1) | 62 | Diacríticos e sinais estendidos |
| **Total** | **145** | glifos com conteúdo visual |

---

## Critérios Psicofísicos (ISO 11548-2)

A análise avalia cada candidato contra **7 critérios**:

| Critério | Limiar |
|---|---|
| Espaçamento entre pinos | $\geq 2{,}5\ \text{mm}$ |
| Gap entre pinos adjacentes | $\geq 1{,}0\ \text{mm}$ |
| Razão espaçamento/diâmetro | $\geq 1{,}5\times$ |
| Eixo menor da célula (1 dedo) | $\leq 25\ \text{mm}$ |
| Eixo maior da célula (multi-dedo) | $\leq 55\ \text{mm}$ |
| Razão de aspecto | $\leq 2{,}5\times$ |
| Capacidade sequencial (glifos/tira) | entre 4 e 8 glifos |

---

## Funcionalidades

=== "Análise"
    - Carrega a fonte ELIS e extrai todos os 145 codepoints mapeados
    - Avalia cada combinação $M \times N$ de resolução e espaçamento
    - Produz relatório de cobertura (glifos aptos / total)
    - Classifica o modo de leitura: 1-dedo, multi-dedo ou fora-de-alcance

=== "Candidatos"
    - Filtra e ranqueia candidatos viáveis
    - Identifica o melhor candidato sequencial e o mais econômico
    - Persiste resultados em JSON para reutilização entre sessões

=== "Visualização"
    - Gera grade visual PNG de diagnóstico
    - Preview da tira tátil por glifo
    - Galeria inline com download direto

=== "Modelo 3D"
    - Gera arquivos **STL** e **3MF** da tira tátil com os glifos da sequência
    - Visualizador Three.js interativo embutido
    - Modelo de teste completo (todos os pinos levantados)

---

## Como Executar

```bash
# CLI
uv run glifo-analise

# Interface Web (FastAPI + Vue 3)
./scripts/start.sh    # produção  — http://localhost:8080
./scripts/dev.sh      # dev mode  — http://localhost:5173 (hot-reload)

# Docker
cd docker && ./manage.sh up
```

---

## Requisitos de Hardware (Alvo)

Um **display matricial de pinos táteis** com grade de $N \times N$ posições que
eleva/abaixa pinos metálicos ou plásticos, permitindo que uma pessoa cega toque
o glifo e identifique o sinal ELIS pelo relevo.

---

## Licença e Citação

Distribuído sob licença **MIT** com cláusula de atribuição.

```bibtex
@software{nascimento2024glifoanalise,
  author  = {Nascimento, Maxwell Amairal do},
  title   = {Glifo Análise},
  year    = {2024},
  url     = {https://github.com/maxwellamaral/glifo-analise}
}
```
