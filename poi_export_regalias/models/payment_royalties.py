# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class PaymentRoyalties(models.Model):
    _name = 'payment.royalties'

    name = fields.Char(string=u'Regalía Minera')
    type = fields.Selection([('regalia', 'Regalias'),
                                          ('seneracom', 'Seneracom')],
                                         string=u'Concepto', default='')
    value = fields.Float(string=u"Valor")
    type_value = fields.Selection([('porcentaje', 'Porcentaje'),
                             ('valor_fijo', 'Valor Fijo')],
                            string=u'Tipo', default='')
    date_update = fields.Date(string=u"Fecha Actualización")
    date_expiration = fields.Date(string=u"Fecha Vencimiento")
    company_id = fields.Many2one('res.company', string=u'Compañia', change_default=True,
                                 required=True, readonly=True,
                                 default=lambda self: self.env['res.company']._company_default_get('payment.royalties'))

    _sql_constraints = [
        ('check_rangue_date',
         "EXCLUDE USING gist (tsrange(date_update, date_expiration) WITH &&)",
         _(u'El rango de fechas ya existe en el registro de regalías')),
        ('royalties_date_update', 'check(date_expiration >= date_update)',
         'Error! La fecha de actualizacion no puede ser mayor a la fecha de vencimiento.')
    ]

