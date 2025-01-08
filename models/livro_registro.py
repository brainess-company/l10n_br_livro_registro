from odoo import models, fields, api
import io
from odoo.tools import xlsxwriter


class LivroRegistroRelatorio(models.TransientModel):
    _name = "livro.registro.relatorio"
    _description = "Livro Registro de Entradas e Saídas"

    name = fields.Char(default="Relatório Livro Registro")
    data_inicio = fields.Date(string="Data de Início", required=True)
    data_fim = fields.Date(string="Data de Fim", required=True)
    tipo_livro = fields.Selection([
        ('entrada', 'Entradas (P1/A)'),
        ('saida', 'Saídas (P2/A)')
    ], string="Tipo de Livro", required=True)
    company_id = fields.Many2one('res.company', string="Empresa", required=True,
                                 default=lambda self: self.env.company)

    def gerar_relatorio(self):
        documentos = self.env['account.move'].search([
            ('move_type', '=', 'in_invoice' if self.tipo_livro == 'entrada' else 'out_invoice'),
            ('invoice_date', '>=', self.data_inicio),
            ('invoice_date', '<=', self.data_fim),
            ('company_id', '=', self.company_id.id),
            ('state', '=', 'posted')
        ])
        if not documentos:
            raise ValueError("Nenhum documento fiscal encontrado no período especificado.")

        # Gerar PDF ou XLSX
        if self.env.context.get('format') == 'pdf':
            return self._gerar_pdf(documentos)
        elif self.env.context.get('format') == 'xlsx':
            return self._gerar_xlsx(documentos)

    def _gerar_xlsx(self, documentos):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Livro Registro')

        # Cabeçalho do relatório
        title = f"LIVRO REGISTRO DE {'ENTRADAS' if self.tipo_livro == 'entrada' else 'SAÍDAS'} - MODELO P{'1' if self.tipo_livro == 'entrada' else '2'}/A"
        sheet.merge_range('A1:I1', title,
                          workbook.add_format({'align': 'center', 'bold': True, 'font_size': 14}))
        sheet.write('A2', f"Empresa: {self.company_id.name}")
        sheet.write('A3', f"Período: {self.data_inicio} a {self.data_fim}")

        # Cabeçalhos da tabela
        headers = [
            'Data Emissão', 'Número NF', 'Série', 'Fornecedor/Cliente',
            'CFOP', 'Base ICMS', 'Valor ICMS', 'Valor IPI', 'Valor Total'
        ]
        header_format = workbook.add_format({'bold': True, 'bg_color': '#CCCCCC', 'border': 1})
        for col_num, header in enumerate(headers):
            sheet.write(4, col_num, header, header_format)

        # Dados
        row = 5
        for doc in documentos:
            for line in doc.line_ids:  # Acessar as linhas da fatura
                sheet.write(row, 0,
                            doc.invoice_date.strftime('%d/%m/%Y') if doc.invoice_date else '')
                sheet.write(row, 1, doc.name or '')
                sheet.write(row, 2, doc.invoice_sequence or '')  # Se necessário
                sheet.write(row, 3, doc.partner_id.name or '')
                sheet.write(row, 4, line.l10n_br_cfop_id.code if line.l10n_br_cfop_id else '')
                sheet.write_number(row, 5,
                                   line.balance)  # Valor ICMS, ou ajuste conforme sua lógica
                sheet.write_number(row, 6,
                                   line.tax_base_amount or 0)  # Valor ICMS, ou ajuste conforme sua lógica
                sheet.write_number(row, 7,
                                   line.l10n_br_ipi_value or 0)  # Se necessário, ajuste conforme sua lógica
                sheet.write_number(row, 8, doc.amount_total)
                row += 1

        # Totais
        total_format = workbook.add_format({'bold': True, 'border': 1})
        sheet.write(row, 4, "Totais:", total_format)
        sheet.write_formula(row, 5, f"=SUM(F6:F{row})", total_format)
        sheet.write_formula(row, 6, f"=SUM(G6:G{row})", total_format)
        sheet.write_formula(row, 7, f"=SUM(H6:H{row})", total_format)
        sheet.write_formula(row, 8, f"=SUM(I6:I{row})", total_format)

        workbook.close()
        output.seek(0)

        return self.env['ir.attachment'].create({
            'name': 'Livro_Registro.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.getvalue()),  # Encode em base64
            'res_model': self._name,
            'res_id': self.id,
        })

    def _gerar_pdf(self, documentos):
        # Referenciar o template XML criado
        report_template = self.env.ref('l10n_br_livro_registro.livro_registro_pdf_template')

        # Definir os dados a serem passados ao template
        data = {
            'docs': self,
            'documentos': documentos,
            'data_inicio': self.data_inicio,
            'data_fim': self.data_fim,
            'tipo_livro': 'Saídas (P2/A)' if self.tipo_livro == 'saida' else 'Entradas (P1/A)',
            'empresa': self.company_id,
        }

        # Gerar o conteúdo do PDF
        pdf_content, content_type = self.env['ir.actions.report']._render_qweb_pdf(
            report_template.id, data
        )

        # Retornar o PDF como um anexo ou resposta
        return self.env['ir.attachment'].create({
            'name': 'Livro_Registro_Saidas.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),  # Encode em base64
            'res_model': self._name,
            'res_id': self.id,
        })
