import logging
from odoo import api, fields, models


_logger = logging.getLogger(__name__)


class SaleReportConfig(models.Model):
    _name = 'sale.report.config'
    _description = 'Conceptos de ventas para reportes'

    name = fields.Char('Descripcion')
    report_id = fields.Many2one('ir.actions.report.xml', 'Reporte',  domain=[('model','in',['account.invoice', 'sale.order'])])
    item_ids = fields.One2many('sale.report.items', 'config_id', 'Items')

class SaleReportItems(models.Model):
    _name = 'sale.report.items'
    _description = 'Conceptos de ventas para reportes'
    _order = "sequence, group_id"

    config_id = fields.Many2one('sale.report.config', 'Configuracion')
    name = fields.Char('Nombre en Reporte')
    item_id = fields.Many2one('atributo.nombre.toyosa', 'Atributo')
    default = fields.Char('Valor por Defecto', default="0")
    group_id = fields.Many2one('sale.report.group', 'Agrupador')
    sequence = fields.Integer('Secuencia')


class SaleReportGroup(models.Model):
    _name = 'sale.report.group'
    _description = 'Agroupadores'
    _order = "sequence"

    name = fields.Char('Titulo')
    sequence = fields.Integer('Secuencia')
