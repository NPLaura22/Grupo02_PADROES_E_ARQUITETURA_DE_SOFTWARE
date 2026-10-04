# Entrega 4b — Respostas do Grupo 02 às objeções do Grupo 04

**Respondem:** Grupo 02 (Saúde, envelope E)
**Objeções recebidas de:** Grupo 04 (Saúde, envelope D), sobre o commit `140610b`

Recebemos nove objeções. Aceitamos seis, aceitamos três em parte e, nesses casos, rebatemos pontos específicos com argumento. Nenhuma foi ignorada. Onde aceitamos, dizemos o que vai mudar e em qual artefato.

**Estado desta entrega:** o repositório continua no commit `140610b` e não foi alterado. As mudanças descritas abaixo são a revisão prevista pelo grupo em resposta às objeções; ainda não foram aplicadas.

| # | Objeção | Posição | O que vai mudar |
|---|---|---|---|
| 1 | Spike prova decisão de outro caso | Aceita em parte (rebate o cenário c) | Spike a refazer em Saúde |
| 2 | *Crypto-shredding* vs. guarda de 20 anos | Aceita | Dados classificados por base legal; shredding só onde a lei permite |
| 3 | Trilha depende de publicação que pode se perder | Aceita | Outbox transacional; leitura de prontuário *fail-closed* |
| 4 | Offline abre acessos fora da trilha e espalha chaves | Aceita em parte | Log local encadeado, DEK com TTL, cache restrito |
| 5 | "Event Sourcing" não reconstrói a operação | Aceita | Renomear; eventos de estado completo em dois agregados |
| 6 | "Imutável" só por convenção | Aceita | Um só store, cadeia de hashes e WORM |
| 7 | Lock mantido durante chamada HTTP ao legado | Aceita | Máquina de estados e novo ADR 06 |
| 8 | Expurgo fora da trilha | Aceita em parte | Trilha e aprovação; executor serverless mantido |
| 9 | Prazo de 24h e anonimização da notificação | Aceita | Relógio de prazo; anonimização removida |

---

## Objeção 1 — A spike prova a decisão de outro caso

**Posição: aceita em parte (rebatemos o cenário c).**

A crítica procede. O README entregue se identifica como "Grupo 5 · Ônibus" e o código modela viagens e repasse. Ele não prova o ADR 05 no caso Saúde, e o próprio README reconhecia a lacuna. Também procede que o risco central do envelope E é provar quem acessou cada prontuário.

Rebatemos dois pontos:

- **Leitura e outbox.** A afirmação de que leituras "não se resolvem com a outbox" vale para o desenho antigo. No desenho revisado (Objeção 3), cada leitura de prontuário grava o registro de acesso na outbox, na mesma transação da consulta. É o mesmo mecanismo.
- **Cenário (c), expurgo.** A entrega pede um programa por decisão, e o expurgo pertence ao ADR 02, não ao ADR 05. Além disso, com a mudança da Objeção 2, o prontuário não é expurgado durante o prazo legal, então o cenário perde o sentido na forma proposta.

**O que vai mudar:** vamos substituir integralmente `3-spike/exemplo.py`, o README e `saida-esperada.txt` por uma versão em Saúde. Ela cobrirá (a) registro de acesso de leitura e de dispensação com falha entre gravar e publicar, e (b) reconstrução, só a partir da auditoria, de quem acessou o registro X no dia D.

## Objeção 2 — O *crypto-shredding* apaga o prontuário que a lei manda guardar por 20 anos

**Posição: aceita.**

Reconhecemos o erro. A LGPD não manda eliminar dado que o controlador deve guardar por obrigação legal (art. 16, I; art. 18, VI), e a Lei 13.787/2018 (art. 6º) só permite eliminar prontuário depois de 20 anos do último registro. A frase "atende 100% à exigência legal" no ADR 02 e a resposta 3 do §4 ("os dados do prontuário tornam-se indecifráveis") tratavam o expurgo como automático. Para o prontuário dentro do prazo, isso está errado. Também procede a observação sobre a trilha: cifrar o identificador do paciente com a DEK dele impede o auditor de saber quem acessou o prontuário de quem.

**O que vai mudar (ADR 02 revisado):**

1. Os dados são classificados por base legal antes de se escolher o mecanismo. Prontuário, dispensação e notificações ficam fora do *crypto-shredding* durante a guarda. O pedido do titular recebe resposta fundamentada no art. 16, I.
2. O *crypto-shredding* continua para dados tratados por consentimento e para o fim do prazo. Vencidos os 20 anos, o job de retenção destrói a chave, que é a forma de eliminar dado dentro de um store append-only.
3. Os eventos de auditoria usam um identificador pseudônimo estável do paciente, fora da DEK. Só os identificadores diretos (nome, CPF, contato) ficam cifrados.
4. O ADR passa pela revisão do responsável de conformidade. Sairão do texto "100%" e "instantâneo".

## Objeção 3 — A trilha "completa" depende de uma publicação que pode se perder

