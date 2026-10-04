"""Grupo 02 — Saúde / Envelope E: prova do ADR 05 (segregação assíncrona).

O banco transacional central e o store imutável de auditoria são bancos
separados. O atendimento nunca espera a auditoria: o evento sai por uma
outbox e chega ao store com entrega "ao menos uma vez" + consumidor idempotente.

SQLite simula os dois bancos; a função entregar() simula o barramento (Kafka).
Dados fixos e sem relógio, para permitir replay exato.
"""

import json
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory


class FalhaSimulada(Exception):
    """Interrupção controlada no cenário de teste."""


def abrir_bancos(pasta):
    central = sqlite3.connect(pasta / "central.db")
    auditoria = sqlite3.connect(pasta / "auditoria.db")
    central.executescript("""
        CREATE TABLE IF NOT EXISTS atendimentos (
            id TEXT PRIMARY KEY, unidade TEXT NOT NULL,
            paciente TEXT NOT NULL, acao TEXT NOT NULL, data TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS outbox (
            id TEXT PRIMARY KEY, evento TEXT NOT NULL,
            entregue INTEGER NOT NULL DEFAULT 0
        );
    """)
    auditoria.executescript("""
        CREATE TABLE IF NOT EXISTS eventos (
            id TEXT PRIMARY KEY, evento TEXT NOT NULL
        );
        CREATE TRIGGER IF NOT EXISTS impedir_update
        BEFORE UPDATE ON eventos BEGIN
            SELECT RAISE(ABORT, 'auditoria append-only');
        END;
        CREATE TRIGGER IF NOT EXISTS impedir_delete
        BEFORE DELETE ON eventos BEGIN
            SELECT RAISE(ABORT, 'auditoria append-only');
        END;
    """)
    return central, auditoria


def registrar(central, identificador, unidade, paciente, acao, data,
              falhar=False):
    """Núcleo: atendimento e intenção de publicar na MESMA transação."""
    evento = json.dumps(dict(id=identificador, unidade=unidade,
                             paciente=paciente, acao=acao, data=data),
                        sort_keys=True)
    with central:
        central.execute("INSERT INTO atendimentos VALUES (?, ?, ?, ?, ?)",
                        (identificador, unidade, paciente, acao, data))
        if falhar:
            raise FalhaSimulada("falha antes de gravar a outbox")
        central.execute("INSERT INTO outbox (id, evento) VALUES (?, ?)",
                        (identificador, evento))


def consumir(auditoria, identificador, evento):
    """Serviço de auditoria: deduplicação persistida junto com o evento."""
    with auditoria:
        existente = auditoria.execute(
            "SELECT evento FROM eventos WHERE id = ?", (identificador,)
        ).fetchone()
        if existente:
            if existente[0] != evento:
                raise ValueError("Mesmo ID com conteúdo diferente")
            return False
        auditoria.execute("INSERT INTO eventos VALUES (?, ?)",
                          (identificador, evento))
    return True


def entregar(central, auditoria, rede=True, perder_ack=False):
    """Relay/barramento mínimo: entrega ao menos uma vez, ACK após o commit."""
    if not rede:
        raise FalhaSimulada("barramento indisponível")
    novos = repetidos = 0
    pendentes = central.execute(
        "SELECT id, evento FROM outbox WHERE entregue = 0 ORDER BY id"
    ).fetchall()
    for identificador, evento in pendentes:
        if consumir(auditoria, identificador, evento):
            novos += 1
        else:
            repetidos += 1
        if perder_ack:
            raise FalhaSimulada("auditoria gravou, mas o ACK se perdeu")
        with central:
            central.execute("UPDATE outbox SET entregue = 1 WHERE id = ?",
                            (identificador,))
    return novos, repetidos


def quantidade(banco, tabela):
    # Tabelas fornecidas somente pelo próprio programa.
    return banco.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]


