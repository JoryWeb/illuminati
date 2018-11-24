##############################################################################
#
#    Odoo
#    Copyright (C) 2014-2016 CodUP (<http://codup.com>).
#
##############################################################################

from odoo import api, fields, models, _

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    asset_id = fields.Many2one("poi.vehicle", string=u"Automovil")


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    service_line_id = fields.Many2one("workshop.order.service.line", string=u"Lineas Servicio")
    item_line_id = fields.Many2one("workshop.order.parts.line", string=u"Items Servicio")
