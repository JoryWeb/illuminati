# © 2014-2015 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    lot_dui_id = fields.Many2one("stock.production.lot", "Serie", states={'draft': [('readonly', False)]}, copy=False,
                                 help="Campo que se pone automaticamente al costear los productos en la carpeta de importaciones")

    picking_ids = fields.Many2many(
        'stock.picking', string='Albaranes',
        copy=False, states={'done': [('readonly', True)]})

    move_line_ids = fields.Many2many(
        'stock.move.line', string='Series',
        copy=False, states={'done': [('readonly', True)]})

    landed_cost_id = fields.Many2one(
        'stock.landed.cost', string='Coste en destino',
        copy=False, states={'done': [('readonly', True)]})

    n_embarque = fields.Char(u"Número de embarque")
    nombre_embarque = fields.Char(u"Nombre de embarque")
    
    @api.multi
    def action_view_quant(self):
        '''
        Refactorizado: Funcion que visualiza reporte de stock por la compra realizada, aplicado solo a series unicas
        '''

        action = self.env.ref('stock.quantsact')
        result = action.read()[0]
        res = self.env.ref('stock.view_stock_quant_tree', False)
        lot_ids = []
        for inv_line in self.invoice_line_ids:
            stock_move = self.env['stock.move'].search([('purchase_line_id', '=', inv_line.purchase_line_id.id)])
            for mov in stock_move:
                for move_l in mov.move_line_ids:
                    lot_ids.append(move_l.lot_id.id)

        result['views'] = [(res and res.id or False, 'tree')]
        result['res_id'] = self.id
        result['domain'] = "[('lot_id','in',[" + ','.join(map(str, lot_ids)) + "])]"
        return result

    @api.multi
    def action_view_invoice(self):
        '''
        Buscar las polizas de importación que esten asignados
        a la carpeta de importaciones
        '''
        lot_ids = []
        invoice_ids = []
        for inv_line in self.invoice_line_ids:
            stock_move = self.env['stock.move'].search([('purchase_line_id', '=', inv_line.purchase_line_id.id)])
            for mov in stock_move:
                for move_l in mov.move_line_ids:
                    lot_ids.append(move_l.lot_id.id)
        sql_query = """
                    select a.account_invoice_id, b.lot_id from account_invoice_stock_picking_rel a
                    inner join stock_move_line b on b.picking_id= a.stock_picking_id
                      inner join account_invoice c on c.id = a.account_invoice_id
                      where c.tipo_fac = '12'
                    """
        params = ()
        sql_query += ' AND b.lot_id IN %s group by a.account_invoice_id, b.lot_id order by b.lot_id'
        params += (tuple(lot_ids),)

        self.env.cr.execute(sql_query, params)
        for line in self.env.cr.dictfetchall():
            invoice_ids.append(line.get('account_invoice_id'))

        sql_query = """ select
                          a.account_invoice_id,
                          b.lot_id
                        from account_invoice_stock_move_line_rel a
                          inner join stock_move_line b on b.id = a.stock_move_line_id
                          inner join account_invoice c on c.id = a.account_invoice_id
                        where c.tipo_fac = '12'
                            """
        params = ()
        sql_query += ' AND b.lot_id IN %s group by a.account_invoice_id, b.lot_id order by b.lot_id'
        params += (tuple(lot_ids),)

        self.env.cr.execute(sql_query, params)
        for line in self.env.cr.dictfetchall():
            invoice_ids.append(line.get('account_invoice_id'))

        inv_ids = list(set(invoice_ids))

        action = self.env.ref('account.action_invoice_tree2')
        result = action.read()[0]
        if len(inv_ids) != 1:
            result['domain'] = "[('id', 'in', [" + ','.join(map(str, inv_ids)) + "])]"
        elif len(inv_ids) == 1:
            res = self.env.ref('account.invoice_supplier_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = inv_ids[0]
        return result

    @api.multi
    def apply_landed_cost(self):
        if not self.journal_id:
            raise UserError(_('Por favor definir el Diario Contable'))

        if not self.state in ('open', 'paid'):
            raise UserError(
                _(u'Antes de Aplicar el gasto la factura tiene que estar en estado válido o pagado'))

        ctx = self._context.copy()

        # Validar que exista algun producto para costeo
        valid_cost = True
        for line_inv in self.invoice_line_ids:
            if line_inv.product_id.landed_cost_ok:
                valid_cost = False

        if valid_cost:
            raise UserError(
                _(u'No existe lineas para costear'))

        if self.landed_cost_id:
            view_id = self.env.ref('stock_landed_costs.view_stock_landed_cost_form').id
            return {
                'name': _('Costos en Destino'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.landed.cost',
                'view_id': view_id,
                'context': ctx,
                'res_id': self.landed_cost_id.id,
                'target': 'new',
            }

        # Ejecutar si tienes costos en destino por picking
        # Evitar que se valore por dos casos en caso de ser ambos no permite generar el coste en destino
        if self.picking_ids and not self.move_line_ids:
            # Verificar si los quants a valorar ya corresponden a
            # Una ubicación de valoración de inventarios
            # 05.02.2017 No es necesario aplicar funcionalidad de transito
            # Odoo aplica las ubicaciónes en transito donde de forma
            # Nativa ya no genera contabilidad y los costos aplicados
            # Al albaran en transito solo genera el asiento contra la cuenta de valoración de las ventas
            # En el entendido que cuando se venda el producto la cuenta de valoración de las ventas se vea afectado tambien
            # for picking in self.pickings_id:
            #     for moves in picking.move_lines:
            #         for quant in moves.quant_ids:
            #             if quant.location_id.usage == 'transit':
            #                 raise UserError(_(
            #                     'No puede aplicar costos al chasis "%s" en la ubicación "%s" ya que es una ubicación de transito') % (
            #                                     quant.lot_id.name, quant.location_id.name))
            #             if self.tipo_fac == '12':
            #                 self.lot_dui_id = quant.lot_id.id

            # Crear cabezara de costos en destinos
            val_landed = {
                'date': self.date,
                'picking_ids': [(6, 0, self.picking_ids.ids)],
                'move_line_ids': [(6, 0, self.move_line_ids.ids)],
                'account_journal_id': self.journal_id.id,
            }
            cost_id = self.env['stock.landed.cost'].create(val_landed)

            for line_inv in self.invoice_line_ids:
                if line_inv.product_id.landed_cost_ok:
                    amount_currency = self.currency_id.compute(line_inv.price_subtotal * line_inv.quantity,
                                                               self.env.user.company_id.currency_id)
                    val_lines_landed = {
                        'cost_id': cost_id.id,
                        'name': line_inv.product_id.name,
                        'product_id': line_inv.product_id.id,
                        'split_method': line_inv.product_id.split_method,
                        'price_unit': amount_currency,
                        'account_id': line_inv.account_id.id and line_inv.product_id.property_account_expense_id.id or line_inv.product_id.categ_id.property_account_expense_categ_id.id,
                        # 'imports_expense': self.id,
                    }
                    self.env['stock.landed.cost.lines'].create(val_lines_landed)
            cost_id.compute_landed_cost()
            cost_id.button_validate()
            self.landed_cost_id = cost_id.id
            # Al generar el costo en destino
            # visualizamos el resultado
            view_id = self.env.ref('stock_landed_costs.view_stock_landed_cost_form').id
            return {
                'name': _('Costos en Destino'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.landed.cost',
                'view_id': view_id,
                'context': ctx,
                'res_id': cost_id.id,
                'target': 'new',
            }

        # Ejecutar si tiene costos en destino por
        # Lote
        elif self.move_line_ids and not self.picking_ids:
            # for quants in self.quants_id:
            #     if quants.location_id.usage == 'transit':
            #         raise UserError(_(
            #             'No puede aplicar costos al chasis "%s" en la ubicación "%s" ya que es una ubicación de transito') % (
            #                         quants.lot_id.name, quants.location_id.name))
            ## Asignar Lote Chasis a Factura DUI
            # for quant in self.quants_id:
            #     if self.invoice_id.tipo_fac == '12':
            #         self.invoice_id.lot_dui_id = quant.lot_id.id
            #         quant.invoice_id = self.invoice_id.id
            # Crear cabezara de costos en destinos
            val_landed = {
                'date': self.date,
                'picking_ids': [(6, 0, self.picking_ids.ids)],
                'move_line_ids': [(6, 0, self.move_line_ids.ids)],
                'account_journal_id': self.journal_id.id,
            }
            cost_id = self.env['stock.landed.cost'].create(val_landed)

            for line_inv in self.invoice_line_ids:
                amount_currency = self.currency_id.compute(line_inv.price_subtotal * line_inv.quantity,
                                                           self.env.user.company_id.currency_id)
                if line_inv.product_id.landed_cost_ok:
                    val_lines_landed = {
                        'cost_id': cost_id.id,
                        'name': line_inv.product_id.name,
                        'product_id': line_inv.product_id.id,
                        'split_method': line_inv.product_id.split_method,
                        'price_unit': amount_currency,
                        'account_id': line_inv.account_id.id and line_inv.product_id.property_account_expense_id.id or line_inv.product_id.categ_id.property_account_expense_categ_id.id,
                    }
                    self.env['stock.landed.cost.lines'].create(val_lines_landed)
            cost_id.compute_landed_cost_moves()
            cost_id.button_validate_moves()
            self.landed_cost_id = cost_id.id

            # Al generar el costo en destino
            # visualizamos el resultado
            view_id = self.env.ref('stock_landed_costs.view_stock_landed_cost_form').id
            return {
                'name': _('Costos en Destino'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.landed.cost',
                'view_id': view_id,
                'context': ctx,
                'res_id': cost_id.id,
                'target': 'new',
            }
        else:
            raise UserError(
                _('No puede aplicar el costeo a un albarán y serie al mismo tiempo!\nSolo debe estar seleccionado uno'))


def _prepare_invoice_line_from_po_line(self, line):
    result = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
    if self.purchase_id.tipo_fac == '3':
        result[
            'account_id'] = line.product_id.property_stock_account_import.id or line.product_id.categ_id.property_stock_account_import_categ_id.id
    return result
