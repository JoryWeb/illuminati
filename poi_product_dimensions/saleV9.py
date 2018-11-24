
from openerp import fields, models, api, _
from openerp.exceptions import Warning


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    total_dimension = fields.Float(string="Total Metric w/o unit")
    total_dimension_display = fields.Char(string="Total Metric", readonly=True)

    @api.model
    def create(self, values):
        if 'product_dimension' in values:
            dimension = self.env['product.dimension'].browse(values['product_dimension'])
            uom_obj = dimension.uom_id
            product_qty = values['product_uom_qty']
            var_x = dimension.var_x
            var_y = dimension.var_y
            var_z = dimension.var_z
            if dimension.metric_type == 'lineal':
                values['total_dimension'] = var_x * product_qty
                values['total_dimension_display'] = str(var_x * product_qty) + uom_obj.name
            elif dimension.metric_type == 'area':
                values['total_dimension'] = var_x * var_y * product_qty
                values['total_dimension_display'] = str(var_x * var_y * product_qty) + uom_obj.name + u"²"
            elif dimension.metric_type == 'volume':
                values['total_dimension'] = var_x * var_y * var_z * product_qty
                values['total_dimension_display'] = str(var_x * var_y * var_z * product_qty) + uom_obj.name + u"³"
            else:
                values['total_dimension'] = None
                values['total_dimension_display'] = None
        return super(SaleOrderLine, self).create(values)

    @api.multi
    def write(self, values):

        if 'product_dimension' in values or 'product_uom_qty' in values:
            if 'product_dimension' in values:
                dimension_id = values['product_dimension']
            else:
                dimension_id = self.product_dimension.id
            dimension = self.env['product.dimension'].browse(dimension_id)
            uom_obj = dimension.uom_id
            if 'product_uom_qty' in values:
                product_qty = values['product_uom_qty']
            else:
                product_qty = self.product_uom_qty
            var_x = dimension.var_x
            var_y = dimension.var_y
            var_z = dimension.var_z

            if dimension.metric_type == 'lineal':
                values['total_dimension'] = var_x * product_qty
                values['total_dimension_display'] = str(var_x * product_qty) + uom_obj.name
            elif dimension.metric_type == 'area':
                values['total_dimension'] = var_x * var_y * product_qty
                values['total_dimension_display'] = str(var_x * var_y * product_qty) + uom_obj.name + u"²"
            elif dimension.metric_type == 'volume':
                values['total_dimension'] = var_x * var_y * var_z * product_qty
                values['total_dimension_display'] = str(var_x * var_y * var_z * product_qty) + uom_obj.name + u"³"
            else:
                values['total_dimension'] = None
                values['total_dimension_display'] = None
        res = super(SaleOrderLine, self).write(values)
        return res

    # def _get_total_dimension(self):
    #     for line in self:
    #         #res[line.id] = {'total_dimension': None, 'total_dimension_display': None}
    #         uom_obj = line.product_dimension.uom_id
    #
    #         product_qty = line.product_uom_qty
    #         var_x = line.product_dimension.var_x
    #         var_y = line.product_dimension.var_y
    #         var_z = line.product_dimension.var_z
    #
    #         if line.product_dimension.metric_type == 'lineal':
    #             line.total_dimension = var_x * product_qty
    #             line.total_dimension_display = str(var_x * product_qty) + uom_obj.name
    #         elif line.product_dimension.metric_type == 'area':
    #             line.total_dimension = var_x * var_y * product_qty
    #             line.total_dimension_display = str(var_x * var_y * product_qty) + uom_obj.name + u"²"
    #         elif line.product_dimension.metric_type == 'volume':
    #             line.total_dimension = var_x * var_y * var_z * product_qty
    #             line.total_dimension_display = str(var_x * var_y * var_z * product_qty) + uom_obj.name + u"³"
    #         else:
    #             line.total_dimension = None
    #             line.total_dimension_display = None