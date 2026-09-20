# Entrega 1: Matriz de Estilos Aplicada

## 1. Identificação do Cenário e Contexto
* **Caso:** Grupo 02 — Saúde: Rede Municipal de Atenção à Saúde.
* **Envelope:** E — Operação sob fiscalização de órgão regulador.
* **Infraestrutura e Equipe:** Nuvem pública com exigência de trilha de auditoria completa; equipe de 15 desenvolvedores e 1 responsável por conformidade.
* **Estrutura Operacional:** 70 Unidades Básicas de Saúde (UBS) com conectividade instável, 5 Unidades de Pronto Atendimento (UPAs), 1 Hospital Municipal (400 leitos), campanhas sazonais de vacinação, integração com sistemas federais e 1 sistema legado de regulação (que deve ser mantido por 2 anos).
* **Exigência Dominante:** Reconstrução histórica total de operações fiscalizadas (prontuário com guarda obrigatória de 20 anos, dispensação de medicamentos e notificações compulsórias em até 24h) conciliada com o cumprimento dos direitos do titular segundo a LGPD (direito ao esquecimento / expurgo ou anonimização segura).

---

## 2. Matriz de Avaliação dos Doze Estilos Arquiteturais

*(Critérios baseados na Seção 2.3 do livro: desempenho, escalabilidade, disponibilidade, modificabilidade, testabilidade, implantabilidade, segurança e custo).*

| Estilo Arquitetural | Serve para o caso e envelope? | Subdomínio de Aplicação | Por quê? (Até 3 frases, citando seções do livro) | Qualidade que Melhora | Qualidade que Piora |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Monolito em Camadas** | **Não** | Nenhum (ou no máximo aplicação administrativa isolada) | A unidade única não suporta as cargas distintas e acopla a lógica de negócios com regras de auditoria, dificultando a isolação de trilhas imutáveis e o expurgo granular da LGPD em tabelas compartilhadas. As Seções 5.6 (*Quando evitar*) e 5.7 (*Custo real*) destacam a perda de fronteiras em domínios grandes e os riscos de manutenção em longo prazo. | Custo operacional inicial | Escalabilidade e Modificabilidade |
| **2. Monolito Modular** | **Sim** | Estrutura central (Prontuário, Farmácia, Agendamento e Regulação) | Estabelece fronteiras internas verificáveis entre os domínios sem impor a complexidade de distribuição inicial para uma equipe de 15 desenvolvedores. As Seções 6.5 (*Quando adotar*) e 6.7 (*Custo real*) sustentam o uso de módulos com dependências verificadas, testes em processo e transações locais. | Modificabilidade e Testabilidade | Implantabilidade |
| **3. Arquitetura Hexagonal** | **Sim** | Regulação de leitos, Prontuário, Farmácia e Integrações externas/legado | Isola o núcleo de regras clínicas e de conformidade contra dependências de banco, nuvem e APIs federais/legadas, permitindo testar a lógica sem infraestrutura externa. As Seções 7.5 (*Quando adotar*) e 7.7 (*Custo real*) justificam o isolamento por portas e adaptadores para viabilizar substituição gradual do legado e auditorias. | Testabilidade e Modificabilidade | Custo inicial (complexidade técnica) |
| **4. Microkernel (Núcleo e Plugins)** | **Não** | Nenhum inicialmente (ou pontualmente em Vigilância para regras de notificação) | O ecossistema exige regras centralizadas e estritas de conformidade, não havendo um ecossistema de extensões de terceiros que justifique o custo de versionamento de plugins. As Seções 8.5 (*Quando adotar*) e 8.6 (*Quando evitar*) alertam que poucas variações conhecidas acrescentam complexidade de manutenção sem benefício proporcional. | Modificabilidade (extensibilidade) | Custo operacional e Simplicidade |
| **5. Microsserviços** | **Em parte** | Agendamento de campanhas e Vigilância epidemiológica | A extração seletiva isola os picos de carga (ex: agendamento) e facilita a aplicação de políticas de expurgo da LGPD por limite de contexto. As Seções 9.5 (*Quando adotar*), 9.6 (*Quando evitar*) e 9.7 (*Custo real*) desaconselham a decomposição total para o time de 15 devs devido ao overhead de observabilidade, consistência distribuída e governança. | Escalabilidade e Segregação da LGPD | Custo operacional e Consistência |
| **6. SOA e Barramento de Serviços (ESB)** | **Em parte** | Integração com sistemas federais e sistema legado de regulação | Serve estritamente como ponto de tradução na fronteira heterogênea para manter o legado ativo na transição de dois anos. Conforme as Seções 10.5 (*Quando adotar*), 10.6 (*Quando evitar*) e 10.7 (*Custo real*), seu uso deve ser restrito ao perímetro, pois o ESB é um ponto único de falha e gargalo de desempenho. | Segurança (integração) | Disponibilidade e Complexidade |
| **7. Arquitetura Orientada a Eventos (EDA)** | **Sim** | Vigilância epidemiológica, Notificações e Trilha de auditoria de acessos | Desacopla a ingestão contínua de auditoria e notificações dos fluxos clínicos, absorvendo indisponibilidades temporárias das UBSs ou APIs externas por meio de filas. As Seções 11.5 (*Quando adotar*), 11.6 (*Quando evitar*) e 11.7 (*Custo real*) sustentam o desacoplamento, mas descartam seu uso em decisões síncronas de reserva de leitos. | Disponibilidade e Escalabilidade | Testabilidade e Consistência imediata |
| **8. Serverless** | **Em parte** | Processamento sob demanda (Expurgo LGPD, relatórios e automações) | Executa tarefas intermitentes sem custo de servidores ociosos, sendo ideal para rotinas isoladas de anonimização e expurgo em nuvem. As Seções 12.5 (*Quando adotar*), 12.6 (*Quando evitar*) e 12.7 (*Custo real*) desaconselham o uso em fluxos clínicos contínuos devido à latência de *cold start* e à dependência de provedor. | Escalabilidade e Custo variável | Testabilidade e Observabilidade |
| **9. Arquitetura Celular (Cell-Based)** | **Não** | Nenhum (não aplicável como topologia global municipal) | Embora contivesse o raio de impacto de falhas entre UPAs, a coordenação da rede municipal exige prontuário compartilhado e consultas globais incompatíveis com o isolamento em células autônomas. As Seções 13.5 (*Quando adotar*), 13.6 (*Quando evitar*) e 13.7 (*Custo real*) demonstram que a replicação eleva drasticamente o custo para o time de 15 devs sem um cenário multi-inquilino. | Disponibilidade (isolamento de falha) | Custo operacional e Governança |
| **10. CQRS** | **Em parte** | Regulação de leitos, Prontuário e Painéis de fiscalização | Separa a escrita transacional de alta densidade das consultas analíticas pesadas e relatórios do órgão regulador. As Seções 14.5 (*Quando adotar*), 14.6 (*Quando evitar*) e 14.7 (*Custo real*) recomendam a adoção local para evitar degradação de performance do atendimento em tempo real, exigindo controle do atraso de projeções. | Desempenho de leitura e Escalabilidade | Custo operacional e Complexidade |
| **11. Event Sourcing** | **Em parte** | Trilha de auditoria de dispensação, notificações e histórico de alterações | Armazena a sequência imutável de eventos garantindo a reconstrução histórica exigida pela fiscalização. Para cumprir o direito ao esquecimento da LGPD sobre a base imutável, adota-se a destruição criptográfica de chaves de decodificação do paciente ou o uso de ponteiros externos, conforme orientado nas Seções 15.5 (*Quando adotar*), 15.6 (*Quando evitar*) e 15.7 (*Custo real*). | Segurança e Rastreabilidade | Custo operacional e Complexidade |
| **12. Pipes and Filters (Dutos e Filtros)** | **Sim** | Pipeline de anonimização, validação e transmissão epidemiológica | Encadeia etapas independentes para desidentificar, validar, enriquecer e transmitir lotes de notificações sanitárias. As Seções 16.5 (*Quando adotar*), 16.6 (*Quando evitar*) e 16.7 (*Custo real*) exigem filtros idempotentes e observabilidade por etapa, descartando o uso em fluxos clínicos conversacionais ou reserva de leitos devido à latência em série. | Modificabilidade e Testabilidade | Custo operacional e Latência |

