
from odoo import api, fields, models, _

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'
    entregado = fields.Boolean(string=u"Entregado")
    expiration_date = fields.Date(string=u"Fecha Vencimiento")
    number_code = fields.Char(string=u"Número/Codigo")
    fisico_enviado = fields.Datetime(string=u"Físico enviado")
    fisico_recibido = fields.Datetime(string=u"Físico Recibido")

    @api.onchange('datas_fname')
    def _onchange_datas_fname(self):
        if self.datas_fname:
            self.name = self.datas_fname
