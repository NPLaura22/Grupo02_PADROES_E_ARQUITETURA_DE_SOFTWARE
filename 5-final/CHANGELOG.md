# CHANGELOG — Documentação de Arquitetura de Software (Envelope E)

Este documento registra todas as modificações, refatorações e reestruturações aplicadas ao repositório a partir da leitura cruzada efetuada pelo **Grupo 04**

---

### Resumo das Mudanças Principais
* **Reformulação dos ADRs Existentes:** Revisão substancial dos ADRs 01, 02, 03, 04 e 05 para correção de falhas conceituais sobre LGPD vs. Guarda Regulatória de 20 anos, eliminação de *Dual Write*, garantia de imutabilidade via *WORM* e reestruturação da trilha de auditoria.
* **Criação do ADR 06 (Novo):** Transição de modelo de concorrência e reserva de leitos para desacoplar travas transacionais de chamadas HTTP externas ao sistema legado.
* **Ajuste Fino na Linguagem e Modelagem Arquitetural:** Eliminação de citações imprecisas a *Event Sourcing* estrito, redefinição das fronteiras de *Serverless* e revisão dos Diagramas C4 (Níveis 2 e 3).
* **Substituição Integral do Spike Técnico (`3-spike/`):** Substituição da demonstração genérica em transporte público por um *Spike* totalmente contextualizado no domínio de Saúde Municipal (garantia de outbox, reconstrução histórica de acessos e resiliência de auditoria).

---

## 1. Alterações Detalhadas por Artefato

### 1.1. Registros de Decisão Arquitetural (`2-arquitetura/ADRs/`)

#### ADR 01: Composição Híbrida e Extensão Serverless
* **Status:** Mantido como Aprovado (com redefinição interna de fronteiras).
* **O que mudou:** O *Serverless Worker* (AWS Lambda / Cloud Functions) teve seu escopo estritamente limitado ao encargo de destruição de chaves no KMS sob ordenamento do núcleo e à geração de relatórios esporádicos. O fluxo de decisão, elegibilidade de expurgo e auditoria da solicitação de expurgo retornaram ao núcleo transacional (`Módulo LGPD`).
* **Motivo:** Atender à Objeção 8 (ausência de controle, aprovação e trilha de auditoria para ações de expurgo LGPD).

#### ADR 02: Gestão de Dados – Classificação por Base Legal e Crypto-Shredding
* **Status:** **Substituído** pelo **ADR 02 (Revisado)**.
* **O que mudou:**
  * Removida a alegação de "expurgo e cifragem instantânea de 100% dos dados".
  * Estabelecida a segregação por Base Legal: Prontuários, dispensações e notificações compulsórias são protegidos pela obrigação legal de guarda de 20 anos (Lei 13.787/2018; CFM) e **não sofrem *crypto-shredding*** durante esse período (LGPD, Art. 16, I).
  * O *crypto-shredding* é mantido apenas para dados tratados por consentimento ou após o vencimento do prazo prescricional de 20 anos.
  * O identificador do paciente nos eventos de auditoria passa a utilizar um pseudônimo estável desvinculado da DEK, garantindo que a trilha de auditoria continue consultável para o auditor mesmo se os dados PII diretos forem expurgados.
* **Motivo:** Atender à Objeção 2 (incompatibilidade entre o *crypto-shredding* irrestrito e a legislação federal de prontuários médicos).

#### ADR 03: Ingestão de Notificações Compulsórias e Prazos da Vigilância
* **Status:** **Substituído** pelo **ADR 03 (Revisado)**.
* **O que mudou:**
  * Removida a etapa de anonimização do *Pipeline Worker* para Notificações Compulsórias (a vigilância epidemiológica necessita da identificação do cidadão, respaldada pelo Art. 11, II da LGPD).
  * Adicionado um mecanismo de controle de SLA de 24 horas baseado em *timestamp* de origem do atendimento clínico (não da chegada ao barramento).
  * Definidos alertas preventivos em 12 horas e canal de contingência manual caso o enlace com a RNDS permaneça indisponível próximo ao limite de 24h.
* **Motivo:** Atender à Objeção 9 (falha de conformidade na anonimização de dados epidemiológicos e falta de garantias reais para o cumprimento do prazo regulatório de 24h).

#### ADR 04: Operação Offline-First e Políticas de Cache em UBS/UPA
* **Status:** **Substituído** pelo **ADR 04 (Revisado)**.
* **O que mudou:**
  * Segregação das políticas *Offline*: As UBSs passam a realizar pré-carga em cache apenas para pacientes agendados no dia, utilizando DEKs com TTL reduzido e descarte automático após a sincronização.
  * As UPAs não realizam pré-carga de histórico de prontuários devido à imprevisibilidade da demanda espontânea, limitando-se a registrar o atendimento corrente localmente.
  * Registros offline passam a ser encadeados em log local *append-only* com verificação por hash e integrados à trilha central com marcação de origem offline e *timestamp* original.
