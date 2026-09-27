"""Grupo 5 — Ônibus / E: prova da segregação assíncrona do ADR 05.

SQLite simula os dois bancos; a chamada de entrega simula o barramento.
Valores são centavos e datas/regras são fixas para permitir replay exato.
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
        CREATE TABLE IF NOT EXISTS viagens (
            id TEXT PRIMARY KEY, operadora TEXT NOT NULL,
            data TEXT NOT NULL, regra TEXT NOT NULL, centavos INTEGER NOT NULL
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


def registrar(central, identificador, operadora, data, regra, centavos,
              falhar=False):
    """Núcleo e adaptador: viagem e intenção de publicar na mesma transação."""
    evento = json.dumps(dict(id=identificador, operadora=operadora,
                             data=data, regra=regra, centavos=centavos),
                        sort_keys=True)
    with central:
        central.execute("INSERT INTO viagens VALUES (?, ?, ?, ?, ?)",
                        (identificador, operadora, data, regra, centavos))
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
    """Relay/barramento mínimo: entrega ao menos uma vez, ACK após commit."""
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


def reconstruir(auditoria):
    """Projeção descartável: usa o valor e a regra históricos, sem saldo atual."""
    totais = {}
    for (conteudo,) in auditoria.execute("SELECT evento FROM eventos ORDER BY id"):
        evento = json.loads(conteudo)
        operadora = evento["operadora"]
        totais[operadora] = totais.get(operadora, 0) + evento["centavos"]
    return totais


def executar(pasta):
    central, auditoria = abrir_bancos(pasta)
    try:
        registrar(central, "v00", "A", "2026-09-01", "tarifa-v1", 500,
                  falhar=True)
    except FalhaSimulada:
        pass
    assert quantidade(central, "viagens") == quantidade(central, "outbox") == 0
    print("1. Falha na transação: viagem e outbox revertidas juntas.")

    registrar(central, "v01", "A", "2026-09-01", "tarifa-v1", 500)
    registrar(central, "v02", "A", "2026-09-16", "tarifa-v2", 550)
    registrar(central, "v03", "B", "2026-09-17", "tarifa-v2", 550)
    try:
        entregar(central, auditoria, rede=False)
    except FalhaSimulada:
        pass
    assert quantidade(central, "viagens") == quantidade(central, "outbox") == 3
    assert quantidade(auditoria, "eventos") == 0
    print("2. Rede fora: 3 viagens confirmadas, 3 eventos pendentes, 0 auditados.")

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

    original = auditoria.execute("SELECT evento FROM eventos WHERE id = 'v01'").fetchone()[0]
    try:
        consumir(auditoria, "v01", original.replace('500', '999'))
    except ValueError:
        print("5. Mesmo ID com conteúdo diferente: rejeitado.")
    else:
        raise AssertionError("Conflito de conteúdo deveria ser rejeitado")

    for comando in ("UPDATE eventos SET evento = '{}' WHERE id = 'v01'",
                    "DELETE FROM eventos WHERE id = 'v01'"):
        try:
            with auditoria:
                auditoria.execute(comando)
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("Mutação da auditoria deveria ser rejeitada")
    print("6. Alteração e exclusão de eventos: bloqueadas.")

    esperado = dict(central.execute(
        "SELECT operadora, SUM(centavos) FROM viagens GROUP BY operadora"
    ))
    assert esperado == {"A": 1050, "B": 550}
    with central:
        central.execute("DELETE FROM viagens")
    assert quantidade(central, "viagens") == 0
    assert reconstruir(auditoria) == esperado
    assert reconstruir(auditoria) == esperado
    print("7. Replay sem estado operacional: A = R$ 10,50; B = R$ 5,50.")
    print("OK: repasse reconstruído sem perda ou duplicação nos cenários testados.")
    central.close()
    auditoria.close()


if __name__ == "__main__":
    with TemporaryDirectory(prefix="onibus-spike-") as diretorio:
        executar(Path(diretorio))
