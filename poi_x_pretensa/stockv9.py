
from openerp import api, models, fields

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    user_option_ids = fields.Many2many('res.users', 'res_shop_option_res_users_rel', 'warehouse_id', 'user_id',
                                       string='Usuarios Asigandos')

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.depends('move_lines')
    def _compute_sale_user_id(self):
        for picking in self:
            user_id = False
            for move in picking.move_lines:
                if move.procurement_id.sale_line_id:
                    user_id = move.procurement_id.sale_line_id.order_id.user_id
                    break
            if user_id:
                picking.vendedor = user_id.id
            else:
                picking.vendedor = self._uid

    @api.depends('move_lines')
    def _compute_sale_order_shop(self):
        for picking in self:
            warehouse_id = False
            for move in picking.move_lines:
                if move.procurement_id.sale_line_id:
                    warehouse_id = move.procurement_id.sale_line_id.order_id.warehouse_id
                    break
            if warehouse_id:
                picking.shop_id = warehouse_id.id

    vendedor = fields.Many2one(comodel_name='res.users', string="Vendedor", compute='_compute_sale_user_id')
    shop_id = fields.Many2one(comodel_name='stock.warehouse', string=u"Tienda/Almacén", compute='_compute_sale_order_shop', store=True)


