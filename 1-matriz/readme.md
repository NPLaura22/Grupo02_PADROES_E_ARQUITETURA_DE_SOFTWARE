# Entrega 1: Matriz de Estilos Aplicada — Caso Saúde (Envelope E)

Este arquivo contém a documentação da **Entrega 1** do projeto de Arquitetura de Software para a Rede Municipal de Atenção à Saúde. A solução foi formulada para atender às restrições do **Envelope E** (Operação sob fiscalização de órgão regulador).

---

## Conteúdo do Diretório

* [`matriz.md`](./matriz.md): Matriz detalhada de avaliação dos 12 estilos arquiteturais do livro-texto, contendo o alinhamento com as restrições do Envelope E, justificativas baseadas em seções do livro e o impacto nas qualidades do sistema.

---

## Visão Geral do Cenário e Contexto (Envelope E)

* **Caso:** Rede Municipal de Atenção à Saúde (Grupo 02).
* **Envelope:** **E — Operação sob fiscalização de órgão regulador.**
* **Infraestrutura e Equipe:** Nuvem pública com exigência de trilha de auditoria completa; equipe de 15 desenvolvedores e 1 responsável por conformidade.
* **Estrutura Operacional:**
  * 70 Unidades Básicas de Saúde (UBS) com conectividade instável.
  * 5 Unidades de Pronto Atendimento (UPAs) e 1 Hospital Municipal (400 leitos).
  * Campanhas sazonais de vacinação de grande escala.
  * Integração com sistemas federais e convivência com 1 sistema legado de regulação (manutenção por 2 anos).
* **Exigência Dominante:** Reconstrução histórica total de operações fiscalizadas (prontuário com guarda obrigatória de 20 anos, dispensação de medicamentos e notificações compulsórias em até 24h) conciliada com o cumprimento dos direitos do titular segundo a LGPD (direito ao esquecimento / expurgo ou anonimização segura).

---

## Resumo da Síntese Arquitetural Adotada

A arquitetura global do sistema foi desenhada em camadas estratégicas para balancear a simplicidade de operação para o time de 15 desenvolvedores com a altíssima exigência de auditoria e conformidade regulatória:

1. **Núcleo do Sistema (Core):**
   * **Monolito Modular + Arquitetura Hexagonal (Portas e Adaptadores):** Garante limites rígidos entre domínios (Prontuário, Regulação, Farmácia, Atendimento) e isola o sistema contra dependências de infraestrutura, nuvem, APIs federais e o sistema legado de regulação.
2. **Processamento Assíncrono e Resiliência:**
   * **Arquitetura Orientada a Eventos (EDA):** Ingestão contínua de audit logs, notificações compulsórias e comunicação com UBSs em conexões instáveis.
3. **Estilos Especializados para Subdomínios Críticos:**
   * **CQRS:** Leitura analítica separada da escrita em tempo real no Módulo de Regulação e Painéis do Órgão Regulador.
   * **Event Sourcing:** Histórico imutável de auditoria com **destruição criptográfica de chaves** para atender ao expurgo exigido pela LGPD sem quebrar a integridade do log.
   * **Pipes and Filters:** Pipeline de desidentificação, validação e transmissão de notificações epidemiológicas.
   * **Serverless:** Rotinas intermitentes e assíncronas de anonimização e relatórios regulatórios sob demanda.
