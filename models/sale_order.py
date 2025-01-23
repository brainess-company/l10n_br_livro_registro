from odoo import models, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def _onchange_partner_id_update_fiscal_operation(self):
        for order in self:
            # Reatribuir o cliente a ele mesmo para disparar gatilhos
            order.partner_id = order.partner_id

            # Atualizar fiscal_operation_id nas linhas
            for line in order.order_line:
                if line.fiscal_operation_id:
                    # Reatribuir o valor atual para disparar gatilhos
                    line.fiscal_operation_id = line.fiscal_operation_id.id
