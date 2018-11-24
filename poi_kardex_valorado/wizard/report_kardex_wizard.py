# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time

from odoo import models, fields, api, _, tools
from datetime import datetime

class PoiReportKardexWizard(models.TransientModel):
    """
    For Reporte kardex valorado
    """
    _name = "poi.report.kardex.wizard"
    _description = "Reporte de Kardex de Inventarios"

    product_id = fields.Many2one('product.product', string='Producto', required=True)
    location_id = fields.Many2one('stock.location', string=u'Ubicación', required=True)
    date_from = fields.Date(string='Desde:', size=64, required=True, default=lambda *a: time.strftime('%Y-%m-%d'))
    date_to = fields.Date(string='Hasta', size=64, required=True, default=lambda *a: time.strftime('%Y-%m-%d'))

    @api.multi
    def open_table(self):
        data = self.read()[0]
        if data['date_from']:
            date_from = str(data['date_from'])+" 00:00:00"
        if data['date_to']:
            date_to = str(data['date_to'])+" 23:59:59"

        if data['product_id']:
            product_id = str(data['product_id'][0])

        if data['location_id']:
            location_id = str(data['location_id'][0])


        self.env['poi.report.kardex.inv'].init(date_from=date_from, date_to=date_to, product_id=product_id, location_id=location_id)
        context_report = {}
        domain_report = []
        name_context = ""
        domain_report = [['date', '<=', date_to], ['date', '>=', date_from]]
        name_context += " Desde: %s | " % (datetime.strptime(data['date_from'],'%Y-%m-%d')).strftime("%d-%m-%Y")
        name_context += " Hasta: %s " % (datetime.strptime(data['date_to'],'%Y-%m-%d')).strftime("%d-%m-%Y")
        data_obj = self.pool.get('ir.model.data')
        model_data_id = self.env['ir.model.data']._get_id('poi_kardex_valorado', 'poi_report_kardex_tree')
        res_id = self.env['ir.model.data'].browse(model_data_id).res_id
        return {
            'domain': str(domain_report),
            'name': _('Kardex'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'poi.report.kardex.inv',
            'view_id': res_id,
            'context': context_report,
            'type': 'ir.actions.act_window'
        }

    @api.multi
    def print_kardex_product_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['product_id', 'location_id', 'date_from', 'date_to'])[0]
        return self._print_report(data)

    def _print_report(self, data):
        return self.env.ref('poi_kardex_valorado.action_report_kardex').report_action(self, data=data)

    @api.multi
    def print_kardex_valorado_product_report(self):
        data = {}
        data['form'] = self.read(['product_id', 'location_id', 'date_from', 'date_to'])[0]
        for field in ['product_id', 'location_id', 'date_from', 'date_to']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        return self._print_report_valorado(data)

    def _print_report_valorado(self, data, ):
        data['form'].update(self.read(['product_id', 'location_id', 'date_from', 'date_to'])[0])
        return self.env.ref('poi_kardex_valorado.action_report_kardex_valorado').report_action(self, data=data)
