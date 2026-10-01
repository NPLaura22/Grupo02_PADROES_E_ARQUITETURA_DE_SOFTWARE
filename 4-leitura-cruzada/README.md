# Entrega 4: Leitura Cruzada — Avaliação Crítica do Grupo 05 (Envelope A)

Este arquivo contém a documentação da **Entrega 4 (Leitura Cruzada)**, referente à análise crítica e auditoria técnica efetuada sobre a solução arquitetural proposta pelo **Grupo 05**, projetada sob as restrições do **Envelope A**.

## Conteúdo do Arquivo

* [`objecoes-enviadas.md`](./objecoes-enviadas.md): Documento completo de objeções técnicas, incluindo o passo a passo metodológico, análise de riscos por decisão, quadro resumo e as 7 objeções detalhadas.

## Escopo e Critérios da Entrega

A leitura cruzada foi estruturada rigorosamente segundo os critérios de avaliação, apresentando **7 objeções arquiteturais** (respeitando a faixa exigida de 5 a 10 objeções).

Cada objeção contida no documento é obrigatoriamente dividida em três partes fundamentais:

1. **Trecho Atacado:** Identificação precisa da decisão, ADR, componente ou arquivo analisado, especificando o arquivo e a seção exata.
2. **Argumento Técnico:** Demonstração fundamentada do porquê a decisão não se sustenta no **Envelope A** (time de 6 devs, sem equipe de Ops, caixa para 6 meses, entrega do piloto em 4 meses para 3 UBSs, picos de vacinação de 20x), evidenciando custos ocultos, gargalos de infraestrutura ou riscos operacionais ignorados.
3. **Contraproposta da Equipe:** Descrição clara e pragmática do que o nosso grupo teria feito no lugar para resolver a questão dentro das limitações reais do envelope.

---

## Resumo das Objeções Registradas

| # | Objeção Técnico-Arquitetural | Trecho Atacado | Risco / Custo Ignorado | Contraproposta da Equipe |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **Vulnerabilidade de Concorrência e Locks no BD Central** | `1-adrs/0002-definir-propriedade-e-consistencia-dos-dados.md` (*Decisão*) | Picos de vacinação de 20x no BD relacional único gerarão contenção de *row locks*, degradando o atendimento de emergência nas UPAs. | Desacoplamento do BD de Vacinação ou buffer de escrita assíncrona/batch para doses. |
| **2** | **Ausência de Archiving para Prontuários (20 Anos)** | `1-adrs/0002-definir-propriedade-e-consistencia-dos-dados.md` (*Opções consideradas*) | Terabytes de dados históricos quentes no BD relacional estouram o caixa de 6 meses e inviabilizam rotinas de *backup/restore*. | Implementação de *Data Lifecycle Management* enviando dados > 2 anos para *Cold Storage* (S3 Glacier/Archive). |
| **3** | **Uso Ineficiente de Serverless (FaaS) para Filas Longas** | `1-adrs/0004-operar-com-uma-unidade-principal...md` (*Decisão*) | Múltiplas horas de indisponibilidade do governo gerarão *cold starts* massivos e explosão de custos em FaaS no reenvio. | Uso de *Background Workers* no próprio container do Monolito Modular, aproveitando a capacidade já paga. |
| **4** | **Omissão de Resolução de Conflitos em Sync Offline** | `1-adrs/0005-sincronizar-atendimentos-offline...md` (*Decisão*) | O mecanismo trata apenas duplicidade de chave, omitindo a fusão e resolução de conflitos de cadastros/triagens divergentes. | Definição explícita de *Vector Clocks*, regras *Last-Write-Wins* ou filas de reconciliação para divergências clínicas. |
| **5** | **Bloqueio na Dispensação de Remédios com Receita Offline** | `2-arquitetura/c4-componentes.md` (*Componente Farmácia*) | Validação síncrona com o Prontuário falha na farmácia central se o atendimento da UBS ocorreu offline e ainda não sincronizou. | Processamento otimista na Farmácia (registro por confiança com validação assíncrona posterior pós-sync). |
| **6** | **Visão Desatualizada de Leitos no Estrangulamento do Legado** | `1-adrs/0003-integrar-legado-e-terceiros...md` (*Decisão*) | A ausência de replicação ou consulta passiva faz a aplicação nova exibir estados de leitos obsoletos gerenciados no legado. | Sincronização passiva de leitura (*Change Data Capture* ou polling no BD legado) para manter o *read model* atualizado. |
| **7** | **Multiplicidade de Pontos de Ops para Equipe Reduzida** | `1-adrs/0006-notificar-vigilancia-por-fila-persistente.md` (*Consequências*) | Arquitetura distribuída (Fila + FaaS + BD + DLQ) desvia o time de 6 devs da entrega do piloto de 4 meses devido à complexidade de Ops. | Centralização da fila no banco via padrão *Transactional Outbox* processado por agendador interno. |

---

## Metodologia de Análise Aplicada

A análise foi conduzida em 6 etapas estruturadas:
1. Mapeamento das restrições do Envelope A.
2. Avaliação de consistência das ADRs (0001 a 0006).
3. Inspeção e confronto dos Diagramas C4 (Contexto, Contêineres e Componentes).
4. Análise de rastreabilidade do mapa de decisões e respostas obrigatórias.
5. Validação do código do Spike (`exemplo.py`).
6. Seleção final das 7 objeções de maior impacto financeiro e operacional.

> Para consultar o detalhamento completo de cada argumento e trecho analisado, consulte o arquivo [`objecoes-enviadas.md`](./objecoes-enviadas.md).
