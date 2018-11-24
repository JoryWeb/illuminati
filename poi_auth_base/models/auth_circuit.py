##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2014 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Developed by: Grover Menacho
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

from odoo import models, fields, api

class PoiAuthCircuit(models.Model):
    _name = 'poi.auth.circuit'
    _description = 'Auth Circuit'

    name = fields.Char('Name', size=32)
    type = fields.Selection([('sequential', 'Sequential'),
                             ('everyone', 'Everyone'),
                             ('anyone', 'Anyone')], 'Type')
    auth_lines = fields.One2many('poi.auth.circuit.lines', 'auth_circuit_id', 'Circuit Lines')


class PoiAuthCircuitLines(models.Model):
    _name = 'poi.auth.circuit.lines'

    auth_circuit_id = fields.Many2one('poi.auth.circuit', 'Circuit')
    sequence = fields.Integer('Sequence')
    user_id = fields.Many2one('res.users', 'User who needs to approve')

    _order = 'sequence'