**Posição: aceita.**

É *dual write*. O ADR 05 pedia "perda zero" sem mecanismo no documento, e um interceptor AOP "sem impactar o fluxo" não serve para leitura de prontuário. Acrescentamos um ponto ao desenho do revisor: a outbox fica no mesmo PostgreSQL que serve o prontuário, então o *fail-closed* não cria um novo modo de indisponibilidade. Se o banco está fora, o prontuário também está. Se só o barramento está fora, a leitura continua e o registro espera na outbox.

**O que vai mudar (C4 nível 2 e ADR 05):**

- Outbox transacional no `dbCore` para toda escrita auditável e para todo acesso de leitura a prontuário.
- O registro de acesso é gravado antes de o dado ser devolvido. Se não gravar, o prontuário não é exibido.
- O relay outbox → barramento aparece no diagrama e no ADR, com consumidor idempotente no serviço de auditoria.

## Objeção 4 — O modo offline abre acessos fora da trilha e espalha chaves nos navegadores

**Posição: aceita em parte.**

Procede. A captura por AOP no servidor não enxerga o que acontece no IndexedDB, o documento não dizia onde ficam as DEKs offline, e ADR 02 e ADR 04 entravam em conflito. O "instantâneo" do *crypto-shredding* também não alcança cópias locais.

Rebatemos um ponto. "Pacientes agendados do dia" funciona na UBS, mas a UPA atende demanda espontânea e não dá para prever quem chega. Na UPA não haverá pré-carga de prontuários: offline, ela registra o atendimento corrente e não consulta histórico. Esse custo clínico é real e deve ser validado com a área assistencial. Mesmo assim preferimos aceitá-lo a espalhar prontuários completos pelos navegadores.

**O que vai mudar (ADR 04 revisado, trecho novo no ADR 02, §1.2.1 e C4):**

- **UBS:** cache limitado aos pacientes agendados do dia. DEKs em cache com TTL curto, descartadas na sincronização.
- **Log local:** acessos registrados em log append-only encadeado por hash, sincronizado junto com o buffer. Entra na trilha central com o *timestamp* original e marcado como origem offline.
- **UPA:** sem pré-carga de prontuários.
- **C4:** passará a mostrar o agente de sincronização.

## Objeção 5 — O que foi chamado de *Event Sourcing* não reconstrói as operações fiscalizadas

**Posição: aceita.**

O estado de verdade está no PostgreSQL e o store recebe um log derivado. Chamá-lo de *Event Sourcing* foi impreciso. A matriz já marcava "Em parte", mas o C4 e o texto diziam "Serviço de Event Sourcing". O payload do §1.3.1 (médico, paciente, ação, IP) não reconstrói o que foi dispensado se a linha operacional mudar depois.

Das duas saídas propostas, escolhemos eventos de domínio com estado completo emitidos pela outbox, e não *Event Sourcing* de verdade. Esse segundo caminho faria do store a fonte de verdade e traria projeções, versionamento de eventos e replay para o PostgreSQL, o custo que a matriz já apontava para uma equipe de 15. A reconstrução histórica exigida se obtém sem isso.

**O que vai mudar:**

- Dispensação e notificação compulsória emitem eventos com o estado completo da mudança: medicamento, lote, dose, versão da prescrição, valores antes e depois.
- Os demais módulos mantêm log de auditoria simples.
- "Serviço de Event Sourcing / Auditoria" passa a "Serviço de Auditoria".
- Na matriz, a linha 11 (Event Sourcing) passa a "Não" como estilo e a síntese descreve log de auditoria com eventos de estado completo, dentro da EDA.

## Objeção 6 — "Imutável" só por convenção

**Posição: aceita.**

Trigger e permissão podem ser desligados por quem administra o banco, e o ADR 05 deixava dois candidatos em aberto. Uma nota: a frase do README da spike sobre proteção contra administrador era um limite declarado da prova de uma decisão (outbox e idempotência), não da arquitetura. A lacuna da arquitetura é a que o revisor aponta.

**O que vai mudar (ADR 05 e C4):**

- **Tecnologia:** decidimos por PostgreSQL particionado append-only. O time já opera PostgreSQL, e o EventStoreDB seria mais uma plataforma para 15 pessoas, o mesmo argumento que usamos contra microsserviços.
- **Cadeia de hashes:** cada evento carrega o hash do anterior dentro da partição. A cadeia é por partição diária, para não serializar todas as escritas.
- **WORM:** o hash de cada lote diário é gravado em armazenamento WORM (Object Lock em modo *compliance*).
- **Verificação:** a checagem da cadeia fica disponível ao auditor e ao responsável de conformidade.

## Objeção 7 — A reserva de leito segura um lock durante uma chamada HTTP ao legado

**Posição: aceita.**

