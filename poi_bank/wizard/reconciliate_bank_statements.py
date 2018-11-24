##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2013 Poiesis Consulting (<http://www.poiesisconsulting.com>).
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


from openerp import models, fields, api, _
from openerp import tools
from openerp.osv.orm import MetaModel, Model, TransientModel, AbstractModel
from openerp.exceptions import Warning
import babel.dates
import datetime
import calendar
import openerp.exceptions
from openerp.tools.translate import _

class ReconciliateBankStatementsWizard(models.TransientModel):
    """
    For Reporte de Lista de Productos
    """
    _name = "reconciliate.bank.statements.wizard"
    _description = "Wizard to Specify some Banks"

    bank_account_ids = fields.Many2many('res.bank.account','wizard_bank_statements_rel','wizard_id','bank_account_id','Bank accounts')


    def view_lines_to_reconciliate(self, cr, uid, ids, context=None):

        mod_obj = self.pool.get('ir.model.data')

        context_report = {}
        domain_report = []

        for wiz in self.browse(cr, uid, ids, context):

            ####################Reporte Historial Compras ############################################

            if not wiz.product_id and not wiz.location_id:
                domain_report = []

            if not wiz.product_id and wiz.location_id:
                domain_report = [['location_id', '=', wiz.location_id.id]]

            if wiz.product_id and not wiz.location_id:
                domain_report = [['product_id', '=', wiz.product_id]]

                # else:
                # domain_report=[['fecha', '>=', wiz.date_from], ['fecha', '<=', wiz.date_to]]

                # context_report['header_data']={'date_from':wiz.date_from,
                # 'date_to':wiz.date_to}

            context_report['search_default_group_producto'] = 1

        tree_res = mod_obj.get_object_reference(cr, uid, 'poi_x_ajvierci', 'poi_report_history_purchase')
        tree_id = tree_res and tree_res[1] or False

        graph_res = mod_obj.get_object_reference(cr, uid, 'poi_x_ajvierci', 'view_history_purchase_graph')
        graph_id = graph_res and graph_res[1] or False

        win_obj = self.pool.get('ir.actions.act_window')
        res = win_obj.for_xml_id(cr, uid, 'poi_x_ajvierci', 'action_poi_reporte_hpurchase_tree', context)
        res['domain'] = str(domain_report)
        res['context'] = context_report
        return res



