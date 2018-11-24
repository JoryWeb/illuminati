# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, exceptions, api, _
STATE_COLOR_SELECTION = [
    ('0', 'Red'),
    ('1', 'Green'),
    ('2', 'Blue'),
    ('3', 'Yellow'),
    ('4', 'Magenta'),
    ('5', 'Cyan'),
    ('6', 'Black'),
    ('7', 'White'),
    ('8', 'Orange'),
    ('9', 'SkyBlue')
]

class ImportsStage(models.Model):
    """ Estados de importación para aplicar a carpetas de importacion
    generadas
    """
    _name = "imports.stage"
    _description = "Estados de Importacion"
    #_order = "sequence, name, id"

    name = fields.Char(string=u"Nombre Estado", required=True)
    sequence = fields.Integer(string=u"Secuencia", required=False)
    state_color = fields.Selection(STATE_COLOR_SELECTION, string=u'Estado Color')

