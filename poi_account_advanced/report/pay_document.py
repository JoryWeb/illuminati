#!/usr/bin/env python
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Poiesis Consulting (<http://www.poiesisconsulting.com>).
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

from openerp import api, models
from openerp.osv import osv
from openerp.addons.poi_bol_base.models.amount_to_text_es import to_word

class report_pay_document_p(models.AbstractModel):
    _name = 'report.poi_account_advanced.pay_document_p'
    
    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('poi_account_advanced.pay_document_p')
        currency_id=self.env['res.currency'].search([('name','=','USD')])
        docs = self.env[report.model].browse(self._ids)

        moneda = docs.journal_id.display_name
        lon = len(moneda)
        moneda = moneda[lon-4:lon-1]
        if moneda == 'BOB':
            moneda = 'Bolivianos'
        elif moneda == 'USD':
            moneda = 'Dolares'
        else:
            moneda = ''

        if docs:
            sql = """ select rate 
                from  res_currency_rate
                where currency_id = """+ str(currency_id.id) +"""
                order by name desc 
                """
            self.env.cr.execute(sql)
            tc = self.env.cr.fetchall()[0][0]
        cu = self.env['res.currency.rate'].search([('currency_id', '=',currency_id.id), ('name','<=', docs.date)], order="name desc")
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self.env[report.model].browse(self._ids),
            'moneda': moneda,
            'tc': tc,
        }

        return report_obj.render('poi_account_advanced.pay_document_p', docargs)
