# -*- coding: utf-8 -*-
from odoo import models, fields, api
class cita(models.Model):

	_name = 'citasrmam.cita'
	
	autor = fields.Char(string="Autor", required=True)
	cita = fields.Text(string="Cita", required=True, translate=True)
	orden = fields.Integer(string="Orden", required=True)
	fecha = fields.Date(string="Fecha de aparición", required=True)