# © 2013 Joaquín Gutierrez
# © 2014-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3


from openerp import models, fields, exceptions, api, _
import openerp.addons.decimal_precision as dp

STATE = [
    ('draft', 'Original'),
    ('cancel', 'Cancelado'),
    ('done', 'Revisado'),
]

class OriginalAnnualPlan(models.Model):
    _name = "poi.original.annual.plan"
    _description = "Plan Anual de Ventas"
    _order = 'name desc'

    name = fields.Char(string='Distribution number', required=True,
                       select=True, default='/')

    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', required=True,
        default=(lambda self: self.env['res.company']._company_default_get(
            'poi.original.annual.plan')))

    state = fields.Selection(STATE, string='Status', readonly=True, default='draft')
    date = fields.Date("Fecha")
    user_id = fields.Many2one('res.users', string='Creador', index=True, track_visibility='onchange',
                              default=lambda self: self.env.user)

    date_revisado = fields.Date("Fecha Revisado")
    note = fields.Text("Notas")
    annual_plan_lines = fields.One2many(
        comodel_name='poi.original.annual.plan.line', ondelete="cascade",
        inverse_name='annual_plan', string='Lineas de Pedido')

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
           vals['name'] = self.env['ir.sequence'].next_by_code('poi.original.annual.plan')
        res_id = super(OriginalAnnualPlan, self).create(vals)
        return res_id

    @api.multi
    def action_calculate(self):
        for distribution in self:
            # Check expense lines for amount 0
            if any([not x.expense_amount for x in distribution.expense_lines]):
                raise exceptions.Warning(
                    _('Please enter an amount for all the expenses'))
            # Check if exist lines in distribution
            if not distribution.cost_lines:
                raise exceptions.Warning(
                    _('There is no picking lines in the distribution'))
            # Calculating expense line
            for cost_line in distribution.cost_lines:
                cost_line.expense_lines.unlink()
                expense_lines = []
                for expense in distribution.expense_lines:
                    if (expense.affected_lines and
                            cost_line not in expense.affected_lines):
                        continue
                    expense_lines.append(
                        self._prepare_expense_line(expense, cost_line))
                cost_line.expense_lines = [(0, 0, x) for x in expense_lines]
            distribution.state = 'calculated'
        return True

    @api.one
    def action_done(self):
        for line in self.cost_lines:
            if self.cost_update_type == 'direct':
                line.move_id.quant_ids._price_update(line.standard_price_new)
                self._product_price_update(
                    line.move_id, line.standard_price_new)
                line.move_id.product_price_update_after_done()
        self.state = 'done'

    @api.multi
    def action_draft(self):
        self.write({'state': 'draft'})
        return True

    @api.one
    def action_cancel(self):
        for line in self.cost_lines:
            if self.cost_update_type == 'direct':
                if self.currency_id.compare_amounts(
                        line.move_id.quant_ids[0].cost,
                        line.standard_price_new) != 0:
                    raise exceptions.Warning(
                        _('Cost update cannot be undone because there has '
                          'been a later update. Restore correct price and try '
                          'again.'))
                line.move_id.quant_ids._price_update(line.standard_price_old)
                self._product_price_update(
                    line.move_id, line.standard_price_old)
                line.move_id.product_price_update_after_done()
        self.state = 'draft'

    @api.multi
    def action_open_report_pivot(self):
        '''
        Solo se requiere la accion y el domain para mostrar el reportes
        '''
        action = self.env.ref('poi_original_annual_plan.action_original_annual_plan_line')
        result = action.read()[0]

        result['context'] = {}
        result['domain'] = "[('annual_plan','=', " + str(self.id) + ")]"
        return result

    @api.multi
    def action_open_report_line(self):
        '''
        This function returns an action that display existing picking orders of given purchase order ids.
        When only one found, show the picking immediately.
        '''
        action = self.env.ref('poi_original_annual_plan.action_original_annual_plan_line_graph')
        result = action.read()[0]
        result['context'] = {'search_default_group_fecha':1, 'graph_mode':'line', 'graph_measure':'cantidad_revisada'}
        result['domain'] = "[('annual_plan','=', " + str(self.id) + ")]"
        #res = self.env.ref('original_annual_plan.view_original_annual_plan_line_graph', False)
        #result['views'] = [(res and res.id or False, 'form')]
        return result

class OriginalAnnualPlanLine(models.Model):
    _name = "poi.original.annual.plan.line"
    _description = "Lineas de Plan anual"

    name = fields.Char(string=u'Descripción')
    annual_plan = fields.Many2one(
        comodel_name='poi.original.annual.plan', string='Plan Anual',
        ondelete='cascade', required=True)
    company_id = fields.Many2one(comodel_name='res.company', string=u'Compañia', required=True)
    project_id = fields.Many2one("account.analytic.account", string=u"Cuenta Analítica")
    modelo = fields.Many2one("modelo.toyosa", string=u"Modelo")
    fecha = fields.Date("Fecha")
    cantidad_prevista = fields.Float(string='Cantidad Prevista', digits_compute=dp.get_precision('Product Unit of Measure'))
    cantidad_revisada = fields.Float(string='Cantidad Revisada', digits_compute=dp.get_precision('Product Unit of Measure'))




