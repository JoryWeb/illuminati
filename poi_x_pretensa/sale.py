##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2013 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Coded by: Grover Menacho
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv, fields
from openerp import api, models
from openerp.tools.translate import _


class ir_model_fields(osv.osv):
    _inherit = 'ir.model.fields'

    _columns = {
        'selection': fields.char('Selection Options', size=512, help="List of options for a selection field, "
                                                                     "specified as a Python expression defining a list of (key, label) pairs. "
                                                                     "For example: [('blue','Blue'),('yellow','Yellow')]"),
    }


ir_model_fields()


class cliente(osv.osv):
    _inherit = 'res.partner'

    def create(self, cr, uid, vals, context=None):

        # Pretensa valida datos minimos
        if ('customer' in vals and vals['customer']) or 'customer' not in vals:
            # Si es cliente o si simplemente no se especifica (como desde la creación directa del widget)
            if 'phone' not in vals and 'mobile' not in vals:
                raise osv.except_osv(_('Datos Inválidos'), _('La creación de un Cliente debe incluir teléfono o Móvil'))
            elif not vals['phone'] and not vals['mobile']:
                raise osv.except_osv(_('Datos Inválidos'), _('La creación de un Cliente debe incluir teléfono o Móvil'))
        new_id = super(cliente, self).create(cr, uid, vals, context=context)
        return new_id


cliente()


