# Grupo 02 | Padrões e Arquitetura de Software

## Caso
**Caso 2: Rede Municipal de Atenção à Saúde**
Unificação do ecossistema municipal de saúde (UBSs, UPAs, Hospital de Referência, Regulação de Leitos, Farmácia Municipal e Vigilância Epidemiológica) com convivência temporária de 2 anos com o sistema legado de regulação.

### Premissas de Dimensionamento do Caso
- **Unidades:** 70 UBSs, 5 UPAs e 1 Hospital de Referência com 400 leitos regulados.
- **Atendimentos:** 12.000 atendimentos/dia na rede; UPA maior com pico de 40 triagens/hora (Protocolo de Manchester).
- **Prontuário:** Guarda obrigatória por 20 anos (normativa CFM/MS).
- **Rede nas UBSs:** Internet instável com quedas diárias que variam de minutos a horas.
- **Regulação de Leitos:** Reserva exclusiva (um leito por paciente) com concorrência em tempo real entre unidades e sistema legado.
- **Farmácia:** 1.200 itens de estoque com controle de lote e validade; dispensação vinculada à receita do prontuário.
- **Vigilância Epidemiológica:** Notificação compulsória de doenças transmissíveis em até 24 horas.
- **Campanhas Sazonais:** Agendamento de vacinação com picos de até 20 vezes o tráfego normal.
- **Proteção de Dados (LGPD):** Prontuário como dado altamente sensível; retenção legal de 20 anos combinada com o direito de acesso, revogação e expurgo do paciente.

---

## Envelope
**Envelope E — Conformidade e Fiscalização Regulatória**
- **Situação e Equipe:** Operação sob rigorosa fiscalização de órgãos reguladores. Equipe composta por 15 desenvolvedores e 1 responsável dedicado à conformidade/auditoria.
- **Infraestrutura:** Nuvem pública com exigência de trilha de auditoria completa e imutável.
- **Exigência Dominante:** Reconstrução histórica total de eventos sanitários convivendo com os direitos da LGPD (direito ao esquecimento e anonimização).
- **Foco do Envelope E:** Responder a *"Como guardar tudo para sempre de forma auditável e ainda assim apagar o que a lei manda apagar?"*
- **Ajustes pós-revisão:** A auditoria sanitária assegura o não-repúdio através de uma **Outbox Transacional** (*fail-closed*), **PostgreSQL Particionado Append-Only + Object Lock WORM** e **classificação estrita por Base Legal** (prontuários protegidos da exclusão por 20 anos pelo Art. 16, I da LGPD).

---

## Integrantes (Grupo 02)
- **Eduardo Sanvido Apolinario | 24013995**
- **Laura Nogueira Pereira | 24013968**
- **Nando Balzaneli Porzia | 24014674**
- **Guilherme Lopes de Almeida | 24017565**
- **Matheus Felis Lino | 24007502**

---

## Estrutura do Repositório

- **`1-matriz/`** — Matriz de Estilos Arquiteturais aplicada ao Envelope E (análise, justificativa e alinhamento dos estilos adotados e descartados, cobrindo a EDA com Outbox, Monolito Modular e eliminação do Event Sourcing estrito).
- **`2-arquitetura/`** — Documento de Arquitetura completo contendo Diagramas C4 (Contexto, Contêineres e Componentes), Mapa de Restrições e Decisões, **ADRs (01 a 06)** e as respostas revisadas às perguntas obrigatórias do caso.
- **`3-spike/`** — Prova de Conceito (PoC/Spike) em Python no domínio de **Saúde Pública**, demonstrando a resiliência da **Outbox Transacional** (ADR 05), eliminação de *Dual Write*, garantia de *Fail-Closed* na leitura do prontuário e a reconstrução histórica da trilha por paciente.
- **`4-leitura-cruzada/`** — Análise crítica e objeções arquiteturais fundamentadas sobre o repositório do grupo avaliado durante o processo de leitura cruzada.
- **`5-final/`** — Consolidação do repositório revisado após a leitura cruzada do Grupo 04, contendo o **`CHANGELOG.md`** detalhado (com justificativa para a aceitação/rebate de cada objeção) e a síntese final do projeto.