Um lock pessimista mantido durante a chamada HTTP prende conexão e leito pelo tempo de resposta do legado, e um timeout deixa reserva fantasma. A resposta 2 oferecia "Pessimistic Locking ou Locks Distribuídos" sem decidir e citava o ADR 05, que não trata de locking. Essa citação foi erro nosso.

**O que vai mudar (novo ADR 06, resposta 2 e C4 nível 3):**

- **Uma autoridade por leito:** o legado enquanto o leito não migrou, o núcleo depois, e o outro lado só leitura.
- **Estados da reserva:** `SOLICITADA → PENDENTE_LEGADO → CONFIRMADA/RECUSADA`, com chave de idempotência.
- **Disputa entre duas unidades:** resolvida por uma transação curta no PostgreSQL (restrição de unicidade ou versão no leito) que não atravessa a chamada externa.
- **Trilha e timeout:** cada transição vai para a trilha. Um timeout leva à reconciliação com o legado, não a um rollback cego.
- **`legadoAdapter`:** deixa de ser "sincronização bidirecional" e passa a escrever no legado só enquanto ele é a autoridade.

## Objeção 8 — O expurgo LGPD, a operação mais sensível, fica fora da trilha

**Posição: aceita em parte.**

A falha principal procede. No C4 nada dispara o `serverlessWorker` e nada registra quem pediu, quem aprovou e quando, apesar do art. 37 da LGPD.

Rebatemos a conclusão de tirar a função do *serverless*. O motivo da função separada não é elasticidade (concordamos que o volume é baixo), e sim segregação de privilégio: só ela tem permissão de destruir chaves. O monolito, que é a superfície maior e tem 15 pessoas mexendo, não terá. Sobre testabilidade e observabilidade: o fluxo (pedido, aprovação, eventos, idempotência) fica no núcleo, testável em processo. A função fica fina: recebe o comando e chama o KMS.

**O que vai mudar (ADR 01, C4 níveis 2 e 3, matriz linha 8):**

- Um módulo LGPD no núcleo recebe o pedido, exige aprovação do responsável de conformidade e grava `ExpurgoSolicitado` e `ExpurgoAprovado` na trilha antes de qualquer destruição.
- O relay da outbox dispara a função (a seta que faltava no C4). A função é idempotente e reporta ao núcleo, que grava `ExpurgoExecutado`.
- Na matriz, o *serverless* fica restrito ao executor de chaves e a relatórios eventuais.

## Objeção 9 — A notificação compulsória é anonimizada e o prazo de 24h não é controlado

**Posição: aceita.**

Retentativa com backoff não garante prazo, e um evento preso no IndexedDB nem chega ao barramento. A frase "garante o envio dentro das 24 horas" era uma promessa sem controle. Também procede quanto à anonimização: a vigilância precisa identificar o caso, e esse tratamento tem amparo na LGPD como obrigação legal e tutela da saúde (art. 11, II).

**O que vai mudar (ADR 03, resposta 4 e C4 nível 2):**

- **Relógio de prazo:** cada notificação tem um relógio contado a partir do *timestamp* do atendimento, não da chegada ao barramento.
- **Alertas e contingência:** alerta em 12h ao responsável da vigilância municipal. Antes de vencer as 24h, contingência por canal alternativo com registro manual auditado.
- **Trilha:** eventos `NotificacaoEnviada` e `NotificacaoAtrasada`.
- **Offline:** notificações compulsórias têm prioridade na fila de sincronização (ligação com a Objeção 4).
- **Pipeline:** a etapa de anonimização sai do pipeline de notificação compulsória e fica só nos extratos analíticos. O Pipes & Filters continua, com validação FHIR, envio e retentativas.

---

## Artefatos que serão alterados

- **ADRs:** 02 (base legal), 03 (prazo de 24h), 04 (offline, trilha e DEK) e 05 (outbox, store único, hash e WORM) revisados. ADR 06 novo, sobre reserva de leito.
- **C4:** nível 2 ganha outbox e relay, agente de sincronização e a seta do expurgo, e perde o EventStoreDB. Nível 3 ganha o módulo LGPD e o `legadoAdapter` ajustado.
- **Matriz:** linhas 8 (*serverless*) e 11 (*Event Sourcing*) e a síntese.
- **Respostas do §4:** 1, 2, 3 e 4 reescritas.
- **Spike:** a ser substituída por versão em Saúde.

## Correções que identificamos por conta própria

Na releitura apareceram quatro problemas que ninguém apontou:

- Citações trocadas: a resposta 2 cita o ADR 05 para locking, e a resposta 1 cita o *Serverless Worker* como sustentação do modo offline. Passarão a citar os ADRs corretos (ADR 06 e ADR 04).
- Restos de edição (`[cite: 6]`) no ADR 01 serão removidos.
- O mapa de decisões diz que o Agendamento será extraído em serviço escalável, mas o ADR 01 e o C4 o mantêm no núcleo. Vamos alinhar os dois textos.
- Kafka/RabbitMQ e "Go / Node.js" aparecem em aberto no C4. Vamos escolher uma opção e justificar.
