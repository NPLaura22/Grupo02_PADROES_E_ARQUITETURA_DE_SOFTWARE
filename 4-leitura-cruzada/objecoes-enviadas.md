# Objeções Técnicas Arquiteturais (Leitura Cruzada)

**Repositório analisado:** [https://github.com/EnricoColella/PAS-grupo-05](https://github.com/EnricoColella/PAS-grupo-05)

## Passo a Passo Metodológico da Leitura Cruzada

Para realizar uma avaliação rigorosa, imparcial e tecnicamente fundamentada da solução proposta pelo Grupo 05, adotamos o seguinte fluxo de análise:

1. **Mapeamento do Envelope A e Restrições:**
   * Alinhamos todas as premissas do Envelope A (equipe de 6 devs, ausência de time de Ops, caixa para 6 meses, entrega do piloto em 4 meses para 3 UBSs, picos de vacinação de 20x e picos em UPAs).

2. **Análise das Decisões Arquiteturais (ADRs 0001 a 0006):**
   * Avaliamos a consistência individual e combinada das ADRs, identificando premissas implícitas, gargalos de infraestrutura, custos ocultos e pontos de acoplamento ou fragilidade operacional.

3. **Inspecção da Modelagem C4 (Contexto, Contêineres e Componentes):**
   * Confrontamos os diagramas C4 com o texto das ADRs para verificar a aderência dos componentes modelados e identificar lacunas no fluxo de dados em cenários críticos (ex.: operação offline, concorrência e integrações síncronas/assíncronas).

4. **Análise dos Documentos de Síntese e Rastreabilidade:**
   * Revisamos o `mapa-restricoes-decisoes.md` e o `respostas-perguntas.md` para averiguar se as justificativas respondiam diretamente aos desafios do problema ou se contornavam riscos operacionais significativos.

5. **Validação Técnica da Prova de Conceito (Spike - ADR 0005):**
   * Analisamos o código em Python (`exemplo.py`) para checar se a implementação simulava fielmente os cenários reais de borda (conflito de dados, reenvio e resiliência).

6. **Formulação e Seleção das Objeções:**
   * Filtramos divergências meramente estéticas ou de preferência de tecnologia. Selecionamos apenas 7 objeções críticas fundadas em **impacto financeiro, risco operacional, complexidade de infraestrutura ou violação de requisitos do Envelope A**.

---

Este documento apresenta uma análise crítica e objeções fundamentadas à solução proposta pela equipe avaliada, confrontando suas decisões arquiteturais (ADRs, Diagramas C4 e Respostas às Perguntas) contra o contexto real, restrições orçamentárias, operacionais e de equipe do **Envelope A** do Caso Saúde.

## Objeção 1: Vulnerabilidade de Concorrência e Bloqueio em Nível de Linha no Banco de Dados Único durante Picos de Carga

* **Trecho Atacado:**

  * **Arquivo:** `1-adrs/0002-definir-propriedade-e-consistencia-dos-dados.md`

  * **Seção:** *Decisão* e *Consequências*

  * **Arquivo auxiliar:** `2-arquitetura/mapa-restricoes-decisoes.md` (Tabela de Requisitos Críticos, linha "Campanha de vacinação gera pico de até 20 vezes o acesso normal")

* **Argumento:**
  A decisão **ADR 0002** define a utilização de um **único banco de dados relacional centralizado** operando sob consistência forte para múltiplos domínios de negócio simultâneos (Prontuário, Regulação, Estoque/Farmácia, Atendimento, Vacinação). O mapa de restrições assume que picos de acesso de até 20 vezes (como em campanhas mundiais ou municipais de vacinação) serão absorvidos apenas pelo autoscaling da aplicação na nuvem (**ADR 0004**).

  Entretanto, essa decisão ignora a restrição física de escrita em um banco de dados relacional central. Em um evento de vacinação em massa (que pode gerar dezenas de milhares de requisições concorrentes em poucas horas nas 70 UBSs), a gravação contínua de baixas no estoque de vacinas e inserção nos prontuários/vacinações causará **contenção severa de locks de tabelas/linhas (row-level locking)**, esgotamento do pool de conexões (*connection pool starvation*) e estouro do limite de I/O por segundo (IOPS). Como a aplicação é um monolito compartilhando o mesmo banco de dados, o travamento gerado pelo módulo de Vacinação **degradará diretamente o desempenho do módulo de Atendimento de Urgência e Triagem nas UPAs**, criando um ponto único de falha (*Single Point of Failure*) operacional e inviabilizando o atendimento emergencial.

* **O que teria sido feito no lugar:**
  Teríamos adotado o desacoplamento físico do banco de dados do módulo de **Vacinação/Campanhas** ou a implementação de uma estratégia de **buffer de escrita assíncrona** (por meio da fila gerenciada citada na ADR 0006) específica para eventos de imunização em massa. O registro imediato da dose seria gravado localmente ou jogado em uma fila de alta vazão para persistência em lote (*batch processing*), liberando a transação relacional principal e isolando o banco central dos picos de IOPS sem prejudicar as emergências das UPAs.

## Objeção 2: Ausência de Estratégia de Purga, Expurgos Legais e Particionamento no Banco do Prontuário com Retenção de 20 Anos

* **Trecho Atacado:**

  * **Arquivo:** `1-adrs/0002-definir-propriedade-e-consistencia-dos-dados.md`

  * **Seção:** *Opções consideradas* e *Consequências*

  * **Arquivo auxiliar:** `2-arquitetura/respostas-perguntas.md` (Pergunta 3)

* **Argumento:**
  No tratamento da Pergunta 3, a equipe argumenta que o módulo de Prontuário Eletrônico detém a responsabilidade pela guarda por 20 anos e auditoria de acesso. Contudo, ao optar por manter esses registros no mesmo banco de dados relacional operacional centralizado (ADR 0002) sem prever **arquivamento frio (*cold storage*) ou particionamento de dados**, a arquitetura ignora os custos financeiros acumulados de infraestrutura em nuvem e a degradação estrutural de queries a longo prazo.

  Armazenar 20 anos de histórico clínico com registros de auditoria detalhados (quem acessou, modificou, timestamps e payloads) de um sistema que atende 12 mil pessoas por dia resultará em **terabytes de dados em tabelas relacionais quentes**. Isso trará um custo exorbitante no serviço gerenciado de banco de dados (violando a restrição de "Caixa para 6 meses" e "Nuvem pública paga por uso"), tornará os rotinas de *backup/restore* inviáveis e reduzirá o desempenho do banco em consultas do dia a dia devido ao tamanho dos índices.

* **O que teria sido feito no lugar:**
  Teríamos estabelecido no ADR 0002 um ciclo de vida de dados (*Data Lifecycle Management*) explícito: dados ativos (últimos 12 a 24 meses) permanecem no banco relacional para busca rápida nas consultas. Dados históricos e trilhas de auditoria consolidadas com mais de 2 anos seriam exportados de forma imutável e compactada para um armazenamento de objetos a baixo custo (*Object Storage* como AWS S3 Glacier ou Azure Archive Storage), garantindo a retenção legal de 20 anos por um fração do custo, sem onerar o banco de produção.

## Objeção 3: Ineficiência Operacional e Risco de Latência pelo Uso de Serverless Functions (FaaS) para Processamento Continuo de Filas de Integração

* **Trecho Atacado:**

  * **Arquivo:** `1-adrs/0004-operar-com-uma-unidade-principal-e-servicos-gerenciados.md`

  * **Seção:** *Decisão*

  * **Arquivo auxiliar:** `1-adrs/0006-notificar-vigilancia-por-fila-persistente.md` (Seção *Decisão*)

* **Argumento:**
  A decisão **ADR 0004** e **ADR 0006** preconiza o uso de uma **função gerenciada (*Serverless/FaaS*)** para consumir tarefas de integração da fila persistente e despachá-las ao Sistema Federal (Vigilância Epidemiológica). Embora a motivação alegada seja "não operar infraestrutura própria", essa decisão ignora a dinâmica operacional e os custos das plataformas serverless quando expostas a processamentos retidos por longos períodos.

  Se o sistema federal permanecer indisponível por várias horas (cenário comum documentado nas restrições), milhares de mensagens ficarão acumuladas na fila. Quando a conexão for restabelecida, o disparo em massa da função gerenciada gerará um efeito de **Cold Start massivo**, gargalos de concorrência com estouro dos limites de execução simultânea (*concurrency limit quotas*) da nuvem, além de um custo de invocação e tempo de execução muito superior ao custo de um *worker* tradicional de segundo plano (*background worker process*) rodando dentro do próprio container da aplicação principal (já que se optou por um monolito modular).

* **O que teria sido feito no lugar:**
  Para o envelope de 6 desenvolvedores e sem equipe dedicada de Ops, a solução mais econômica e simples seria utilizar um **processo de background (Worker)** rodando dentro da própria instância do Monolito Modular (ou como um processo leve acoplado à unidade principal), consumindo a fila via agendador ou leitor de polling. Isso eliminaria a necessidade de configurar, monitorar e pagar por um serviço de FaaS separado em nuvem, aproveitando a capacidade já paga da aplicação principal.

## Objeção 4: Falta de Mecanismo de Resolução de Conflitos e Inconsistência de Dados Sanitários no Reenvio Offline do Atendimento

* **Trecho Atacado:**

  * **Arquivo:** `1-adrs/0005-sincronizar-atendimentos-offline-de-forma-idempotente.md`

  * **Seção:** *Decisão* e *Consequências*

  * **Arquivo auxiliar:** `3-spike/exemplo.py`

* **Argumento:**
  O ADR 0005 e a prova de conceito (`exemplo.py`) demonstram com sucesso como evitar a **duplicação** de registros em caso de reenvio de uma mesma transação (utilizando chaves únicas e checagem de idempotência). No entanto, o design **oculta e ignora o problema real da sincronização offline: conflitos de dados cadastrais/clínicos modificados concorrentemente**.

  No mundo real de uma UBS/UPA, durante o período de queda de internet, o cadastro de um paciente ou o estado de uma fila pode sofrer alterações locais enquanto a central também é atualizada por outra unidade via canal alternativo (ex.: dados atualizados no cartão SUS ou transferência registrada por telefone). Ao limitar o mecanismo de sync a um mero "if chave processada do-nothing", a arquitetura não define o comportamento quando o estado do banco central entra em **conflito** com os atributos enviados pela unidade (ex.: paciente alterou o nome, médico reclassificou a gravidade da triagem enquanto a unidade estava offline). O sistema simplesmente sobrescreverá dados sem rastreio de divergências ou descartará atualizações clínicas válidas.

* **O que teria sido feito no lugar:**
  Teríamos formalizado no ADR 0005 uma regra clara de **Políticas de Resolução de Conflitos** (ex.: *Last-Write-Wins* baseado em relógio lógico/vector clock, ou flagging de registros conflitantes em uma fila de conciliação manual para validação médica/administrativa). O spike deveria ter demonstrado não apenas a duplicidade de chave, mas a fusão segura de estados (*state merging*) de um atendimento offline com o histórico do prontuário central.

## Objeção 5: Risco Implicito na Validação de Transações de Farmácia por Interações Inter-Módulos em Chamadas Síncronas do Monolito

* **Trecho Atacado:**

  * **Arquivo:** `2-arquitetura/c4-componentes.md`

  * **Seção:** *Componente Farmácia e Estoque*

  * **Arquivo auxiliar:** `2-arquitetura/mapa-restricoes-decisoes.md` (Linha "Dispensação exige receita vinculada ao prontuário")

* **Argumento:**
  A tabela do mapa de decisões exige que o módulo de Farmácia valide a existência da receita médica através da interface do módulo de Prontuário, sem acessar a base de dados de forma direta (respeitando a propriedade lógica dos dados). Na arquitetura proposta (C4 Componentes), a Farmácia faz uma chamada **síncrona em memória/módulo** para o Prontuário durante o ato de dispensação de medicamentos.

  Essa abordagem ignora o cenário frequente em que o atendimento médico/receita foi gerado em uma UBS enquanto ela operava em **modo offline** (ADR 0005) e a sincronização central ainda não ocorreu (ex.: a UBS ainda está sem internet, mas o paciente já se deslocou com a receita física até a farmácia central para retirar o remédio). Como a receita médica ainda não chegou ao banco central por pendência do sync offline, a validação síncrona exigida no mapa de decisões **falhará na farmácia central**, impedindo a dispensação do medicamento ao paciente, mesmo este portando a prescrição física carimbada.

* **O que teria sido feito no lugar:**
  Teríamos previsto no módulo de Farmácia uma camada de validação contingencial que permitisse o registro da dispensação por "confiança com reconciliação posterior" (*optimistic processing*), gravando o número da receita física e o CRM do médico prescritor. A validação transacional com o Prontuário ocorreria de forma assíncrona assim que os dados da UBS fossem sincronizados no servidor central, auditando eventuais inconsistências sem negar o atendimento de medicação urgente ao cidadão.

## Objeção 6: Complexidade Desnecessária e Fragilidade Técnica no Estrangulamento do Sistema Legado de Regulação sem Camada de Sincronização Passiva

* **Trecho Atacado:**

  * **Arquivo:** `1-adrs/0003-integrar-legado-e-terceiros-por-adaptadores.md`

  * **Seção:** *Decisão*

  * **Arquivo auxiliar:** `2-arquitetura/respostas-perguntas.md` (Pergunta 2 e Pergunta 5)

* **Argumento:**
  A decisão **ADR 0003** e a Resposta 2 defendem a transição do sistema de Regulação antigo para o novo através do padrão *Strangler Fig* (Estrangulamento), afirmando rigorosamente que "não haverá dual-write de reservas" e que o legado será a única autoridade até que a capacidade seja 100% migrada.

  Portanto, o argumento falha ao não prever como o novo sistema tomará conhecimento do **estado global atualizado dos leitos** se ele não consulta o banco do legado de forma leitura-passiva nem recebe replicações. Se uma leito for reservado por um usuário utilizando diretamente a interface do sistema legado (que continuará ativo durante o período de 2 anos por equipes não migradas), e o novo sistema tentar consultar a disponibilidade de leitos para exibição aos médicos nas UPAs via API do novo sistema, as telas do novo sistema mostrarão dados desatualizados a menos que **todas as consultas** passem como proxy direto para o legado, gerando uma latência enorme e dependência total da disponibilidade do sistema antigo (que é instável e lento).

* **O que teria sido feito no lugar:**
  Em vez de bloquear completamente qualquer replicação de dados e confiar 100% no roteamento síncrono por chamadas no Adaptador, teríamos implementado uma **sincronização passiva de leitura (CDC - Change Data Capture ou Polling na base do legado)** para manter uma visão de leitura (*read model*) atualizada no banco novo. As escritas (confirmação da reserva) continuariam direcionadas unicamente à autoridade vigente (legado no início), mas a consulta/visualização de leitos seria instantânea e resiliente na aplicação nova.

## Objeção 7: Desconsideração do Custo de Observabilidade e Monitoramento de Tarefas Assíncronas Retidas no Contexto de Equipe Reduzida

* **Trecho Atacado:**

  * **Arquivo:** `1-adrs/0006-notificar-vigilancia-por-fila-persistente.md`

  * **Seção:** *Consequências*

  * **Arquivo auxiliar:** `2-arquitetura/c4-conteineres.md` (Serviço de Fila Persistente e Função de Integração)

* **Argumento:**
  O ADR 0006 impõe a necessidade de "monitorar o atraso da fila (*lag*) para que tarefas pendentes não permaneçam sem tratamento" e gerenciar alertas para falhas na notificação compulsória à Vigilância Epidemiológica no prazo legal de 24 horas.

  Ao adicionar um ecossistema composto por **Fila Persistente Gerenciada + FaaS/Function Gerenciada + Banco de Dados Central + Alertas Customizados**, o grupo introduziu **quatro pontos distintos de observabilidade e falha**. Para um time de apenas 6 desenvolvedores e **sem equipe dedicada de operação (Ops)**, o custo cognitivo e operacional de configurar Dead Letter Queues (DLQ), métricas de vazão de FaaS, alarmes de retenção de fila e rastreamento distribuído (*distributed tracing* entre o monolito, a fila e a função) consumirá um tempo precioso de engenharia que deveria estar focado na entrega do Prontuário para as 3 UBSs nos 4 meses do contrato inicial.

* **O que teria sido feito no lugar:**
  Teríamos simplificado o mecanismo assíncrono mantendo a tabela de "Tarefas de Integração Pendentes" no próprio banco de dados relacional (padrão *Transactional Outbox*). Um agendador interno (*cron/background job*) na própria aplicação processaria os registros pendentes. Dessa forma, a observabilidade, a auditoria e as métricas seriam centralizadas na mesma ferramenta de log/métrica do Monolito Modular, reduzindo a complexidade de infraestrutura a zero e mantendo o foco total da pequena equipe nas regras de negócio.

## Resumo do Impacto das Objeções no Envelope A

| Objeção | Componente/Decisão Afetada | Risco Principal Ignorado | Impacto Direto no Envelope A | 
 | ----- | ----- | ----- | ----- | 
| **1. Lock no BD Central em Picos** | ADR 0002 / BD Central | Contenção de escrita e queda das UPAs | Falha no atendimento emergencial durante campanhas | 
| **2. Retenção de 20 anos sem Archiving** | ADR 0002 / Prontuário | Explosão de custos de nuvem e lentidão | Estouro do caixa de 6 meses por infraestrutura | 
| **3. FaaS para Filas de Longo Acúmulo** | ADR 0004 e 0006 / FaaS | Custo elevado e estour de cotas/cold start | Sobrecarga operacional no time sem Ops | 
| **4. Omissão de Resolução de Conflitos** | ADR 0005 / Sync Offline | Corrupção/perda de dados sanitários | Inconsistência de cadastros entre UBS e Central | 
| **5. Bloqueio na Dispensação de Remédios** | C4 Componentes / Farmácia | Negativa de medicação com receita offline | Prejuízo direto ao atendimento do cidadão | 
| **6. Visão de Leitos sem Replicação** | ADR 0003 / Legado Regulação | Telas de regulação com dados desatualizados | Erro médico/operacional na escolha de leitos | 
| **7. Multiplicidade de Pontos de Ops** | ADR 0006 / Fila + FaaS | Complexidade de monitoramento distribuído | Desvio do time de dev do prazo de 4 meses | 
