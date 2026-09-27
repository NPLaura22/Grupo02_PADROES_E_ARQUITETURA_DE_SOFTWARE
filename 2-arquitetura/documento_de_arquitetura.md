C4Context
    title Diagrama de Contexto - Rede Municipal de Atenção à Saúde (Envelope E)

    Person(paciente, "Cidadão / Paciente", "Solicita consultas, exames, vacinas e exerce direitos LGPD.")
    Person(medico, "Profissional de Saúde", "Atende em UBS/UPA/Hospital, prescreve medicamentos e registra prontuários.")
    Person(auditor, "Auditor do Órgão Regulador", "Fiscaliza conformidade, tempos de atendimento e Notificações Compulsórias.")

    System(sistemaSaude, "Sistema Municipal de Saúde", "Gerencia prontuários, regulação de leitos, dispensação de medicamentos e auditoria imutável.")

    System_Ext(sistemaLegado, "Sistema Legado de Regulação", "Mantido por 2 anos para gestão de filas históricas.")
    System_Ext(ministerioSaude, "Sistemas Federais / MS (e-SUS/RNDS)", "Recebe notificações compulsórias em até 24h e dados consolidados.")

    Rel(paciente, sistemaSaude, "Consulta agendamentos e histórico", "HTTPS / Fluxo")
    Rel(medico, sistemaSaude, "Registra atendimentos e prescreve", "HTTPS / Fluxo")
    Rel(auditor, sistemaSaude, "Consulta relatórios e trilha de auditoria", "HTTPS / Fluxo")

    Rel(sistemaSaude, sistemaLegado, "Sincroniza solicitações de leitos/exames", "HTTPS / REST / Chamada")
    Rel(sistemaSaude, ministerioSaude, "Transmite notificações e lotes RNDS", "HTTPS / mTLS / Evento")
