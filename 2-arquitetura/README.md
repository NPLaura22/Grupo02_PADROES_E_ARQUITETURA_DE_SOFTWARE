# Entrega 2: Documentação de Arquitetura de Software — Caso Saúde (Envelope E)

Este arquivo contém a documentação técnica completa da **Entrega 2** para a Rede Municipal de Atenção à Saúde, contemplando as decisões de design, modelo de dados, resiliência e conformidade regulatória segundo os requisitos do **Envelope E**.

## Conteúdo do Arquivo

* [`documento_de_arquitetura.md`](./documento_de_arquitetura.md): Documentação arquitetural completa incluindo diagramas C4 (Contexto, Contêineres e Componentes), mapa de rastreabilidade de restrições, decisões arquiteturais registradas (ADRs) e respostas aos questionamentos do cenário municipal.

---

## Estrutura do Documento Arquitetural

### 1. Diagramas C4 (Mermaid)
A arquitetura foi modelada utilizando a convenção **C4 Model** para prover visibilidade em diferentes níveis de abstração:
* **Nível 1 (Contexto):** Define os atores humanos (Cidadão, Profissional de Saúde e Auditor) e a integração com sistemas externos (*Sistema Legado de Regulação* e *Sistemas Federais e-SUS/RNDS*).
* **Nível 2 (Contêineres):** Mapeia a topologia do ecossistema na nuvem pública (Portal Web SPA, Ingress Gateway, Núcleo Monolítico Modular, Barramento de Eventos Kafka, Workers dedicados e triplo armazenamento: *OLTP*, *Append-Only Audit Store* e *KMS*).
* **Nível 3 (Componentes):** Detalha a implementação interna do Núcleo Modular com **Arquitetura Hexagonal (Portas e Adaptadores)**, demonstrando o desacoplamento de domínios (*Prontuário*, *Farmácia*, *Regulação*) e adaptadores para o legado e criptografia LGPD.

### 2. Mapa de Restrições e Decisões
Tabela de alinhamento estratégico que vincula diretamente as demandas operacionais do Envelope E às soluções arquiteturais adotadas:
* **Guarda de 20 Anos vs. LGPD:** Solucionado com *Event Sourcing* segregado + Criptografia Envelope e *Crypto-Shredding*.
* **Instabilidade de Redes (70 UBSs):** Solucionado com estratégia *Offline-First* e sincronização *Store and Forward*.
* **Manutenção do Legado (2 Anos):** Solucionado com o padrão *Adapter* / *Strangler Fig* (Estrangulamento).
* **Time Reduzido (15 devs):** Solucionado com composição híbrida focada em Monolito Modular.

### 3. Registro de Decisões Arquiteturais (ADRs)
* **ADR 01 (Estrutura Geral):** Composição Híbrida com Núcleo Monolítico Modular e Fronteiras Explícitas.
* **ADR 02 (Gestão de Dados):** Criptografia Envelope com Destruição de Chaves para LGPD vs. Auditoria Imutável.
* **ADR 03 (Integração com Terceiros):** Padrão Adapter e Ingestão Assíncrona via *Pipes & Filters*.
* **ADR 04 (Operação):** Infraestrutura Cloud Híbrida com Buffer Local em UBSs.
* **ADR 05 (Análise de Risco):** Segregação Estrutural entre Banco Transacional Central e Store Imutável de Auditoria.

### 4. Respostas às Perguntas Obrigatórias do Caso
Detalhamento técnico fundamentado nos diagramas e ADRs para os 5 cenários críticos do município:
1. Operação contínua de emergência nas UPAs/UBSs sem conexão de rede (*Offline-First*).
2. Concorrência e prevenção de *double-booking* em leitos disputados por unidades diferentes (*Pessimistic Locking* + *Adapter*).
3. Rastreabilidade individual de acessos aos prontuários e conciliação legal de guarda de 20 anos com expurgo LGPD.
4. Garantia de entrega das Notificações Compulsórias epidemiológicas em até 24h (*Pipes & Filters* + *Exponential Backoff*).
5. Estratégia de desativação progressiva e sem parada do Sistema Legado de Regulação ao longo de 24 meses.

---

> Para visualizar o documento na íntegra com os diagramas renderizados em Mermaid, abra o arquivo [`documento_de_arquitetura.md`](./documento_de_arquitetura.md).
