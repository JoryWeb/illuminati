# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __odoo__.py file in root directory
##############################################################################
from odoo import models, api, fields, registry, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import odoo.addons.decimal_precision as dp
from lxml import etree
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class AnioToyosa(models.Model):
    _name = 'anio.toyosa'

    name = fields.Integer(u"Año")

    _sql_constraints = [
        ('name_uniq', 'unique (name)', u"El año ya existe !"),
    ]

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    country_id = fields.Many2one("res.country", u"País de Procedencia")
    n_produccion = fields.Char(u"Número de Producción", readonly=False, required=True, default='')
    warrant = fields.Selection([('sin_warrant', 'Sin Warrant'), ('warrant', 'Con Warrant')], required=False,
                               string=u"Método de financiamento")
    type_import = fields.Selection([('normal', 'normal'), ('toyosa', 'toyosa')])
    bank_id = fields.Many2one('res.bank', string="Banco")
    picking_type_id = fields.Many2one('stock.picking.type', 'Entregar', required=True, default=False,
                                      help="This will determine picking type of incoming shipment")
    partner_id_client = fields.Many2one('res.partner', string="Cliente")
    n_prestamo = fields.Char("N° de Prestamo")

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        # Quitar sheet para acomodar mejor el ancho de tantas columnas
        res = super(PurchaseOrder, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                         submenu=submenu)

        if view_type == 'form':
            doc = etree.XML(res['arch'])
            for sheet in doc.xpath("//sheet"):
                parent = sheet.getparent()
                index = parent.index(sheet)
                for child in sheet:
                    parent.insert(index, child)
                    index += 1
                parent.remove(sheet)
            res['arch'] = etree.tostring(doc)
        return res

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id_toyosa(self):
        # self.onchange_partner_id()
        if not self.partner_id:
            self.country_id = False
        else:
            self.country_id = self.partner_id.country_id.id
        return {}

    @api.onchange('date_order')
    def onchange_date_order_toyosa(self):
        if not self.date_order:
            self.n_produccion = ""
        else:
            valor = datetime.strptime(self.date_order, DEFAULT_SERVER_DATETIME_FORMAT)
            if valor.month > 10:
                self.n_produccion = str(valor.month) + '/' + str(valor.year)
            else:
                self.n_produccion = '0' + str(valor.month) + '/' + str(valor.year)
        return {}

    # @api.multi
    # def _create_picking(self):
    #     for order in self:
    #         if order.tipo_fac != '3':
    #             super(PurchaseOrder, self)._create_picking()
    #         else:
    #             if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
    #                 res = order._prepare_picking()
    #                 # El picking creado debe asignarse a la compra
    #                 res['purchase'] = order.id
    #                 picking = self.env['stock.picking'].create(res)
    #                 picking.n_produccion = order.n_produccion
    #                 moves = order.order_line.filtered(
    #                     lambda r: r.product_id.type in ['product', 'consu'])._create_stock_moves(picking)
    #
    #                 # Barrer el color interno y externo
    #                 for move_toy in moves:
    #                     move_toy.colorinterno = move_toy.purchase_line_id.colorinterno.id
    #                     move_toy.colorexterno = move_toy.purchase_line_id.colorexterno.id
    #                     move_toy.edicion = move_toy.purchase_line_id.edicion
    #                     move_toy.marca = move_toy.purchase_line_id.product_id.modelo.marca.id
    #                     move_toy.modelo = move_toy.purchase_line_id.modelo.id
    #                 move_ids = moves.action_confirm()
    #                 moves = self.env['stock.move'].browse(move_ids)
    #                 moves.force_assign()
    #                 # Crear Lotes de producción y asignar al primer movimientos
    #                 # En función del codigo master
    #                 # 12022017 Se utiliza el objeto poi.stock.reservation.lot para que puedan ser
    #                 # Utilizados en reservas y en reporte de reservas
    #                 pack_lot = self.env['stock.pack.operation.lot']
    #                 production_lot = self.env['stock.production.lot']
    #                 body_html = "<table style='width:80%;border: 1px solid black;border-collapse: collapse;'>" \
    #                             "<tr>" \
    #                             "<td>Chasis</td>" \
    #                             "<td>Color Interno</td>" \
    #                             "<td>Color Externo</td>" \
    #                             "<td>Color Katashiki</td>" \
    #                             "<td>Color Modelo</td>" \
    #                             "<td>Warrant</td>" \
    #                             "</tr>"
    #                 body_tr = ""
    #                 # 29082017 Prueba, existe un problema al registrar un mismo master con
    #                 # diferente colores, el sistema crea un solo pack operation y al momento de generar la distribución
    #                 # es dificil saber donde se hizo la transaccion.
    #                 is_real = False
    #                 for pack in picking.pack_operation_product_ids:
    #                     if pack.product_id.tracking in ('serial') and pack.product_id.cost_method in ('real'):
    #                         stock_link = self.env["stock.move.operation.link"].search([('operation_id', '=', pack.id)])
    #                         stock_link.unlink()
    #                         pack.unlink()
    #                         is_real = True
    #                     elif pack.product_id.cost_method in ('real'):
    #                         is_real = True
    #                     else:
    #                         is_real = False
    #                         break
    #                 # Ya no se necesita eliminar todos los packs del picking
    #                 # picking.pack_operation_product_ids.unlink()
    #
    #                 for move_line in picking.move_lines_related:
    #                     if move_line.product_id.tracking in ('serial') and move_line.product_id.cost_method in ('real'):
    #                         valor_pack = {'location_dest_id': move_line.location_dest_id.id,
    #                                       'product_id': move_line.product_id.id,
    #                                       'product_qty': move_line.product_qty,
    #                                       'product_uom_id': move_line.product_uom.id,
    #                                       'location_id': move_line.location_id.id,
    #                                       'picking_id': move_line.picking_id.id,
    #                                       'colorinterno': move_line.colorinterno.id,
    #                                       'colorexterno': move_line.colorexterno.id,
    #                                       'edicion': move_line.edicion,
    #                                       'price_unit': move_line.price_unit,
    #                                       'owner_id': False, }
    #                         pack_id = self.env["stock.pack.operation"].create(valor_pack)
    #                         self.env['stock.move.operation.link'].create({'move_id': move_line.id,
    #                                                                       'operation_id': pack_id.id,
    #                                                                       'qty': move_line.product_qty,
    #                                                                       })
    #                 for pack in picking.pack_operation_product_ids:
    #                     if pack.product_id.tracking in ('serial'):
    #                         for move in picking.move_lines:
    #                             if pack.product_id.id == move.product_id.id and pack.colorinterno.id == move.colorinterno.id and pack.colorexterno.id == move.colorexterno.id and pack.edicion == move.edicion and pack.price_unit == move.price_unit:
    #                                 if pack.product_id.tracking == 'serial':
    #                                     for x in range(int(move.product_uom_qty)):
    #                                         sum_qty = 1
    #                                         serie = 1
    #                                         n_correlativo = self.env['ir.sequence'].next_by_code(
    #                                             'stock.pack.operation.lot')
    #                                         produccion = str(move.purchase_line_id.order_id.n_produccion)
    #                                         edicion = str(move.purchase_line_id.edicion)
    #                                         codigo = order.name + "|" + produccion + '-' + str(n_correlativo)
    #                                         warrant = order.warrant
    #                                         if warrant == 'sin_warrant':
    #                                             lot_id = production_lot.with_context(mail_create_nolog=True).create({
    #                                                 'name': codigo,
    #                                                 'product_id': move.product_id.id,
    #                                                 'katashiki': move.purchase_line_id.katashiki.id,
    #                                                 'modelo': move.purchase_line_id.modelo.id,
    #                                                 'colorinterno': move.purchase_line_id.colorinterno.id,
    #                                                 'colorexterno': move.purchase_line_id.colorexterno.id,
    #                                                 'state_finanzas': 'sin_warrant',
    #                                                 'state_importaciones': 'no_nacionalizado',
    #                                                 'embarque': move.picking_id.embarque,
    #                                                 'n_produccion': codigo,
    #                                                 'produccion': produccion,
    #                                                 'edicion': move.purchase_line_id.edicion,
    #                                                 'anio_modelo': move.purchase_line_id.anio.id,
    #                                                 'order_line_id': move.purchase_line_id.id,
    #                                                 'bank_id': move.purchase_line_id.order_id.bank_id.id,
    #                                             })
    #                                         else:
    #                                             lot_id = production_lot.with_context(mail_create_nolog=True).create({
    #                                                 'name': codigo,
    #                                                 'product_id': move.product_id.id,
    #                                                 'katashiki': move.purchase_line_id.katashiki.id,
    #                                                 'colorinterno': move.purchase_line_id.colorinterno.id,
    #                                                 'colorexterno': move.purchase_line_id.colorexterno.id,
    #                                                 'modelo': move.purchase_line_id.modelo.id,
    #                                                 'embarque': move.picking_id.embarque,
    #                                                 'state_finanzas': 'no_liberado',
    #                                                 'state_importaciones': 'no_nacionalizado',
    #                                                 'n_produccion': codigo,
    #                                                 'produccion': produccion,
    #                                                 'edicion': move.purchase_line_id.edicion,
    #                                                 'anio_modelo': move.purchase_line_id.anio.id,
    #                                                 'order_line_id': move.purchase_line_id.id,
    #                                                 'bank_id': move.purchase_line_id.order_id.bank_id.id,
    #                                             })
    #                                         pack_lot.create({
    #                                             'lot_id': lot_id.id,
    #                                             'operation_id': pack.id,
    #                                             'qty': 0,
    #                                             'qty_todo': sum_qty,
    #                                             'lot_name': codigo,
    #                                             'edicion': edicion,
    #                                             'n_produccion': codigo,
    #                                             'colorinterno': move.purchase_line_id.colorinterno.id,
    #                                             'colorexterno': move.purchase_line_id.colorexterno.id,
    #                                             'n_correlativo': n_correlativo,
    #                                             'price_unit': move.price_unit,
    #                                         })
    #                                         body_tr = body_tr + """
    #                                                 <tr>
    #                                                 <td>""" + str(codigo) + """</td>
    #                                                 <td>""" + str(move.purchase_line_id.colorinterno.name) + """</td>
    #                                                 <td>""" + str(move.purchase_line_id.colorexterno.name) + """</td>
    #                                                 <td>""" + str(move.purchase_line_id.katashiki.name) + """</td>
    #                                                 <td>""" + str(move.purchase_line_id.modelo.name) + """</td>
    #                                                 <td>""" + str(warrant) + """</td>
    #                                                 </tr>
    #                                         """
    #                                         serie += 1
    #
    #                 body_html_send = body_html + body_tr + "</table>"
    #                 ## Enviar notificación de Chasis Creados a los grupos de venta base.group_sales_salesman_all_leads
    #                 ## base.group_sale_manager para que dispongan de las unidades para vender
    #
    #                 group_manager = self.env.ref('base.group_sale_manager')
    #                 group_salesman = self.env.ref('base.group_sale_salesman_all_leads')
    #
    #                 user_ids = group_manager.users.ids
    #                 user_ids = user_ids + group_salesman.users.ids
    #                 user_id = self._uid
    #
    #                 usuario = self.env['res.users'].browse(user_id)
    #                 # for user in user_ids:
    #                 #     partner_id = self.env['res.users'].browse(user).partner_id.id
    #                 #     usuario.message_post(body="Chasis Disponibles Para la venta <br />" + body_html_send,
    #                 #                          partner_ids=[partner_id],
    #                 #                          model='mail.channel', subject='',
    #                 #                          message_type='comment', subtype_is=1)
    #
    #                 # #Como el modulo depende de purchase_imports
    #                 # #podemos crear el documento de importaciones en este punto
    #
    #                 # si el metodo de valoración es real en la configuración no se debe crear
    #                 # la carpeta de importaciones
    #                 if not is_real:
    #                     valid_ppp = True
    #                     product_name = ''
    #                     # Validar si todos los productos son promedio ponderado
    #                     for move_line in picking.move_lines_related:
    #                         if move_line.product_id.cost_method in ('average'):
    #                             valid_ppp = True
    #                         else:
    #                             valid_ppp = False
    #                             product_name = move_line.product_id.name
    #
    #                     if valid_ppp:
    #                         imports = self.env['poi.purchase.imports']
    #                         values = {
    #                             'order_id': self.id,
    #                             'partner_id': self.partner_id.id,
    #                             'date': self.date_order,
    #                             'currency_id': self.currency_id.id,
    #                         }
    #                         imp = imports.create(values)
    #                         order.imports = imp.id
    #                     else:
    #                         raise UserError(_(
    #                             u'El producto %s tiene la configuración de Costo Real') % (product_name))
    #
    #     return True

    @api.multi
    def get_formview_id(self):
        """ Update form view id of action to open the invoice """
        if self.type_import in ('toyosa'):
            return self.env.ref('poi_x_toyosa.purchase_order_form_toyosa').id
        else:
            return self.env.ref('purchase.purchase_order_form').id

    @api.multi
    def action_view_invoice(self):
        '''
        Actualizar funcionalidad de tipo de compra asignar a factura
        '''

        result = super(PurchaseOrder, self).action_view_invoice()
        #### En caso de que se deba buscar un diario para multimoneda para que el asiento contable sea visible con la factura ####

        if hasattr(self, 'tipo_fac') and hasattr(self, 'type_import'):
            context = result['context']
            context.update({'type': 'in_invoice', 'default_purchase_id': self.id,
                            'default_tipo_fac': self.tipo_fac, 'importaciones': True})
        if self.payment_term_id:
            asd = result['context']
            asd.update({'default_payment_term_id': self.payment_term_id.id})
        return result


