# Entrega 3 — Grupo 5 · Ônibus · Envelope E

**Decisão provada:** [ADR 05 — Segregação Estrutural entre Banco Transacional Central e Store Imutável de Auditoria](../2-arquitetura/documento_de_arquitetura.md#adr-05-decisão-mais-arriscada--segregação-estrutural-entre-banco-transacional-central-e-store-imutável-de-auditoria). O documento existente descreve Saúde; esta spike adapta seu fluxo de contêineres (§1.2) para bilhetagem e repasse às operadoras, conforme o caso Ônibus/E do grupo 5. O diagrama abaixo explicita o recorte executado; a entrega 2 ainda precisa dessa adaptação de domínio.

```mermaid
flowchart LR
    N["Núcleo modular: bilhetagem"] -->|"SQL / transação: viagem + outbox"| C[(Banco central)]
    C -->|"Leitura da outbox / chamada"| B["Relay / barramento simulado"]
    B -->|"Evento / reentrega até ACK"| A[Serviço de auditoria]
    A -->|"Append-only / chamada"| S[(Store de auditoria)]
    S -->|"Leitura / replay"| R[Repasse por operadora]
```

**O que prova.** Separar os bancos permite reconstruir o repasse mesmo após apagar o estado operacional. Para fechar o risco do ADR 05, a outbox grava a viagem e a intenção de publicação na mesma transação; o consumidor deduplica pelo ID. O programa verifica rollback, rede indisponível, perda de confirmação após gravar na auditoria, reinício, reentrega, conflito de conteúdo e bloqueio de alteração/exclusão. Três viagens com duas versões de tarifa produzem sempre R$ 10,50 para A e R$ 5,50 para B, usando valores históricos em centavos. As verificações internas falham se os resultados divergirem.

**Como rodar**, dentro de `3-spike/`, com Python 3.12 e somente sua biblioteca padrão:

```sh
python3 exemplo.py
python3 exemplo.py > /tmp/saida-spike.txt
diff -u saida-esperada.txt /tmp/saida-spike.txt
```

SQLite em arquivos temporários simula os dois bancos; chamadas locais simulam o barramento e suas falhas. Os arquivos são removidos ao terminar. Não há dependências ou serviços a instalar.

**Se a decisão estivesse errada**, uma viagem confirmada poderia não chegar à auditoria ou uma reentrega duplicaria o repasse, impedindo a reconstrução exigida pela fiscalização do envelope E. A prova cobre a recuperação das falhas simuladas, pressupondo armazenamento preservado e retorno da comunicação. Não mede escala/latência nem implementa proteção contra administrador do banco. Usa apenas dados financeiros fictícios, sem identidade de passageiro; o expurgo de dados pessoais e o KMS do ADR 02 ficam fora desta prova de uma única decisão.
