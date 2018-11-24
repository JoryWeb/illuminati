##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Poiesis Consulting (<http://www.poiesisconsulting.com>).
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

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

from lxml import etree
import time
import unicodedata
from openerp.tools.translate import _

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

class nota_credito(osv.TransientModel):

    _name = 'poi_bol.nota.wizard'
    _description = 'Asistente Nota de Crédito'

    _columns = {
        'description': fields.many2one('revert.description','Motivo', required=True),
        'date': fields.date('Fecha', help=u'Esta será la fecha de la Nota y se aplicará al Período correspondiente'),
        'journal_id': fields.many2one('account.journal', 'Diario Nota', help=u'Especifica el Diario a aplicar en la Nota de Crédito. Por defecto, usará el mismo Diario de la Factura base.'),
        'make_picking': fields.boolean(u'Crear Albarán', help=u"Esta opción creará un Albarán de Entrada por los productos devueltos."),
        'warehouse_id': fields.many2one('stock.warehouse', string='Almacen', help=u"Almacen al cual se hara la Entrada por devolución"),
        'product_ids': fields.one2many('poi_bol.nota.wizard.line', 'wizard_id', 'Productos a creditar'),
    }
    _defaults={
        'date': lambda *a: time.strftime('%Y-%m-%d'),
    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None:context = {}
        res = super(nota_credito, self).default_get(cr, uid, fields, context=context)
        inv_ids = context.get('active_ids', False)
        if inv_ids and len(inv_ids)>0:
            invoice_o = self.pool.get('account.invoice')
            inv_ids = context.get('active_ids', False)
            inv_lines = []
            for invoice in invoice_o.browse(cr, uid, inv_ids, context=context):
                for line in invoice.invoice_line_ids:
                    inv_lines.append((0,0,{'product_id': line.product_id.id, 'quantity': line.quantity or 0, 'uom_id': line.uom_id.id}))
            res.update({'product_ids': inv_lines})

        return res


    #Creado para hacer heredable la creacion de la nota.
    def _prepare_nota(self, cr, uid, nota):
        res = {'description': nota.description.id,
               'date': nota.date,
               'journal_id': nota.journal_id and nota.journal_id.id or False,
               'no_annul': True,
               }

        return res


    def action_make_nota(self, cr, uid, ids, context=None):

        refund_wiz = self.pool.get('account.invoice.refund')
        invoice_obj = self.pool.get('account.invoice')
        invoice_line_obj = self.pool.get('account.invoice.line')
        inv_ids = context.get('active_ids', False)
        if type(inv_ids) is list:
            inv_id = inv_ids[0]
            inv_base = invoice_obj.browse(cr, uid, inv_ids, context=context)[0]
        else:
            inv_id = inv_ids
            inv_base = invoice_obj.browse(cr, uid, inv_ids, context=context)

        #Error we don't need this. Set Base Invoice to annul

        #inv_base.action_annul()


        for nota in self.browse(cr, uid, ids, context=context):

            #Reutilizar funcionalidad del wizard Refund
            wiz_id = refund_wiz.create(cr, uid,self._prepare_nota(cr, uid, nota), context=context)
            wiz_ret = refund_wiz.compute_refund(cr, uid, [wiz_id], 'refund', context=context)

            refund_id = False
            for dom in wiz_ret['domain']:
                if dom[0] == 'id':
                    refund_id = dom[2]
                    if type(refund_id) is list: refund_id = refund_id[0]
            if not refund_id:
                raise osv.except_osv(u'Error de ejecución',u'No se pudo generar la rectificación')
            refund = invoice_obj.browse(cr, uid, [refund_id], context=context)[0]


            #Map Returned Products
            prods_returned = {}
            for prod in nota.product_ids:
                prods_returned[prod.product_id.id] = prod.quantity,prod.uom_id
            #Modify lines from refund according to returned products
            for refund_line in refund.invoice_line_ids:
                if refund_line.product_id.id in prods_returned:
                    returned_qty = prods_returned[refund_line.product_id.id][0]
                    returned_uom = prods_returned[refund_line.product_id.id][1]
                    if refund_line.uom_id.id != returned_uom.id:
                        #Asegurar que la cantidad no se exceda despues del cambio de UdM
                        #Asegurar que el precio se calcule en base a la factura original; no de Lista de precios actual.
                        if not returned_uom or not returned_uom.factor:
                            raise osv.except_osv(u'Dato inválido',u'Unidad de Medida de devolución no válida.')
                        equi_qty = returned_qty*refund_line.uos_id.factor/returned_uom.factor
                        equi_price = refund_line.price_unit*refund_line.uos_id.factor/returned_uom.factor
                        if equi_qty > refund_line.quantity:
                            raise osv.except_osv(u'Error de Datos',u'La cantidad a creditar no puede ser mayor a la de la factura base')
                        invoice_line_obj.write(cr, uid, [refund_line.id], {'quantity': returned_qty, 'uos_id': returned_uom.id, 'price_unit': equi_price})
                    elif refund_line.quantity > returned_qty:
                        invoice_line_obj.write(cr, uid, [refund_line.id], {'quantity': returned_qty})
                    elif refund_line.quantity == returned_qty:
                        pass    #Keep quantity
                    else:
                        raise osv.except_osv(u'Error de Datos',u'La cantidad a creditar no puede ser mayor a la de la factura base')
                else:
                    invoice_line_obj.unlink(cr, uid, refund_line.id, context=context)
            # TODO: La funcion button reset taxes no extiste en la version de oodo 9,
            #invoice_obj.button_reset_taxes(cr, uid, [refund_id], context=context)
            #Validate??


            #Make picking if applicable
            pick_id = False
            if nota.make_picking:
                if not nota.warehouse_id:
                    raise osv.except_osv(u'Dato inválido',u'Debe especificar un Almacen para la devolución de stock')

                cr.execute("select id,default_location_dest_id from stock_picking_type where id in \
                              (select return_picking_type_id from stock_picking_type where code = 'outgoing' and return_picking_type_id !=0 and warehouse_id = %s order by sequence limit 1)",(nota.warehouse_id.id,))
                rs = cr.fetchone()
                if rs:
                    picking_type_id = rs[0]
                    location_dest_id = rs[1]
                else:
                    raise osv.except_osv(u'Error de configuración',u"No se encontró un 'Tipo de albarán para devoluciones' para el almacen especificado.")

                pick_obj = self.pool.get('stock.picking')
                partner_obj = self.pool.get('res.partner')
                stock_moves = []
                for prod in nota.product_ids:
                    move_dict = {
                        'product_id': prod.product_id.id,
                        'name': prod.product_id.name,
                        'product_uom_qty': prod.quantity,
                        'product_uom': prod.uom_id.id,
                        # TODO: product_uos no existe el campo en el stock_move
                        #'product_uos': prod.uom_id.id,
                        'location_id': inv_base.partner_id.property_stock_customer and inv_base.partner_id.property_stock_customer.id or partner_obj.default_get(cr, uid, ['property_stock_customer'], context=context)['property_stock_customer'],
                        'location_dest_id': location_dest_id,
                        'picking_type_id': picking_type_id,
                        'warehouse_id': nota.warehouse_id.id,

                    }
                    stock_moves.append((0,0,move_dict))
                pick_id = pick_obj.create(cr, uid, {
                    'origin': inv_base.name,
                    'partner_id': inv_base.partner_id.id,
                    'picking_type_id': picking_type_id,
                    'company_id': inv_base.company_id.id,
                    'move_type': 'direct',
                    'location_id': inv_base.partner_id.property_stock_customer and inv_base.partner_id.property_stock_customer.id or partner_obj.default_get(cr, uid, ['property_stock_customer'], context=context)['property_stock_customer'],
                    'location_dest_id': location_dest_id,
                    'note': ('Devolucion por Nota de credito sobre %s') % (str(strip_accents(inv_base.number)),),
                    # TODO: el campo invoice state no existe en el adddon stock account de la version 9
                    #'invoice_state': 'none',
                    'move_lines': stock_moves,
                }, context=context)

                pick_obj.action_confirm(cr, uid, [pick_id], context=context)
                pick_obj.action_assign(cr, uid, [pick_id], context=context)

            #Get Dosificación
            dosif_id = False
            dosif_users_pool=self.pool.get('poi_bol_base.cc_dosif.users')
            dosif_users_ids=dosif_users_pool.search(cr, uid, [('user_id','=',uid),('user_default','=',True)])
            if dosif_users_ids:
                for dosif_users in dosif_users_pool.browse(cr, uid, dosif_users_ids):
                    if dosif_users.dosif_id.activa and dosif_users.dosif_id.applies == 'out_refund':
                        dosif_id = dosif_users.dosif_id.id
            #Update key values on refund
            invoice_obj.write(cr, uid, [refund_id], {'note_from_id': inv_id, 'tipo_fac': '6', 'estado_fac': 'V', 'cc_dos': dosif_id, 'picking_id': pick_id})

        dummy, view_res = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'invoice_form')
        return {
            'name': 'Nota de Crédito',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_res,
            'res_model': 'account.invoice',
            'domain': [('type','=','out_refund'),('note_from_id','=',inv_id)],
            'context': context,
            'res_id': refund_id,
            'type': 'ir.actions.act_window',
        }

class nota_credito_items(osv.TransientModel):

    _name = 'poi_bol.nota.wizard.line'
    _description = 'Productos a creditar'

    _columns = {
        'wizard_id': fields.many2one('poi_bol.nota.wizard', required=True, ondelete='cascade'),
        'product_id': fields.many2one('product.product', string='Producto', required=True),
        'uom_id': fields.many2one('product.uom', string='UdM'),
        'quantity': fields.float('Cantidad', digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
    }
