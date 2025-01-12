from odoo import models, fields, api
import io
import base64
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
        # entrada
        # todo: separar os decumentos de entrada e saída
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
            'Data Emissão', 'Número NF', 'Série',
            'tipo', 'cliente',
            'Fornecedor/Cliente',
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
                sheet.write(row, 1, doc.fiscal_document_id.document_number or '')
                sheet.write(row, 2, doc.fiscal_document_id.document_serie or '')  # Se necessário
                # SERIE - doc.fiscal_document_id.document_serie
                # NUMBER - doc.fiscal_document_id.document_number
                # DOCUMENT TYPE - doc.fiscal_document_id.document_type_id.prefix
                # CODIGO EMITENTE - codigo aleatório pode ser o id

                sheet.write(row, 3, doc.fiscal_document_id.document_type_id.prefix or '')  # Se necessário
                sheet.write(row, 4, doc.partner_id or '')  # Se necessário


                # select am.move_type,am.state,am.company_id,am.*, lf.* from account_move as am
                # select * from account_move as am left join l10n_br_fiscal_document as lf on lf.id = am.fiscal_document_id
                # select * from l10n_br_fiscal_document

                sheet.write(row, 5, doc.partner_id.name or '')
                sheet.write(row, 6, line.fiscal_document_line_id.cfop_id.code if line.fiscal_document_line_id.cfop_id else '')
                sheet.write_number(row, 7,
                                   line.balance)  # Valor ICMS, ou ajuste conforme sua lógica
                sheet.write_number(row, 8,
                                   line.tax_base_amount or 0)  # Valor ICMS, ou ajuste conforme sua lógica
                sheet.write_number(row, 9,
                                   line.fiscal_document_line_id.ipi_value or 0)  # Se necessário, ajuste conforme sua lógica
                sheet.write_number(row, 10, doc.amount_total)
                row += 1

        # Totais
        total_format = workbook.add_format({'bold': True, 'border': 1})
        sheet.write(row, 6, "Totais:", total_format)
        sheet.write_formula(row, 7, f"=SUM(F6:F{row})", total_format)
        sheet.write_formula(row, 8, f"=SUM(G6:G{row})", total_format)
        sheet.write_formula(row, 9, f"=SUM(H6:H{row})", total_format)
        sheet.write_formula(row, 10, f"=SUM(I6:I{row})", total_format)

        workbook.close()
        output.seek(0)

        # Criar o anexo para download
        attachment = self.env['ir.attachment'].create({
            'name': 'Livro_Registro.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.getvalue()),  # Encode em base64
            'res_model': self._name,
            'res_id': self.id,
        })

        # Retornar o anexo como resposta
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%d?download=true' % attachment.id,
            'target': 'new',
        }

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
