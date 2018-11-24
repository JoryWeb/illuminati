from odoo import models, fields, api

class SaleOrderExtra(models.TransientModel):
    _name = "sale.order.extra"
    _description = "Extra Accsesorios para La orden de Venta"

    product_id = fields.Many2one('product.product', 'Producto')
    order_id = fields.Many2one('sale.order', 'Cotizacion')


    @api.onchange('order_id')
    def _onchange_product_id_domain(self):
        available_products_ids = []
        product_obj = self.env['product.product']
        domain_str = [('accessory', '=', True), ('master_padre', 'in', self.order_id.product_id.id)]
        product_ids = product_obj.search(domain_str)

        for lot in product_ids:
            available_products_ids.append(lot.id)


        return {
            'domain': {'product_id': [('id', 'in', available_products_ids)]}
        }

    @api.multi
    def action_add_items(self):
        self.order_id.order_line_a = [(0,0,{'product_id': self.product_id.id})]
