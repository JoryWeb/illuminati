from odoo import models, fields, api
from datetime import date, datetime


class DiaryBookWiz(models.TransientModel):
    _name = "diary.book.wiz"

    date = fields.Date('Hasta', default=fields.Date.today(), help="Seleciona todos los Asientos de la Fecha Indicada.", required=True)

    @api.multi
    def action_view_report(self):
        data = {}
        if self.date:
            data.update({'date': self.date})

        return self.env.ref('poi_x_toyosa_report.diary_book').report_action(self, data=data)
