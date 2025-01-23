from odoo import models, fields
from odoo.tests.common import Form


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def update_partner_using_form(self):
        for order in self:
            # Criar um formulário para a ordem de venda
            order_form = Form(order)

            # Atualizar o parceiro no formulário
            order_form.partner_id = order.partner_id

            # Salvar as mudanças feitas pelo formulário
            updated_order = order_form.save()

            # Opcional: retornar ou fazer algo com o pedido atualizado
            return updated_order
