from odoo import models, fields, api
from datetime import date, datetime
import calendar

class SaleMoveWizard(models.TransientModel):
    _name = "sale.move.wizard"

    @api.model
    def _default_first_day(self):
        today = datetime.strptime(fields.Date.today(), "%Y-%m-%d").date()
        caledar_today = calendar.monthrange(today.year, today.month)
        if today.month == 1:
            before_month = 12
            before_year = today.year - 1
        else:
            before_month = today.month - 1
            before_year = today.year
        if today.month > 9:
            month = str(today.month)
        else:
            month = '0'+str(today.month)
        caledar_before_month = calendar.monthrange(before_year, before_month)
        first_day = str(today.year)+'-'+str(month)+'-01'
        last_day = str(today.year)+'-'+str(month)+'-'+str(caledar_today[1])
        return first_day

    @api.model
    def _default_last_day(self):
        today = datetime.strptime(fields.Date.today(), "%Y-%m-%d").date()
        caledar_today = calendar.monthrange(today.year, today.month)
        if today.month == 1:
            before_month = 12
            before_year = today.year - 1
        else:
            before_month = today.month - 1
            before_year = today.year
        if today.month > 9:
            month = str(today.month)
        else:
            month = '0'+str(today.month)
        caledar_before_month = calendar.monthrange(before_year, before_month)
        first_day = str(today.year)+'-'+str(month)+'-01'
        last_day = str(today.year)+'-'+str(month)+'-'+str(caledar_today[1])
        return last_day


    date_from = fields.Date("Desde", default=lambda self: self._default_first_day(), required=True)
    date_to = fields.Date("Hasta", default=lambda self: self._default_last_day(), required=True)
    # date_cut = fields.Date("Fecha de Corte", default=fields.Date.today(), required=True)


    @api.multi
    def action_view_report(self):
        domain = []
        # if self.date:
        #     domain.append(['date_invoice', '<=', self.date])
        if self.date_from:
            domain.append(['payment_date', '>=' , self.date_from])
        if self.date_to:
            domain.append(['payment_date', '<=', self.date_to])
        return {
            'name': "Movimiento de Ventas",
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'sale.move.report',
            'type': 'ir.actions.act_window',
            'context': {
                'date_cut': self.date_to,
            },
            'domain': domain,
        }
