# -*- coding: utf-8 -*-
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

from openerp import models, fields, api, _

class ResAgency(models.Model):
    _name = 'res.agency'
    _description = 'Agencies'
    _order = 'name'

    @api.multi
    def name_get(self):
        reads = self.read(['name','parent_id'])
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

    @api.one
    @api.depends('name','parent_id')
    def _complete_name(self):
        name = self.name
        names = self.name_get()
        for complete_name in names:
            if complete_name[0] == self.id:
                self.complete_name = complete_name[1]
                break

    name = fields.Char(string='Agency Name', index=True, copy=False)
    shop_ids = fields.One2many('stock.warehouse', 'agency_id', string='Shops', copy=False)
    parent_id = fields.Many2one('res.agency','Parent Agency', select=True, ondelete='cascade')
    child_ids = fields.One2many('res.agency', 'parent_id', string='Child Agencies')
    complete_name = fields.Char(string='Complete Name', store=True, readonly=True, compute='_complete_name')