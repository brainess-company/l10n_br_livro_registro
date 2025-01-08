{
    "name": "Livro Registro de Entradas e Saídas",
    "summary": "Geração dos relatórios Livro Registro de Entradas (P1/A) e Saídas (P2/A)",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "brainess",
    "depends": ["base", "sale", "purchase", "account", "l10n_br_fiscal"],
    "data": [
        "security/ir_model_access.csv",
        "views/livro_registro_views.xml",
        "reports/livro_registro_report.xml",
    ],
    "installable": True,
    "application": True,
}
