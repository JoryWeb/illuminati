# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time

from odoo import models, fields, api, _, tools
from datetime import datetime

class PoiReportKardexChasisWizard(models.TransientModel):
    """
    Para reporte de Kardex Valorado Chasis
    """
    _name = "poi.report.kardex.chasis.wizard"
    _description = "Reporte de Kardex de Inventarios"

    #product_id = fields.Many2one('product.product', string='Producto', required=True)
    #location_id = fields.Many2one('stock.location', string=u'Ubicación', required=True)
    lot_id = fields.Many2one('stock.production.lot', string='Lote/chasis', required=False)
    #date_from = fields.Date(string='Desde:', size=64, required=True, default=lambda *a: time.strftime('%Y-%m-%d'))
    date_to = fields.Date(string='Hasta', size=64, required=True, default=lambda *a: time.strftime('%Y-%m-%d'))
    ufv_value = fields.Boolean("Ver actualización UFV")
    @api.multi
    def open_table(self):
        data = self.read()[0]
        #if data['date_from']:
        #    date_from = str(data['date_from'])+" 00:00:00"
        if data['lot_id']:
            lot_id = data['lot_id']

        if data['date_to']:
            date_to = str(data['date_to'])

        if data['ufv_value']:
            ufv_value = str(data['ufv_value'])

        self.env['poi.report.kardex.chasis'].init(date_to=date_to, lot_id=lot_id[0])
        context_report = {}
        domain_report = []
        name_context = ""
        #domain_report = [['date', '<=', date_to]]
        name_context += " Hasta: %s " % (datetime.strptime(data['date_to'],'%Y-%m-%d')).strftime("%d-%m-%Y")
        data_obj = self.pool.get('ir.model.data')
        model_data_id = self.env['ir.model.data']._get_id('poi_x_toyosa', 'poi_report_kardex_chasis_tree')
        res_id = self.env['ir.model.data'].browse(model_data_id).res_id
        return {
            #'domain': str(domain_report),
            'name': _('Kardex Chasis Resumen'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'poi.report.kardex.chasis',
            'view_id': res_id,
            'context': context_report,
            'type': 'ir.actions.act_window'
        }

    @api.multi
    def print_kardex_product_report(self):
        data = {}
        data['form'] = self.read(['product_id', 'location_id', 'lot_id', 'date_from', 'date_to'])[0]
        for field in ['product_id', 'location_id', 'lot_id', 'date_from', 'date_to']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        return self._print_report(data)

    def _print_report(self, data,):
        data['form'].update(self.read(['product_id', 'location_id', 'lot_id', 'date_from', 'date_to'])[0])
        return self.env['report'].get_action(self, 'poi_kardex_valorado_chasis.report_kardex', data=data)

    @api.multi
    def print_kardex_valorado_product_report(self):
        data = {}
        data['form'] = self.read(['product_id', 'location_id', 'lot_id', 'date_from', 'date_to'])[0]
        for field in ['product_id', 'location_id', 'lot_id', 'date_from', 'date_to']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        return self._print_report_valorado(data)

    def _print_report_valorado(self, data, ):
        data['form'].update(self.read(['product_id', 'location_id', 'lot_id', 'date_from', 'date_to'])[0])
        return self.env['report'].get_action(self, 'poi_kardex_valorado_chasis.report_kardex_valorado', data=data)
