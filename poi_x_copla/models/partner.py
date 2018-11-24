# -*- coding: utf-8 -*-

from odoo import api, fields, models, osv, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    date_limit_invoice = fields.Date(string=u'Fecha Límite de Emisión Facturas')
    drivers_license = fields.Char(string=u'Licencia de Conducir')
    business_card = fields.Boolean(string='Tarjeta de Operaciones', default=True, help='')
    casual_permit = fields.Boolean(string='Permiso Casual')
    license_expiration = fields.Date(string=u'Vencimiento Licencia')
    expiration_trading_card = fields.Date(string=u'Vencimiento Tarjeta de operaciones')
    expiration_permit_provider = fields.Date(string=u'Vencimiento Permiso proveedor')
    days_rolear = fields.Integer(string=u'Dias para rolear')
    m_approximate_day = fields.Float(string=u'Multa Aproximada por dia')
    days_free_stay = fields.Integer(string=u'Dias libres de estadia')
    daily_rate_container = fields.Integer(string=u'Tarifa diaria por contenedor')
    observation1 = fields.Char(string=u'Observaciones')
    observation2 = fields.Char(string=u'Observaciones')
    observation3 = fields.Char(string=u'Observaciones')
    observation4 = fields.Char(string=u'Observaciones')
    placa = fields.Char(string=u'placa')
    propietario = fields.Char(string=u'propietario')
    conductor = fields.Char(string=u'conductor')
    codigo = fields.Char(string=u'codigo')
    capacidad = fields.Char(string=u'capacidad')
    dato1 = fields.Char(string=u'Dato1')
    dato2 = fields.Char(string=u'Dato2')
    dato3 = fields.Char(string=u'Dato3')
    currency_prov = fields.Selection([('EUR', 'EUR'),
                                      ('USD', 'USD'),
                                      ('BS', 'BS')],
                                     string=u'Moneda del proveedor')
    fleet_lines_ids = fields.One2many('partner.fleet.vehicle', 'partner_id', string='')


class PartnerFleetVehicle(models.Model):
    _name = 'partner.fleet.vehicle'
    fleet_id = fields.Many2one('fleet.vehicle', string=u"Placa")
    owner_id = fields.Many2one("res.partner", string=u"Propietario")
    driver_id = fields.Many2one("res.partner", string=u"Conductor")
    cod_barras = fields.Char(string=u"Código de Barras")
    capacity = fields.Float(string=u"Capacidad")
    partner_id = fields.Many2one('res.partner', string='Proveedor', required=True, ondelete='cascade', index=True,
                                 copy=True)

    @api.multi
    @api.onchange('fleet_id')
    def onchange_fleet_id(self):
        if self.fleet_id:
            self.owner_id = self.fleet_id.owner_id.id
            self.driver_id = self.fleet_id.driver_id.id
            self.cod_barras = self.fleet_id.cod_barras
            self.capacity = self.fleet_id.capacity
