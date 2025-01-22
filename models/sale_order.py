from odoo import models, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def _onchange_partner_id_update_fiscal_operation(self):
        for order in self:
            for line in order.order_line:
                if line.fiscal_operation_id:
                    # Atribuir novamente o mesmo valor para disparar gatilhos
                    line.fiscal_operation_id = line.fiscal_operation_id.id