def linha_do_tempo(eventos):
    """Visão do auditor: histórico por paciente, na ordem dos eventos."""
    historico = {}
    for conteudo in eventos:
        e = json.loads(conteudo)
        historico.setdefault(e["paciente"], []).append(
            f'{e["data"]} {e["unidade"]} {e["acao"]}')
    return historico


def executar(pasta):
    central, auditoria = abrir_bancos(pasta)
    try:
        registrar(central, "a00", "UPA-1", "p-001", "triagem", "2026-10-01",
                  falhar=True)
    except FalhaSimulada:
        pass
    assert quantidade(central, "atendimentos") == quantidade(central, "outbox") == 0
    print("1. Falha na transação: atendimento e outbox revertidos juntos.")

    registrar(central, "a01", "UPA-1", "p-001", "triagem", "2026-10-01")
    registrar(central, "a02", "UPA-1", "p-002", "triagem", "2026-10-02")
    registrar(central, "a03", "UBS-12", "p-001", "prescricao", "2026-10-03")
    try:
        entregar(central, auditoria, rede=False)
    except FalhaSimulada:
        pass
    assert quantidade(central, "atendimentos") == quantidade(central, "outbox") == 3
    assert quantidade(auditoria, "eventos") == 0
    print("2. Rede fora: 3 atendimentos confirmados, 3 eventos pendentes, 0 auditados.")

    try:
        entregar(central, auditoria, perder_ack=True)
    except FalhaSimulada:
        pass
    assert quantidade(auditoria, "eventos") == 1
    assert central.execute("SELECT SUM(entregue) FROM outbox").fetchone()[0] == 0
    print("3. ACK perdido: 1 evento auditado; entrega continua pendente.")

    central.close()
    auditoria.close()
    central, auditoria = abrir_bancos(pasta)
    assert entregar(central, auditoria) == (2, 1)
    assert entregar(central, auditoria) == (0, 0)
    assert quantidade(auditoria, "eventos") == 3
    assert central.execute("SELECT SUM(entregue) FROM outbox").fetchone()[0] == 3
    print("4. Após reinício: 2 novos, 1 repetido ignorado; 3 eventos únicos.")

    original = auditoria.execute(
        "SELECT evento FROM eventos WHERE id = 'a01'").fetchone()[0]
    try:
        consumir(auditoria, "a01", original.replace("triagem", "alterada"))
    except ValueError:
        print("5. Mesmo ID com conteúdo diferente: rejeitado.")
    else:
        raise AssertionError("Conflito de conteúdo deveria ser rejeitado")

    for comando in ("UPDATE eventos SET evento = '{}' WHERE id = 'a01'",
                    "DELETE FROM eventos WHERE id = 'a01'"):
        try:
            with auditoria:
                auditoria.execute(comando)
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("Mutação da auditoria deveria ser rejeitada")
    print("6. Alteração e exclusão de eventos: bloqueadas.")

    esperado = linha_do_tempo(
        e for (e,) in central.execute(
            "SELECT evento FROM outbox ORDER BY id"))
    with central:
        central.execute("DELETE FROM atendimentos")
        central.execute("DELETE FROM outbox")
    assert quantidade(central, "atendimentos") == 0
    reconstruido = linha_do_tempo(
        e for (e,) in auditoria.execute(
            "SELECT evento FROM eventos ORDER BY id"))
    assert reconstruido == esperado
    assert (len(reconstruido["p-001"]), len(reconstruido["p-002"])) == (2, 1)
    assert reconstruido == linha_do_tempo(
        e for (e,) in auditoria.execute(
            "SELECT evento FROM eventos ORDER BY id"))
    print("7. Replay sem estado operacional: p-001 = 2 registros; p-002 = 1 registro.")
    print("OK: histórico reconstruído sem perda ou duplicação nos cenários testados.")
    central.close()
    auditoria.close()


if __name__ == "__main__":
    with TemporaryDirectory(prefix="saude-spike-") as diretorio:
        executar(Path(diretorio))