* **Motivo:** Atender à Objeção 4 (vazamento e dispersão de chaves/prontuários em navegadores no modo offline e falta de rastreabilidade na trilha local).

#### ADR 05: Segregação de Banco Transacional e Store Imutável de Auditoria
* **Status:** **Substituído** pelo **ADR 05 (Revisado)**.
* **O que mudou:**
  * Removida a nomenclatura imprecisa de "*Event Sourcing*" para o modelo geral da aplicação, redefinindo-o como **Log de Auditoria com Eventos de Estado Completo** emitidos via **Outbox Transacional** no `dbCore`.
  * Escolha tecnológica consolidada no **PostgreSQL Particionado (Append-Only)**, descartando o EventStoreDB para evitar sobrecarga operacional sobre a equipe.
  * Inclusão de **Outbox Transacional** no mesmo banco do prontuário (`dbCore`), garantindo leitura e gravação de acesso *fail-closed* (se a outbox falhar, o prontuário não é exibido).
  * Implementação de **Cadeia de Hashes por partição diária** e gravação do hash de fechamento em **Armazenamento WORM (Object Lock em modo compliance)**.
* **Motivo:** Atender às Objeções 3, 5 e 6 (eliminação do problema de *Dual Write*, imprecisão no conceito de *Event Sourcing* e falta de garantias físicas de imutabilidade).

#### ADR 06 (NOVO): Regulação de Leitos com Máquina de Estados e Decoupling Transacional
* **Status:** **Aprovado** (Novo ADR).
* **O que mudou:**
  * Fica proibida a retenção de *locks* relacionais/pessimistas no PostgreSQL durante chamadas de rede HTTP externas ao sistema legado.
  * Estabelecida uma máquina de estados explícita (`SOLICITADA` → `PENDENTE_LEGADO` → `CONFIRMADA`/`RECUSADA`) acompanhada de chave de idempotência.
  * A disputa concorrente de leitos passa a ser resolvida por uma transação curta no banco local, enquanto a comunicação com o legado ocorre de forma assíncrona/reconciliada.
* **Motivo:** Atender à Objeção 7 (risco de trava de leitos e conexões de banco durante latência/timeout de chamadas HTTP ao sistema legado).

---

### 1.2. Diagramas de Arquitetura C4 (`2-arquitetura/1-c4/`)

#### Diagrama de Contêineres (Nível 2)
* **Inclusões:** Adicionado o componente de *Transactional Outbox* no `dbCore`, o serviço de *Relay Outbox*, e o agente local de sincronização das UBSs. Adicionada a seta de disparo direcionada do *Relay* para o *Serverless Worker*.
* **Remoções/Ajustes:** Removida a referência ao EventStoreDB (substituído por PostgreSQL Particionado Append-Only + WORM). A etapa de anonimização no *Pipeline Worker* foi isolada e mantida apenas para relatórios analíticos, sendo removida das Notificações Compulsórias.
* **Padronização:** Tecnologias consolidadas (PostgreSQL para dados operacionais e auditoria; Apache Kafka para mensageria assíncrona; Java/Spring Boot no Núcleo).

#### Diagrama de Componentes (Nível 3)
* **Inclusões:** Adicionado o **Módulo LGPD** no núcleo monolítico para recepção, validação, aprovação humana de conformidade e publicação dos eventos `ExpurgoSolicitado` e `ExpurgoAprovado`.
* **Ajustes:** O `legadoAdapter` teve sua responsabilidade ajustada para escrita direcionada no legado estritamente durante a fase em que o legado detém a autoridade sobre o leito, passando a atuar apenas como consulta após a migração.

---

### 1.3. Matriz de Rastreabilidade e Decisões (`1-matriz/matriz.md`)

* **Linha 8 (Serverless):** Reescrita para refletir que o estilo *Serverless* atua exclusivamente na execução pontual da destruição de chaves criptográficas no KMS e em relatórios, sob comando da outbox.
* **Linha 11 (Event Sourcing):** Status alterado para "Não", redefinindo a justificativa para **Arquitetura Orientada a Eventos (EDA)** com **Outbox Transacional e Log de Auditoria com Eventos de Estado Completo**.
* **Alinhamento do Agendamento:** Unificada a decisão de manter o módulo de Agendamento dentro do Monolito Modular, prevendo extração isolada apenas se houver necessidade comprovada de escala durante campanhas vacinais sazonais.

---

### 1.4. Respostas às Perguntas Obrigatórias do Caso (`2-arquitetura/perguntas.md`)

