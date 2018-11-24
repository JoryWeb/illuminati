# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _, tools
from odoo.tools.translate import _
import odoo.addons.decimal_precision as dp
from datetime import datetime


class HrVoucherConfig(models.Model):
    _name = "hr.voucher.config"
    _description = "Configuracion Boleta de Pago"

    name = fields.Char(string="Nombre")
    sequence = fields.Integer('Secuencia')
    width = fields.Integer('Ancho', default=6 ,help="Ancho de la Columna Maximo valor 12")

    line_ids = fields.One2many('hr.voucher.config.line', 'config_id', string="Lienas de Configuracion")


class HrVoucherConfigLine(models.Model):
    _name = "hr.voucher.config.line"
    _description = "Configuracion Boleta de Pago"

    config_id = fields.Many2one('hr.voucher.config', string="Configuracion", ondelete='cascade', index=True)
    name = fields.Char(string="Nombre en Reporte")
    salary_rules_id = fields.Many2one('hr.salary.rule', 'Regla Salarial')
    sequence = fields.Integer('Secuencia')
