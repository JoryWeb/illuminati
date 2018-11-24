#!/usr/bin/env python
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Autor: Nicolas Bustillos
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

from openerp import models, fields, api


class company(models.Model):
    _inherit = 'res.company'

    nit = fields.Char('NIT', size=11, help=u"Número de Identificación Tributaria.")
    razon = fields.Char(u'Razón Social', help=u"Razón Social de la Empresa.")
    actividad = fields.Char(u'Actividad económica', size=256, help=u"Actividad económica según Impuestos Internos.")
    handle_inv_tax_data = fields.Boolean('Gestionar datos impositivos en Facturas',
                                         help="Soporta y valida la imputación de datos impositivos destinados a Libros de Compra y Venta.")
    direct_stock_post = fields.Boolean('Posteo directo de Inventarios',
                                       help="Los asientos generados por movimientos de almacen serán contabilizados de forma directa.")
    allow_invoice_direct = fields.Boolean('Permitir pago directo de Facturas',
                                          help="Habilita la opción de contabilizar el Pago directo de una Factura al momento de confirmarla.")
    allow_invoice_defer = fields.Boolean('Permitir facturas con Fecha anterior',
                                         help="Permite ingresar facturas de venta con una fecha anterior a hoy.")
    fill_second_curr = fields.Boolean('Forzar segunda moneda en Asientos',
                                      help="Para Asientos que usen cuentas con segunda moneda se llenará el monto secundario.")
    currency_id_sec = fields.Many2one('res.currency', 'Moneda Secundaria')
    multi_activity = fields.Boolean('Multiples actividades?',
                                    help=u"Especifica si aplica múltiples Actividades Económicas para esta Compañía")
    company_activity_ids = fields.One2many('company.activity', 'company_id', 'Actividades económicas')

    validate_unique_nit = fields.Selection([
        ('valid', 'Validar Nit/CI en compañia'),
        ('not_valid', 'No validar NIT en compañia')
    ], string="Validación NIT/CI Unicos", default='not_valid',
        help="Es necesario validar el NIT/CI Unicos por compañia")

    # ToDo. Sincronizar cambios en res.partner relacionado a Company!


# LIsta de actividades economicas
class company_activity(models.Model):
    _name = "company.activity"

    name = fields.Char(u'Actividad económica', help=u"Actividad económica según Impuestos Internos.")
    principal = fields.Boolean('Actividad principal',
                               help="Definir si es la actividad principal para la impresión de la factura")
    company_id = fields.Many2one('res.company', 'wizard')


class poi_bol_config(models.TransientModel):
    _inherit = 'res.config.settings'

    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env.user.company_id.id)
    module_poi_pos_bol = fields.Boolean('Punto de Venta',
                                        help="Instalar módulo de adecuación de Punto de Venta localizado para Bolivia")
    module_poi_bol_cc = fields.Boolean('Código de Control',
                                       help="Instalar módulo de adecuación para facturación electronica según norma vigente en Bolivia")
    module_poi_purchase_imports = fields.Boolean('Importaciones',
                                                 help="Instalar módulo de adecuación de Compras para la contabilización de Importaciones según norma vigente en Bolivia")
    module_poi_bol_pay = fields.Boolean('Planillas de RRHH',
                                        help="Instalar módulo de adecuación de Recursos Humanos y su cálculo de planillas según norma vigente en Bolivia")
    module_poi_bol_asset = fields.Boolean('Activos Fijos',
                                          help="Instalar módulo de adecuación Contable para la gestión de Activos Fijos según norma vigente en Bolivia")
    allow_invoice_direct = fields.Boolean('Permitir pago directo de Facturas',
                                          help="Habilita la opción de contabilizar el Pago directo de una Factura al momento de confirmarla.")
    allow_invoice_defer = fields.Boolean(default=lambda self: self.env.user.company_id.allow_invoice_defer == True,
                                         string='Permitir facturas con Fecha anterior',
                                         help="Permite ingresar facturas de venta con una fecha anterior a hoy.")

    allow_invoice_defer_save = fields.Boolean(related='company_id.allow_invoice_defer',
                                              string='Permitir facturas con Fecha anterior',
                                              help="Permite ingresar facturas de venta con una fecha anterior a hoy.")

    direct_stock_post = fields.Boolean('Posteo directo de Inventarios',
                                       help="Los asientos generados por movimientos de almacen serán contabilizados de forma directa.")
    fill_second_curr = fields.Boolean('Forzar segunda moneda en Asientos',
                                      help="Para Asientos que usen cuentas con segunda moneda se llenará el monto secundario.")
    monto_bancarizacion = fields.Integer('Monto de bancarizacion')

    validate_unique_nit = fields.Boolean(u'Validar NIT/CI único',
                                         default=lambda self: self.env.user.company_id.validate_unique_nit == 'valid',
                                         help="Validar que no existan clientes o proveedores con NIT o CI repetidos.")
    validate_nit_ci = fields.Selection(related='company_id.validate_unique_nit',
                                       string="Configuraciones NIT/CI Unicos *")

    @api.multi
    def get_default_monto_bancarizacion(self):
        param = self.env['ir.config_parameter'].get_param('monto_bancarizacion', default=50000)
        return {'monto_bancarizacion': param}

    @api.multi
    def set_monto_bancarizacion(self):
        self.env['ir.config_parameter'].set_param('monto_bancarizacion', self[0].monto_bancarizacion)

    # @api.multi
    # def get_default_validate_unique_nit(self):
    #     param = self.env['ir.config_parameter'].get_param('validate_unique_nit', default='False')
    #     return {'validate_unique_nit': param}
    #
    # @api.multi
    # def set_validate_unique_nit(self):
    #     self.env['ir.config_parameter'].set_param('validate_unique_nit', self[0].validate_unique_nit)

    def set_values(self):
        super(poi_bol_config, self).set_values()
        self.validate_nit_ci = 'valid' if self.validate_unique_nit else 'not_valid'
        self.allow_invoice_defer_save = True if self.allow_invoice_defer else False
