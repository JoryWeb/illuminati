##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Poiesis Consulting
#    autor: Nicolas Bustillos
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


from openerp.osv import fields,osv
import openerp.tools
import openerp.addons.decimal_precision as dp

import time

class poi_libro_mayor (osv.Model):
    _name = 'poi.cuadre.account.module'
    _description = "Cuadre Contable Modular"
    _order = 'date_move,id'
    _auto = False

    _columns = {
               'check': fields.char('VoBo'),
               'name': fields.char('Glosa', size=64, readonly=True),
               'move_id': fields.many2one('account.move', string='Asiento', readonly=True),
               'account_id': fields.many2one('account.account', string='Cuenta', readonly=True),
               'account_type': fields.char('Tipo Cuenta', readonly=True),
               'journal_id': fields.many2one('account.journal', string='Diario', readonly=True),
               'period_id': fields.many2one('account.period', string=u'Período', readonly=True),
               'date_move': fields.date('Fecha Asiento', readonly=True),
               'partner_id': fields.many2one('res.partner', string='Socio', readonly=True),
               'state': fields.char('Estado', readonly=True),
               'type_trans': fields.selection([('out_invoice','Factura de venta'),('in_invoice','Factura de compra'),('out_refund','Rectificación venta'),('in_refund','Rectificación compra'),('receipt','Pago cliente'),('payment','Pago proveedor'),('statement','Registro Caja'),('picking','Albaran'),('_no_module_','x_No Modular_x')], string=u'Transacción', readonly=True),
               'date_trans': fields.date('Fecha', readonly=True),
               'invoice_id': fields.many2one('account.invoice', string=u'Factura', readonly=True),
               'voucher_id': fields.many2one('account.voucher', string=u'Pago', readonly=True),
               'statement_id': fields.many2one('account.bank.statement', string=u'Registro Caja', readonly=True),
               'picking_id': fields.many2one('stock.picking', string=u'Albarán', readonly=True),
               'name_trans': fields.char('Transacción Nr.', readonly=True),
               'reconcile_ref': fields.char('Reconcilio', readonly=True),
               'debit': fields.float('Debe', digits_compute=dp.get_precision('Account'), readonly=True),
               'credit': fields.float('Haber', digits_compute=dp.get_precision('Account'), readonly=True),
               'saldo': fields.float('Saldo', digits_compute=dp.get_precision('Account'), readonly=True),

    }

    def init(self, cr):

        view_query = """
            CREATE OR REPLACE VIEW poi_cuadre_account_module AS (
                select case when aml.date not between ap.date_start and ap.date_stop then 'X Error Asiento Fecha<>Periodo (!)'
                          when ai.date_invoice not between iap.date_start and iap.date_stop then 'X Error Factura Fecha<>Periodo (!)'
                          when aml.period_id != (case when ai.type is not null then ai.period_id when av.id is not null then av.period_id when abs.id is not null then abs.period_id else aml.period_id end) then 'X Error Periodos Asiento<>Trans (!)'
                          when extract('month' from aml.date) != (case when ai.type is not null then extract('month' from ai.date_invoice) when av.id is not null then extract('month' from av.date) when abs.id is not null then extract('month' from abs.date) else extract('month' from aml.date) end) then 'X Error Fechas Asiento<>Trans (!)'
                          else 'OK' end as check
                    ,aml.id as id,am.id as move_id,am.journal_id,ap.id as period_id,ap.name as period_name,aml.date as date_move,aml.name, aa.id as account_id, aa.name as account_name, aa.type as account_type, aml.debit, aml.credit,round(aml.debit - aml.credit,2) as saldo
                    ,case when ai.type is not null then ai.state when av.id is not null then av.state when abs.id is not null then abs.state when sp.id is not null then sp.state else am.state end as state
                    ,case when ai.type is not null then ai.number when av.id is not null then av.number when abs.id is not null then abs.name when sp.id is not null then sp.name else '' end as name_trans
                    ,case when ai.type is not null then ai.type when av.id is not null then av.type when abs.id is not null then 'statement' when sp.id is not null then 'picking' else '_no_module_' end as type_trans
                    ,case when ai.type is not null then ai.date_invoice when av.id is not null then av.date when abs.id is not null then abs.date when sp.id is not null then sp.date_done::date else NULL end as date_trans, rp.id as partner_id,rp.name as partner_name, ai.id as invoice_id,ai.number, av.id as voucher_id, abs.id as statement_id, sp.id as picking_id
                    ,aml.reconcile_id, aml.reconcile_ref, aml.reconcile_partial_id
                from account_move_line aml inner join account_move am on am.id=aml.move_id inner join account_account aa on aa.id=aml.account_id left outer join res_partner rp on rp.id=aml.partner_id left outer join account_period ap on ap.id=aml.period_id
                        left outer join account_invoice ai on aml.move_id=ai.move_id
                        left outer join account_period iap on iap.id=ai.period_id
                        left outer join account_voucher av on aml.move_id=av.move_id
                        left outer join account_bank_statement abs on abs.id=aml.statement_id
                        left outer join stock_picking sp on sp.name=aml.ref
                where am.state in ('posted')
                order by aml.date,aml.id
            )
        """

        openerp.tools.sql.drop_view_if_exists(cr, 'poi_cuadre_account_module')

        cr.execute(view_query)

    def launch_move(self, cr, uid, ids, context=None):

        line = self.browse(cr, uid, ids[0], context=context)

        action_form = {
            'name': "Asiento contable",
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'account.move',
            'res_id': int(line.move_id.id),
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': str([]),
            'target': 'new',
            'context': context,
        }
        return action_form

    def launch_form(self, cr, uid, ids, context=None):

        line = self.browse(cr, uid, ids[0], context=context)

        if line.type_trans in ('out_invoice','out_refund'):
            name = "Factura"
            model = 'account.invoice'
            res = line.invoice_id.id
        elif line.type_trans in ('in_invoice','in_refund'):
            name = "Factura de compra"
            model = 'account.invoice'
            res = line.invoice_id.id
        elif line.type_trans in ('payment','receipt'):
            name = "Pago"
            model = 'account.voucher'
            res = line.voucher_id.id
        elif line.type_trans in ('statement'):
            name = "Registro de caja"
            model = 'account.bank.statement'
            res = line.statement_id.id
        elif line.type_trans in ('picking'):
            name = "Albaran"
            model = 'stock.picking'
            res = line.picking_id.id
        else:
            return False
        action_form = {
            'name': name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': model,
            'res_id': int(res),
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': str([]),
            'target': 'new',
            'context': context,
        }
        return action_form

