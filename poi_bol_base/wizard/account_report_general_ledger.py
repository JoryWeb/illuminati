
from openerp import fields, models, _
from openerp.exceptions import UserError


class AccountReportGeneralLedger(models.TransientModel):
    _inherit = "account.report.general.ledger"
    account_ids = fields.Many2many('account.account', string=u"Cuentas Contables (opcional)")

    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update(self.read(['initial_balance', 'sortby'])[0])
        if data['form'].get('initial_balance') and not data['form'].get('date_from'):
            raise UserError(_("You must define a Start Date"))
        # Se adiciona la opcion de poder seleccionar cuentas contables en el formulario
        account_ids = self.read(['account_ids'])[0]
        if account_ids['account_ids']:
            records = self.env['account.account'].browse(account_ids['account_ids'])
            data['ids'] = account_ids['account_ids']
            self.model = 'account.account'
            self = self.with_context(active_model='account.account')
        else:
            records = self.env[data['model']].browse(data.get('ids', []))
        return self.env['report'].with_context(landscape=True).get_action(records, 'account.report_generalledger', data=data)


class AccountBalanceReport(models.TransientModel):
    _inherit = "account.balance.report"
    _description = 'Trial Balance Report'

    account_ids = fields.Many2many('account.account', string=u"Cuentas Contables (opcional)")

    def _print_report(self, data):
        data = self.pre_print_report(data)
        account_ids = self.read(['account_ids'])[0]
        if account_ids['account_ids']:
            records = self.env['account.account'].browse(account_ids['account_ids'])
            data['ids'] = account_ids['account_ids']
            self.model = 'account.account'
            self = self.with_context(active_model='account.account')
        else:
            records = self.env[data['model']].browse(data.get('ids', []))
        return self.env['report'].get_action(records, 'account.report_trialbalance', data=data)
