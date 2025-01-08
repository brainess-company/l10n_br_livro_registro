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

    def _gerar_pdf(self, documentos):
        # Referenciar o template XML criado
        report_template = self.env.ref('livro_registro.livro_registro_pdf_template')

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

    def _gerar_xlsx(self, documentos):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Livro Registro')

        # Cabeçalhos
        headers = [
            'Data Emissão', 'Número NF', 'Série', 'Fornecedor/Cliente',
            'CFOP', 'Base ICMS', 'Valor ICMS', 'Valor IPI', 'Valor Total'
        ]
        for col_num, header in enumerate(headers):
            sheet.write(0, col_num, header)

        # Dados
        row = 1
        for doc in documentos:
            sheet.write(row, 0, doc.invoice_date)
            sheet.write(row, 1, doc.name)
            sheet.write(row, 2, doc.invoice_sequence)
            sheet.write(row, 3, doc.partner_id.name)
            sheet.write(row, 4, doc.l10n_br_cfop_id.code if doc.l10n_br_cfop_id else '')
            sheet.write(row, 5, doc.amount_untaxed)
            sheet.write(row, 6, doc.amount_tax)
            sheet.write(row, 7, doc.l10n_br_ipi_value)
            sheet.write(row, 8, doc.amount_total)
            row += 1

        workbook.close()
        output.seek(0)

        return self.env['ir.attachment'].create({
            'name': 'Livro_Registro.xlsx',
            'type': 'binary',
            'datas': output.getvalue().encode('base64'),
            'res_model': self._name,
            'res_id': self.id,
        })