class ColorInterno(models.Model):
    _name = 'color.interno'
    name = fields.Char("Color Interno")
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "El color ya existe !"),
    ]

class ColorExterno(models.Model):
    _name = 'color.externo'
    name = fields.Char("Color Externo")
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "El color ya existe !"),
    ]

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    modelo = fields.Many2one("modelo.toyosa", "Modelo")
    katashiki = fields.Many2one("katashiki.toyosa", u"Código modelo")
    colorinterno = fields.Many2one("color.interno", string="Color Interno")
    colorexterno = fields.Many2one("color.externo", string="Color Externo")
    anio = fields.Many2one("anio.toyosa", string=u"Año Modelo")
    edicion = fields.Char("ED")
    date_neumatico = fields.Datetime(string=u'Fecha vencimiento', required=True, index=True,
                                     default=fields.Datetime.now)
    price_transporte = fields.Float(string='Precio transporte y seguro', required=True,
                                    digits=dp.get_precision('Product Price'),
                                    default=0.0)
    price_fabrica = fields.Float(string='Precio fabrica', required=True, digits=dp.get_precision('Product Price'),
                                 default=0.0)

    price_flete = fields.Float("Costo Flete")
    price_seguro = fields.Float("Costo Seguro")


    # Filtrar productos en funcion de los que se selecciona en la orden
    @api.onchange('modelo', 'katashiki')
    def onchange_modelo_katashiki(self):
        res = {}
        res.setdefault('domain', {})
        # Katashiki es el 'Código Modelo'
        if self.modelo and not self.katashiki:
            res['domain'] = {'product_id': [('modelo', '=', self.modelo.id), ('tracking', '=', 'serial')],
                             'katashiki': [('modelo', '=', self.modelo.id)]}
            return res
        elif self.katashiki and not self.modelo:
            res['domain'] = {'product_id': [('katashiki', '=', self.katashiki.id), ('tracking', '=', 'serial')]}
            return res
        elif self.modelo and self.katashiki:
            res['domain'] = {'product_id': [('modelo', '=', self.modelo.id), ('katashiki', '=', self.katashiki.id),
                                            ('tracking', '=', 'serial')]}
            return res
        else:
            res['domain'] = {
                'product_id': [('active', '=', True), ('purchase_ok', '=', True), ('tracking', '=', 'serial')]}
            return res
        return {}

    @api.multi
    def update_ed(self):

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'poi.purchase.line.update.wizard',
            'type': 'ir.actions.act_window',
            'context': self._context,
            'target': 'new'
        }

    @api.multi
    def _prepare_stock_moves(self, picking):
        res = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        for re in res:
            order = self.order_id
            re['colorinterno'] = self.colorinterno.id
            re['colorexterno'] = self.colorinterno.id
            re['edicion'] = self.edicion
            re['price_unit_fob'] = order.company_id.currency_id.compute(re['price_unit'], order.currency_id, round=False)
            re['currency_id'] = self.order_id.currency_id.id

        return res
