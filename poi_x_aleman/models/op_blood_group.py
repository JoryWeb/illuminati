# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
from dateutil import parser


class OpBloodGroup(models.Model):
    _name = 'op.blood.group'
    _rec_name = 'composition'

    composition = fields.Char('Composicion', required=True)