class ReconciliationAssistant(models.TransientModel):
    _name = 'reconciliation.assistant'
    _description = 'Place where all the Bank Statements Will be conciliated'


    st_lines = fields.One2many('ra.statement.lines','assistant_id','Statement Lines')
    mv_lines = fields.One2many('ra.move.lines','assistant_id','Move Lines')

    @api.one
    @api.depends('st_lines')
    def _get_st_total(self):
        total = 0.0
        for s in self.st_lines:
            if s.to_reconcile:
                total+=s.amount
        self.st_total = total

    @api.one
    @api.depends('mv_lines')
    def _get_mv_total(self):
        total = 0.0
        for m in self.mv_lines:
            if m.to_reconcile:
                total += m.amount
        self.mv_total = total

    st_total = fields.Float('Statement Total', compute=_get_st_total)
    mv_total = fields.Float('Moves Total', compute=_get_mv_total)



    def _prereconciliate_automatic(self, st_lines, mv_lines):
        prereconciled = [] #Dictionaries with {'st_lines': [], 'mv_lines': []}
        st_lines_orphan = []
        mv_lines_orphan = []

        st_lines_prereconciled = []
        mv_lines_prereconciled = []

        st_ids_reconciled = []
        mv_ids_reconciled = []

        for st in st_lines:
            new_test = True
            for mv in mv_lines:
                if st.id not in st_ids_reconciled and mv.id not in mv_ids_reconciled and st.bank_account_id and mv.bank_account_id and st.bank_account_id.id == mv.bank_account_id.id \
                        and st.amount == mv.debit - mv.credit:
                    st_lines_prereconciled.append(st)
                    mv_lines_prereconciled.append(mv)

                    st_ids_reconciled.append(st.id)
                    mv_ids_reconciled.append(mv.id)

        for st in st_lines:
            if st.id not in st_ids_reconciled:
                st_lines_orphan.append(st)

        for mv in mv_lines:
            if mv.id not in mv_ids_reconciled:
                mv_lines_orphan.append(mv)

        return {'st_lines_prereconciled': st_lines_prereconciled,
                'mv_lines_prereconciled': mv_lines_prereconciled,
                'st_lines_orphan': st_lines_orphan,
                'mv_lines_orphan': mv_lines_orphan}


    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(ReconciliationAssistant, self).default_get(cr, uid, fields, context=context)
        active_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        #Objetos
        st_obj = self.pool.get('account.bank.statement.line')
        mv_obj = self.pool.get('account.move.line')

        st_lines = []
        mv_lines = []

        if active_model == 'reconciliation.assistant':
            st_domain = [('bank_reconcile_id','=',False),('bank_account_id','!=',False)]
            mv_domain = [('bank_reconcile_id', '=', False), ('bank_account_id', '!=', False)]

            st_ids = st_obj.search(cr, uid, st_domain)
            mv_ids = mv_obj.search(cr, uid, mv_domain)
            st_lines = st_obj.browse(cr, uid, st_ids)
            mv_lines = mv_obj.browse(cr, uid, mv_ids)


        res2 = self._prereconciliate_automatic(st_lines, mv_lines)

        ast_lines = []
        amv_lines = []


        if res2.get('st_lines_prereconciled'):
            for pst in res2.get('st_lines_prereconciled'):
                pst_item = {
                    'to_reconcile': True,
                    'bank_account_id': pst.bank_account_id.id,
                    'st_id': pst.id,
                    'ref': pst.ref,
                    'name': pst.name,
                    'amount': pst.amount,
                    'comment': pst.bank_reconcile_comment,
                }
                ast_lines.append(pst_item)


        if res2.get('mv_lines_prereconciled'):
            for pmv in res2.get('mv_lines_prereconciled'):
                pmv_item = {
                    'to_reconcile': True,
                    'bank_account_id': pmv.bank_account_id.id,
                    'mv_id': pmv.id,
                    'ref': pmv.move_id.ref,
                    'name': pmv.name,
                    'amount': pmv.debit - pmv.credit,
                    'comment': pmv.bank_reconcile_comment
                }
                amv_lines.append(pmv_item)

        if res2.get('st_lines_orphan'):
            for ost in res2.get('st_lines_orphan'):
                ost_item = {
                    'bank_account_id': ost.bank_account_id.id,
                    'st_id': ost.id,
                    'ref': ost.ref,
                    'name': ost.name,
                    'amount': ost.amount,
                    'comment': ost.bank_reconcile_comment,
                }
                ast_lines.append(ost_item)

        if res2.get('mv_lines_orphan'):
            for omv in res2.get('mv_lines_orphan'):
                omv_item = {
                    'bank_account_id': omv.bank_account_id.id,
                    'mv_id': omv.id,
                    'ref': omv.move_id.ref,
                    'name': omv.name,
                    'amount': omv.debit - omv.credit,
                    'comment': omv.bank_reconcile_comment
                }
                amv_lines.append(omv_item)

        res.update(st_lines=ast_lines)
        res.update(mv_lines=amv_lines)

        return res

    @api.one
    def reconciliate_lines(self):
        mv_total = 0.0
        st_total = 0.0
        for m in self.mv_lines:
            if m.to_reconcile:
                mv_total += m.amount

        for s in self.st_lines:
            if s.to_reconcile:
                st_total += s.amount

        if mv_total != st_total:
            raise Warning(_('To reconcilate those columns values must match'))

        if mv_total != 0.0 and st_total != 0.0:
            bank_reconcile_name = ''
            for st in self.st_lines:
                if st.to_reconcile:
                    if bank_reconcile_name != '':
                        bank_reconcile_name += ' - '+st.name
                    else:
                        bank_reconcile_name = st.name
            bank_reconcile_obj = self.env['account.bank.statement.reconcile']
            bank_reconcile_id = bank_reconcile_obj.create({'name': bank_reconcile_name})

            for r_st in self.st_lines:
                if r_st.to_reconcile:
                    r_st.st_id.write({'bank_reconcile_id': bank_reconcile_id.id})
                    r_st.unlink()
            for r_mv in self.mv_lines:
                if r_mv.to_reconcile:
                    r_mv.mv_id.write({'bank_reconcile_id': bank_reconcile_id.id})
                    r_mv.unlink()

        return True



class RAStatementLines(models.TransientModel):
    _name = 'ra.statement.lines'

    assistant_id = fields.Many2one('reconciliation.assistant','Assistant')
    st_id = fields.Many2one('account.bank.statement.line', 'Statement Line ID')
    to_reconcile = fields.Boolean('To Reconcile')
    bank_account_id = fields.Many2one('res.bank.account', string='Bank Account')
    ref = fields.Char('Ref')
    name = fields.Char('Description')
    amount = fields.Float('Amount')
    comment = fields.Char('Comment')

    @api.onchange('comment')
    def _onchange_comment(self):
        self.st_id.write({'bank_reconcile_comment': self.comment})
        self.env.cr.commit()


class RAMoveLines(models.TransientModel):
    _name = 'ra.move.lines'

    assistant_id = fields.Many2one('reconciliation.assistant', 'Assistant')
    mv_id = fields.Many2one('account.move.line', 'Move Line ID')
    to_reconcile = fields.Boolean('To Reconcile')
    bank_account_id = fields.Many2one('res.bank.account', string='Bank Account')
    ref = fields.Char('Ref')
    name = fields.Char('Description')
    amount = fields.Float('Amount')
    comment = fields.Char('Comment')

    @api.onchange('comment')
    def _onchange_comment(self):
        self.mv_id.write({'bank_reconcile_comment': self.comment})
        self.env.cr.commit()