---

## 3. Estilos Descartados como Arquitetura Global (Análise Detalhada)

Para atender ao **Envelope E** mantendo o foco no rigor fiscalatório e no cumprimento da LGPD sem sobrecarregar a equipe de 15 desenvolvedores, os seguintes estilos foram explicitamente descartados como estrutura principal:

1. **Monolito em Camadas**
   * **Motivo do Descarte:** A falta de isolamento estrito entre a camada de apresentação, regras de negócio e persistência dificulta garantir que 100% das operações passariam obrigatoriamente pelas trilhas de auditoria (Seção 2.7, Tabela 2.2). Além disso, a LGPD exige a revogação e o expurgo/anonimização granular de dados sensíveis a pedido do cidadão (direito ao esquecimento). Em um monolito em camadas tradicional, com banco relacional compartilhado e acoplado, realizar essa higienização sem afetar a integridade relacional é propenso a falhas de conformidade (Seções 2.5, 5.6 e 5.7).
2. **Arquitetura Celular (Cell-Based)**
   * **Motivo do Descarte:** A arquitetura celular divide o sistema em instâncias independentes para isolar falhas. No entanto, a gestão de saúde pública de um município requer consultas unificadas de leitos, regulação em tempo real e histórico global do paciente entre UBSs e UPAs. Multiplicar e replicar infraestruturas completas aumentaria drasticamente o custo e a complexidade de operação e auditoria para a equipe (Seções 13.5, 13.6 e 13.7).

---

## 4. Síntese Arquitetural
A solução adota como núcleo inicial um **Monolito Modular com Arquitetura Hexagonal**, garantindo transações locais, isolamento do sistema legado de 2 anos e testabilidade sem impor o custo de uma distribuição prematura. 

A **Arquitetura Orientada a Eventos (EDA)** atua na comunicação assíncrona, ingestão de auditoria e integração das UBSs. Para cenários pontuais e específicos, aplicam-se:
* **CQRS** na regulação de leitos e painéis de fiscalização;
* **Event Sourcing** na preservação do histórico de auditoria (com destruição criptográfica de chaves para expurgo LGPD);
* **Pipes and Filters** no pipeline de higienização e envio de notificações sanitárias;
* **Serverless** para tarefas intermitentes de expurgo e consolidação de relatórios.

---

## Referências
* ABREU, Douglas Henrique Siqueira. *Estilos Arquiteturais de Software: guia de consulta*. 2026. Capítulos 2 a 16 e Apêndice A.
* ABREU, Douglas Henrique Siqueira. *Um problema, cinco realidades: projeto de arquitetura sob restrição*. PUC-Campinas, 2026. Caso 2: Saúde e Envelope E.
