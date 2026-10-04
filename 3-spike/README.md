# Entrega 3 — Grupo 02 · Saúde · Envelope E

**Decisão provada:** [ADR 05 — Segregação Estrutural entre Banco Transacional Central e Store Imutável de Auditoria](../2-arquitetura/documento_de_arquitetura.md#adr-05-decisão-mais-arriscada--segregação-estrutural-entre-banco-transacional-central-e-store-imutável-de-auditoria). A spike executa o fluxo de contêineres do documento de arquitetura (§1.2) para atendimentos das UPAs e UBSs: núcleo, banco central, barramento, serviço de auditoria e store imutável. O diagrama abaixo explicita o recorte executado.

```mermaid
flowchart LR
    N["Núcleo modular: atendimento"] -->|"SQL / transação: atendimento + outbox"| C[(Banco central)]
    C -->|"Leitura da outbox / chamada"| B["Relay / barramento simulado"]
    B -->|"Evento / reentrega até ACK"| A[Serviço de auditoria]
    A -->|"Append-only / chamada"| S[(Store de auditoria)]
    S -->|"Leitura / replay"| R[Linha do tempo por paciente]
```

**O que prova.** Separar os bancos permite reconstruir o histórico por paciente mesmo após apagar o estado operacional. Para fechar o risco do ADR 05 (perder ou duplicar evento entre os dois bancos), a outbox grava o atendimento e a intenção de publicação na mesma transação; o consumidor deduplica pelo ID. O programa verifica rollback, rede indisponível, perda de confirmação após gravar na auditoria, reinício, reentrega, conflito de conteúdo e bloqueio de alteração/exclusão. Três atendimentos (dois do paciente p-001 e um do p-002) produzem sempre a mesma linha do tempo, reconstruída somente a partir da auditoria. As verificações internas falham se os resultados divergirem.

**Como rodar**, dentro de `3-spike/`, com Python 3.12 e somente sua biblioteca padrão:

```sh
python3 exemplo.py
python3 exemplo.py > /tmp/saida-spike.txt
diff -u saida-esperada.txt /tmp/saida-spike.txt
```

SQLite em arquivos temporários simula os dois bancos; chamadas locais simulam o barramento e suas falhas. Os arquivos são removidos ao terminar. Não há dependências ou serviços a instalar.

**Se a decisão estivesse errada**, um atendimento confirmado poderia não chegar à auditoria ou uma reentrega duplicaria o evento, impedindo a reconstrução exigida pela fiscalização do envelope E. A prova cobre a recuperação das falhas simuladas, pressupondo armazenamento preservado e retorno da comunicação. Não mede escala/latência nem implementa proteção contra administrador do banco. Usa apenas dados fictícios, com pseudônimos no lugar de identidade do paciente; o expurgo de dados pessoais e o KMS do ADR 02 ficam fora desta prova de uma única decisão.
