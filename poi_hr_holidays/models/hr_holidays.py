# ©  2011,2013 Michael Telahun Makonnen <mmakonnen@gmail.com>
# ©  2014 initOS GmbH & Co. KG <http://www.initos.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api, _
from datetime import datetime, date

class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    @api.multi
    def get_days(self, employee_id):
        days = 0
        now = datetime.now()
        current_year = now.year
        date_entry = datetime.strptime(employee_id.date_entry, '%Y-%m-%d').replace(year=current_year)
        date_today = datetime.now()
        date_today = date_today.replace(hour=0, minute=0, second=0, microsecond=0)

        if date_entry == date_today:
            last_date = datetime.strptime(employee_id.date_entry, '%Y-%m-%d')
            last_dif = (date_today - last_date).days
            last_years = int(float(last_dif) / 360)
            if last_years >= 1:
                if last_years >= 1 and last_years <= 4:
                    days = 15
                if last_years >= 5 and last_years <= 9:
                    days = 20
                if last_years >= 10:
                    days = 30
        return days

    @api.model
    def update_vacations_days(self):
        emp_obj = self.env['hr.employee']
        type_obj = self.env['hr.holidays.status']
        status_ids = type_obj.search([('limit', '=', False), ('name', '=', 'Dias de Vacacion')])
        status_id = status_ids and status_ids[0] or False
        for e in emp_obj.search([('active','=',True)]):
            if e.date_entry:
                days = self.get_days(e)
                if days > 0:
                    vals = {
                        'name': _('Allocation for %s') % e.name,
                        'employee_id': e.id,
                        'holiday_status_id': status_id.id,
                        'type': 'add',
                        'holiday_type': 'employee',
                        'number_of_days_temp': days,
                    }
                    leave_id = self.create(vals)
                    leave_id.signal_workflow('confirm')
                    leave_id.signal_workflow('validate')
                    leave_id.signal_workflow('second_validate')
