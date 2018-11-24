# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
from dateutil import parser


class OpSport(models.Model):
    _name = 'op.sport'
    
    name = fields.Char('Nombre', required=True)
