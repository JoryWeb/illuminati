# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _, tools
from datetime import datetime, timedelta


class PoiReportKardexValuationWizard(models.TransientModel):
    """
    For Reporte kardex valorado
    """
    _name = "poi.report.kardex.valuation.wizard"
    _description = "Auditoria de inventarios"

    product_ids = fields.Many2many('product.product', 'poi_product_kardex_valuation_rel', 'wizard_id',
                                   'product_id', string=u'Productos', readonly=False)

    warehouse_ids = fields.Many2many('stock.warehouse', 'poi_warehouse_kardex_valuation_rel', 'wizard_id',
                                     'warehouse_id', string=u'Almacenes', readonly=False)

    date_from = fields.Date('Fecha Desde', readonly=False, required=True)
    date_to = fields.Date('Fecha Hasta', readonly=False, default=fields.Datetime.now)
    cost_method = fields.Selection([('standard', 'Costo Estandar'),
                                    ('average', 'Costo promedio'),
                                    ('real', 'Costo Real(FIFO)')], string=u'Método de Coste',
                              required=True,
                              help="Seleccione el metodo de costeo según configuración de categoria de productos"
                                   "  * Csoto Estandar: El costo no se modifica\n"
                                   "  * Costo promedio: El costo se calcula con cada ingreso de compras o ajustes de Inventarios\n"
                                   "  * Costo Real: Los costos son desigandos por las compras y no recalcula el valor unitario de cada producto (FIFO)")

    @api.onchange('cost_method')
    def onchange_cost_method(self):
        if self.cost_method == 'average':
            prod = self.env['product.product'].search([('categ_id.property_cost_method', '=', 'average')])
            ids = []
            for pr in prod:
                ids.append(pr.id)
            products = {'product_ids': [('id', 'in', ids), ('qty_moves', '>', 0)]}
        elif self.cost_method == 'real':
            prod = self.env['product.product'].search([('categ_id.property_cost_method', '=', 'real')])
            ids = []
            for pr in prod:
                ids.append(pr.id)
            products = {'product_ids': [('cost_method', '=', 'real'), ('qty_moves', '>', 0)]}
        else:
            prod = self.env['product.product'].search([('categ_id.property_cost_method', '=', 'standard')])
            ids = []
            for pr in prod:
                ids.append(pr.id)
            products = {'product_ids': [('cost_method', '=', 'standard'), ('qty_moves', '>', 0)]}
        return {'domain': products}

    @api.multi
    def open_table(self):
        data = self.read()[0]
        if data['date_from']:
            date_from = str(data['date_from']) + " 00:00:00"
        else:
            date_from = datetime.now()

        if data['date_to']:
            date_to = str(data['date_to']) + " 23:59:59"

        product_ids = []
        warehouse_ids = []
        for wizard in self:
            cost_method = wizard.cost_method
            #product_ids = wizard.product_ids.ids
            for product in wizard.product_ids:
                if product.cost_method == cost_method:
                    product_ids.append(product.id)

            warehouse_ids = wizard.warehouse_ids.ids

        if cost_method == 'average':
            self.env['poi.report.kardex.valuation'].init(date_from=date_from, date_to=date_to)
            context_report = {'group_by': 'product_id'}
            domain_report = []
            name_context = ""
            domain_report = [['date', '<=', date_to], ['date', '>=', date_from], ['product_id', 'in', product_ids],
                             ['warehouse_id', 'in', warehouse_ids]]
            name_context += " Desde: %s | " % (datetime.strptime(data['date_from'], '%Y-%m-%d')).strftime("%d-%m-%Y")
            name_context += " Hasta: %s " % (datetime.strptime(data['date_to'], '%Y-%m-%d')).strftime("%d-%m-%Y")
            data_obj = self.pool.get('ir.model.data')
            model_data_id = self.env['ir.model.data']._get_id('poi_kardex_valorado', 'poi_report_kardex_valuation_inh')
            res_id = self.env['ir.model.data'].browse(model_data_id).res_id
            return {
                'domain': str(domain_report),
                'name': _('Auditoría de Inventarios'),
                'view_type': 'form',
                'view_mode': 'tree',
                'nodestroy': True,
                'res_model': 'poi.report.kardex.valuation',
                'view_id': res_id,
                'context': context_report,
                'type': 'ir.actions.act_window'
            }
        elif cost_method in ('real', 'standard'):
            self.env['poi.report.kardex.valuation.real'].init(date_from=date_from, date_to=date_to)
            context_report = {'group_by': 'product_id'}
            domain_report = []
            name_context = ""
            domain_report = [['date', '<=', date_to], ['date', '>=', date_from], ['product_id', 'in', product_ids],
                             ['warehouse_id', 'in', warehouse_ids]]
            name_context += " Desde: %s | " % (datetime.strptime(data['date_from'], '%Y-%m-%d')).strftime("%d-%m-%Y")
            name_context += " Hasta: %s " % (datetime.strptime(data['date_to'], '%Y-%m-%d')).strftime("%d-%m-%Y")
            data_obj = self.pool.get('ir.model.data')
            model_data_id = self.env['ir.model.data']._get_id('poi_kardex_valorado', 'poi_report_kardex_valuation_real_inh')
            res_id = self.env['ir.model.data'].browse(model_data_id).res_id
            return {
                'domain': str(domain_report),
                'name': _('Auditoría de Inventarios Real'),
                'view_mode': 'tree',
                'view_type': 'form',
                'nodestroy': True,
                'res_model': 'poi.report.kardex.valuation.real',
                'view_id': res_id,
                'context': context_report,
                'type': 'ir.actions.act_window'
            }