* **Resposta 1 (Triagem UPA e Modo Offline):** Atualizada para detalhar a política da UPA sem pré-carga de prontuários, gravação em log local encadeado e sincronização ordenada via Kafka sustentada pelo **ADR 04**. Citação corrigida (removida citação ao *Serverless Worker*).
* **Resposta 2 (Concorrência de Leitos e Legado):** Reescrita para fundamentar a reserva única através da máquina de estados transacional curta e autoridade única, citando explicitamente o **ADR 06** e **ADR 03** (removida citação errônea ao ADR 05).
* **Resposta 3 (Trilha de Acesso e LGPD vs. 20 Anos):** Ajustada para explicar a convivência legal entre a imutabilidade do log (com pseudônimos) e a destruição de chaves via *Crypto-shredding* restrita aos dados elegíveis, citando o **ADR 02** e **ADR 05**.
* **Resposta 4 (Notificação Compulsória em até 24h):** Atualizada para incluir o relógio de SLA baseado no atendimento de origem, alertas preventivos em 12h, contingência manual e remoção da anonimização, sustentada pelo **ADR 03**.
* **Resposta 5 (Substituição do Legado):** Ajustada para refletir a estratégia de *Strangler Fig* com transferência de autoridade por leito e máquina de estados, sustentada pelo **ADR 01**, **ADR 03** e **ADR 06**.

---

### 1.5. Código de Prova de Conceito / Spike Técnico (`3-spike/`)

* **Substituição Completa:** O código genérico de transporte público (`exemplo.py`) foi removido.
* **Novo Código (`3-spike/src/`):** Implementada uma aplicação Python/SQL contextualizada no domínio de **Saúde Publica (Envelope E)** demonstrando:
  1. Leitura de prontuário com gravação síncrona na tabela de *Outbox Transacional* dentro da mesma transação do banco de dados.
  2. Mecanismo de *Fail-Closed*: simulação de falha na gravação da outbox que impede a exibição do prontuário ao médico.
  3. Leitura e reconstituição completa do histórico de acessos de um paciente a partir do repositório de auditoria.
* **Documentação:** `README.md` e `saida-esperada.txt` reescritos para documentar a prova de conceito do **ADR 05** e **ADR 02** no contexto do Envelope E.

---

## 2. Correções Internas Adicionais (Auto-Revisão)

Durante o processo de reestruturação, foram identificadas e corrigidas as seguintes inconsistências internas no repositório:

1. **Citações Cruzadas Incorretas:** A Pergunta 1 citava indevidamente o *Serverless Worker* para sustentar a operação offline (corrigido para ADR 04); a Pergunta 2 citava o ADR 05 para travas de concorrência (corrigido para ADR 06).
2. **Remoção de Artefatos de Edição:** Varredura e remoção de marcas residuais de texto e tags de edição (ex: ``).
3. **Harmonização do Módulo de Agendamento:** Mapeamento alinhado entre o C4 Nível 2, ADR 01 e a Matriz de Decisões, mantendo o Agendamento no Monolito Modular.
4. **Decisão Tecnológica do Barramento e Serviços:** Eliminação de opções em aberto no C4 Nível 2 e 3; consolidação em **Apache Kafka** (Barramento) e **Java / Spring Boot** (Núcleo).

---

## 3. Matriz de Objeções e Ações Aplicadas

| Objeção | Posição | Artefatos Afetados | Resumo da Ação |
| :--- | :--- | :--- | :--- |
| **01. Spike inadequado ao caso** | Aceita em parte | `3-spike/` (código, README, saída) | Código reescrito no domínio de Saúde focado na outbox de leitura e auditoria. |
| **02. *Crypto-shredding* vs. Guarda 20 anos** | Aceita | ADR 02, C4 Nível 2 e 3, Pergunta 3 | Segregação por base legal. Prontuários protegidos da exclusão por 20 anos. Pseudônimos na trilha. |
| **03. Perda de mensagens na trilha** | Aceita | ADR 05, C4 Nível 2 e 3, `3-spike/` | Outbox transacional no PostgreSQL; gravação de acesso em modelo *fail-closed*. |
| **04. Riscos do modo Offline** | Aceita em parte | ADR 04, ADR 02, C4 Nível 2, Pergunta 1 | Cache da UBS restrito aos agendados do dia; UPA sem pré-carga; log local com hash. |
| **05. Imprecisão no *Event Sourcing*** | Aceita | ADR 05, C4 Nível 2, Matriz | Conceito redefinido para Log de Auditoria com Eventos de Estado Completo via Outbox. |
| **06. Imutabilidade frágil** | Aceita | ADR 05, C4 Nível 2 | PostgreSQL Particionado Append-Only + Cadeia de Hashes + Armazenamento WORM. |
| **07. Lock transacional preso em HTTP** | Aceita | ADR 06 (Novo), C4 Nível 3, Pergunta 2 | Remoção do lock distribuído/pessimista longo; introdução de Máquina de Estados e autoridade por leito. |
| **08. Expurgo LGPD fora da trilha** | Aceita em parte | ADR 01, C4 Nível 2 e 3, Matriz | Módulo LGPD no núcleo com aprovação e trilha; *Serverless* restrito à execução técnica no KMS. |
| **09. Falhas no prazo de 24h e anonimização** | Aceita | ADR 03, C4 Nível 2, Pergunta 4 | Relógio de SLA no atendimento; alertas em 12h; anonimização removida da notificação epidemiológica. |
