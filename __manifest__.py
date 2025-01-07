{
    "name": "Livro Registro de Entradas e Saídas",
    "summary": "Geração dos relatórios Livro Registro de Entradas (P1/A) e Saídas (P2/A)",
    "version": "1.0",
    "author": "Sua Empresa",
    "license": "AGPL-3",
    "depends": ["base", "sale", "purchase", "l10n_br_fiscal"],
    "data": [
        "views/livro_registro_views.xml",
        "reports/livro_registro_report.xml",
    ],
    "installable": True,
    "application": False,
}
