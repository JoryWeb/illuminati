# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from openerp import models, fields, api, _
from datetime import datetime, timedelta


class PoiPrevisionInsumosWizard(models.TransientModel):

    _name = 'poi.prevision.insumos.wizard'

    date_from = fields.Date('Fecha Desde', readonly=False, required=True)
    date_to = fields.Date('Fecha Hasta', readonly=False, default=fields.Datetime.now)

    @api.multi
    def open_table(self):
        data = self.read()[0]
        if data['date_from']:
            date_from = str(data['date_from'])
        else:
            date_from = datetime.now()

        if data['date_to']:
            date_to = str(data['date_to'])
        context_report = {'group_by': ['location_id','product_id']}
        name_context = ""
        domain_report = [['date', '<=', date_to], ['date', '>=', date_from]]
        name_context += " Desde: %s | " % (datetime.strptime(data['date_from'], '%Y-%m-%d')).strftime("%d-%m-%Y")
        name_context += " Hasta: %s " % (datetime.strptime(data['date_to'], '%Y-%m-%d')).strftime("%d-%m-%Y")
        data_obj = self.pool.get('ir.model.data')
        model_data_id = self.env['ir.model.data']._get_id('poi_procurement_sale_forecast',
                                                          'view_poi_prevision_insumos_report_tree')
        res_id = self.env['ir.model.data'].browse(model_data_id).res_id
        return {
            'domain': str(domain_report),
            'name': _('Proyección de Stock'),
            'view_mode': 'tree',
            'view_type': 'form',
            'nodestroy': True,
            'res_model': 'poi.prevision.insumos.report',
            'view_id': res_id,
            'context': context_report,
            'type': 'ir.actions.act_window'
        }