class sale_order(osv.osv):
    _inherit = 'sale.order'

    def onchange_vendedor(self, cr, uid, ids, vendedor, context=None):
        # Redundancia inevitable debido a los campos que 'sale_crm' inserta despues de user_id.
        v = {}
        if vendedor:
            v['user_id'] = vendedor
        else:
            v['user_id'] = False

        return {'value': v}

    def onchange_user(self, cr, uid, ids, user_id, context=None):
        v = {}
        if user_id:
            v['vendedor'] = user_id
        else:
            v['vendedor'] = False

        return {'value': v}

    # def _get_total_metric(self, cr, uid, ids, field_names, arg=None, context=None):
    #
    #     res = {}
    #
    #     for order in self.browse(cr, uid, ids, context=context):
    #         res[order.id] = {}
    #         sum_metric = 0.0
    #         sum_metric_m2 = 0.0
    #         sum_metric_m3 = 0.0
    #         sum_weight = 0.0
    #         top_uom = ''
    #         for line in order.order_line:
    #             tot_dim = line.get_total_dimension()[line.id] or 0.0
    #             metric_type = line.get_metric_type()[line.id]
    #             if metric_type == 'lineal':
    #                 sum_metric += tot_dim
    #                 sum_metric_m2 += 0.0
    #                 sum_metric_m3 += 0.0
    #             else:
    #                 if metric_type == 'area':
    #                     sum_metric_m2 += tot_dim
    #                     sum_metric += 0.0
    #                     sum_metric_m3 += 0.0
    #                 else:
    #                     if metric_type == 'volume':
    #                         sum_metric_m3 += tot_dim
    #                         sum_metric_m2 += 0.0
    #                         sum_metric += 0.0
    #                     else:
    #                         sum_metric += 0.0
    #                         sum_metric_m2 += 0.0
    #                         sum_metric_m3 += 0.0
    #             sum_weight += (
    #                           line.product_id and line.product_id.weight or 0.0) * tot_dim  # * (line.product_uom_qty or 0.0)
    #             top_uom = line.product_dimension and line.product_dimension.uom_id.name or ''
    #
    #             res[order.id]['total_metric'] = str(sum_metric) + ' ' + top_uom
    #
    #             res[order.id]['total_metric_m2'] = str(sum_metric_m2) + ' ' + top_uom + u"²"
    #
    #             res[order.id]['total_metric_m3'] = str(sum_metric_m3) + ' ' + top_uom + u"³"
    #
    #             res[order.id]['total_weight'] = sum_weight / 46  # División para quintales
    #     return res

    _columns = {
        'tipo_entrega': fields.selection([('planta', 'En planta'), ('obra', 'En obra')], 'Entrega', required=False),
        'socio_ref': fields.many2one('res.partner', 'Socio Referente'),
        'vendedor': fields.many2one('res.users', 'Vendedor', readonly=True,
                                    states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'warehouse_alt_id': fields.many2one('stock.warehouse', u'Almacén alternativo', readonly=True,
                                            states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                            help=u"Almacén alternativo de despacho; a especificar sólo en casos especiales en los que la mercadería no será despachada desde la misma Tienda."),
        'flete_origen': fields.char('Flete Origen', size=32),
        'flete_destino': fields.char('Flete Destino', size=32),
        'seguro': fields.char('Seguro', size=32),
        'nandina': fields.char(u'Código NANDINA', size=32),
        'partner_shipping_id': fields.many2one('res.partner', u'Dirección de Entrega', readonly=True, required=True,
                                               states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                               help=u"Dirección de entrega para el cliente."),

    }

    # def onchange_shop_id(self, cr, uid, ids, shop_id, context=None):
    #
    #     res=super(sale_order,self).onchange_shop_id(cr, uid, ids, shop_id, context=context)
    #     #En principio, restringir CUALQUIER Almacen alternativo
    #     if 'domain' not in res:
    #         res['domain'] = {}
    #     res['domain']['warehouse_alt_id'] = [('id', '=', 0)]
    #     res['value']['warehouse_alt_id'] = False
    #     if shop_id:
    #         shop = self.pool.get('res.shop').browse(cr, uid, shop_id, context=context)
    #         if shop.warehouse_id:
    #             #Sólo si su tienda lo tiene parametrizado, habilitar los almacenes autorizados
    #             valid_warehouse_id = []
    #             for wh in shop.warehouse_id:
    #                 valid_warehouse_id.append(wh.id)
    #             res['domain']['warehouse_alt_id'] = [('id', 'in', valid_warehouse_id)]
    #
    #     return res
    #
    # def _prepare_order_picking(self, cr, uid, order, context=None):
    #
    #     pick_dict = super(sale_order, self)._prepare_order_picking(cr, uid, order,context=context)
    #     if order.user_id:
    #         pick_dict['vendedor'] = order.user_id.id
    #     if order.tipo_entrega:
    #        pick_dict['tipo_entrega'] = order.tipo_entrega
    #     if order.socio_ref:
    #        pick_dict['socio_ref'] = order.socio_ref.id
    #     return pick_dict
    #

    # def _prepare_order_line_move(self, cr, uid, order, line, picking_id, date_planned, context=None):
    #
    #     res = super(sale_order, self)._prepare_order_line_move(cr, uid, order, line, picking_id, date_planned, context=context)
    #     if order.warehouse_alt_id:
    #         location_id = order.warehouse_alt_id.lot_stock_id and order.warehouse_alt_id.lot_stock_id.id or False
    #         if location_id:
    #             if order.warehouse_alt_id.id not in [x.id for x in order.shop_id.warehouse_ids]:
    #                 raise osv.except_osv((u'Inválido'), (u'El almacén Alternativo seleccionado no esta autorizado para esta Tienda.'))
    #             res['location_id']=location_id
    #
    #     return res
    #
    # def action_button_confirm(self, cr, uid, ids, context=None):
    #
    #     #Antes de validar una venta, pretensa verifica que el cliente tenga nit o ci
    #     for order in self.browse(cr, uid, ids, context=context):
    #         if order.partner_id:
    #             if order.partner_id.is_company and (not order.partner_id.nit or order.partner_id.nit == ''):
    #                 raise osv.except_osv((u'Inválido'), ('Para confirmar una venta la empresa Cliente debe tener un NIT asignado'))
    #             if not order.partner_id.is_company and (not order.partner_id.ci or order.partner_id.ci == ''):
    #                 raise osv.except_osv((u'Inválido'), ('Para confirmar una venta el contacto Cliente debe tener un CI asignado'))
    #
    #
    #     return super(sale_order, self).action_button_confirm(cr, uid, ids, context=context)


sale_order()


class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'

    def _get_desp_total(self, cr, uid, ids, field_names, arg=None, context=None):

        res = {}

        for sale_line in self.browse(cr, uid, ids, context=context):
            total = False
            if sale_line.despuntes:
                total = int(sale_line.despuntes) * (sale_line.product_uom_qty or 0.0)
            res[sale_line.id] = total

        return res

    # def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
    #
    #     res = {}
    #     res = super(sale_order_line, self)._amount_line(cr, uid, ids, field_name, arg, context=context)
    #     return res

    _columns = {
        'despuntes': fields.selection([('0', '0'), ('1', '1'), ('2', '2')], 'Nr Desp.', required=False,
                                      help="Nr. de Despuntes en el Producto"),
        'desp_total': fields.function(_get_desp_total, type='integer', string='Tot Desp.'),
        # 'price_subtotal_db': fields.function(_amount_line, store=True, string='Subtotal', digits_compute= dp.get_precision('Account')),
    }


    # def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
    #         uom=False, qty_uos=0, uos=False, name='', partner_id=False,
    #         lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
    #     #Por ahora, anular mensaje de advertencia de stock negativo
    #     result = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty=qty, uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)
    #     if 'warning' in result:
    #         ###--##--##--##
    #         tipo_producto=self.pool.get('product.product').browse(cr, uid, product, context=context).type
    #
    #         if tipo_producto=='product' or tipo_producto=='service':
    #             if result['warning'].get('message') is not None:
    #                 if result['warning'].get('message').find('stock') and context.get('product_dimension', False)==False:
    #                     result['warning']=False
    #         if context.get('product_dimension', False):
    #             pricelist_version=self.pool.get('product.pricelist.version').search(cr,uid,[('pricelist_id','=',pricelist),('active','=',True)])
    #             product_pricelist_version=self.pool.get('product.pricelist.item').search(cr,uid,[('price_version_id','=',pricelist_version[0]),('product_id','=',product)])
    #             product_pricelist_item=self.pool.get('product.pricelist.item').browse(cr, uid, product_pricelist_version, context=context)
    #             min_metric=product_pricelist_item[0].min_metric
    #             max_metric=product_pricelist_item[0].max_metric
    #             product_dimension=context['product_dimension']
    #             metric_type=self.pool.get('product.dimension').browse(cr, uid, product_dimension, context=context)
    #             tipo=self.pool.get('product.product').browse(cr, uid, product, context=context)
    #
    #             if tipo.metric_type=='lineal':
    #                 if metric_type.var_y==0 and metric_type.var_z==0:
    #                     if  metric_type.var_x<min_metric or metric_type.var_x>max_metric:
    #                         result['warning']['message'] = u'La dimensión seleccionada no es valida para este producto, por favor seleccione otra dimensión'
    #                     else:
    #                         result['warning']=False
    #                 else:
    #                     result['warning']=False
    #
    #             if tipo.metric_type=='volume':
    #                 total_volume=metric_type.var_x*metric_type.var_y*metric_type.var_z
    #                 if  total_volume<min_metric or total_volume>max_metric:
    #                     result['warning']['message'] = u'La dimensión seleccionada no es valida para este producto, por favor seleccione otra dimensión'
    #                 else:
    #                     result['warning']=False
    #     return result


sale_order_line()


# Usar res.shop
class stock_warehouse(osv.osv):
    _inherit = "stock.warehouse"
    _columns = {
        'warehouse_ids': fields.many2many('stock.warehouse', 'stock_ware_warehouse_rel', 'ware_id', 'warehouse_id',
                                          string='Almacenes alternativos',
                                          help=u"Especifica almacenes adicionales alternativos, desde los cuales la persona con el rol adecuado podrá hacer ventas directas."),
    }


stock_warehouse()
