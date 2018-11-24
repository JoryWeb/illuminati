from openerp.osv import fields, osv
import unicodedata


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


class product_return(osv.osv):
    """docstring for pret_cubiertas_report"""
    _name = "product.return"
    _description = 'Product Return'
    _inherit = ['mail.thread']

    _columns = {
        'sale_id': fields.many2one('sale.order', 'Orden de Venta'),
        'partner_id': fields.many2one('res.partner', 'Cliente'),
        'picking_id': fields.many2one('stock.picking', 'Albaran'),
        'date': fields.date('Fecha'),
        'cause': fields.text('Motivo de la Devolucion', required=True),
        'request_id': fields.many2one('res.users', 'Solicitado por'),
        'user_id': fields.many2one('res.users', 'Aprobado por'),
        'state': fields.selection([
            ('draft', 'Borrador'),
            ('send', 'Enviado'),
            ('confirm', 'Confirmado'),
            ('done', 'Realizado'),
            ('cancel', 'Cancelado'),
        ], 'Status', select=True, readonly=True),
        'line_ids': fields.one2many('product.return.line', 'return_id', 'Productos', readonly=False),
    }

    _defaults = {
        'state': 'draft',
        'request_id': lambda self, cr, uid, ctx: uid,
    }

    def onchange_sale_id(self, cr, uid, ids, sale_id=False, contract_id=False, context=None):
        so_obj = self.pool.get('sale.order')

        if context is None:
            context = {}
        # defaults
        res = {'value': {
            'partner_id': False,

        }
        }
        order_id = so_obj.search(cr, uid, [('id', '=', sale_id)], context=context)

        if not order_id:
            return res
        order = so_obj.browse(cr, uid, order_id[0], context=context)
        res['value'].update({
            'partner_id': order and order.partner_id.id or False,
        })
        return res

    def onchange_picking_id(self, cr, uid, ids, picking_id=False, contract_id=False, context=None):
        sp_obj = self.pool.get('stock.picking')

        if context is None:
            context = {}
        # defaults
        res = {'value': {
            'line_ids': False,
            }
        }
        picking_id = sp_obj.search(cr, uid, [('id', '=', picking_id)], context=context)

        if not picking_id:
            return res
        picking = sp_obj.browse(cr, uid, picking_id[0], context=context)
        lines = []
        for sm in picking.move_lines:
            lines.append((0, 0, {'product_id': sm.product_id.id, 'origin_qty': sm.product_qty, 'lote': sm.restrict_lot_id.id,
                           'product_uom': sm.product_uom.id}))
        res['value'].update({
            'line_ids': lines
        })
        return res

    def request_return(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'send'}, context=context)

    def approve_request(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'confirm', 'user_id': uid}, context=context)

    def process_return(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'done'}, context=context)

    def cancel_return(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'cancel'}, context=context)


class product_return_line(osv.osv):
    """docstring for pret_cubiertas_report"""
    _name = "product.return.line"
    _description = 'Product Return'

    _columns = {
        'return_id': fields.many2one('product.return', 'Producto Retornar'),
        'product_id': fields.many2one('product.product', 'Producto'),
        'dimension_id': fields.many2one('product.dimension', 'Dimension'),
        'lote': fields.many2one('stock.production.lot', 'N° Serie'),
        'product_uom': fields.many2one('product.uom', 'Unidad de Medida'),
        'origin_qty': fields.float('Cantidad'),
        'return_qty': fields.float('Cantidad Devuelta'),
    }
