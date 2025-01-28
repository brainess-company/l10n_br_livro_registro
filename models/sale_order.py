from odoo import models, fields
from odoo.tests.common import Form


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def update_partner_using_form(self):
        for order in self:
            order_form = Form(order)
            order_form.partner_id = order.partner_id
            updated_order = order_form.save()
            return updated_order

    def write(self, values):
        # Verificar se o campo 'partner_id' foi alterado
        if 'partner_id' in values:
            # Chamar a função quando o 'partner_id' for alterado
            self.update_partner_using_form()

        # Chamar o método 'write' original para salvar as mudanças
        return super(SaleOrder, self).write(values)
