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

import time

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError

class AccountAnalyticTagCategory(models.Model):
    _name = 'account.analytic.tag.category'
    _description = 'Analytic Tag Categories'

    name = fields.Char(string='Analytic Tag Category', index=True, required=True)


class AccountAnalyticTag(models.Model):
    _inherit = 'account.analytic.tag'

    parent_id = fields.Many2one('account.analytic.tag', 'Parent')
    child_ids = fields.One2many('account.analytic.tag', 'parent_id', 'Childs')
    category_id = fields.Many2one('account.analytic.tag.category', 'Category')

    @api.one
    @api.constrains('parent_id')
    def _check_recursion(self):
        ct = self.id
        if self.parent_id:
            t = self
            while t.parent_id:
                if t.parent_id.id == ct:
                    raise ValidationError(_("There is a recursive error."))
                t = t.parent_id


    @api.multi
    @api.depends('name', 'parent_id')
    def name_get(self):
        result = []
        for tag in self:
            name = ''
            if tag.parent_id:
                pname = dict(tag.parent_id.name_get())[tag.parent_id.id]
                name += pname + ' > ' + tag.name
            else:
                name = tag.name
            result.append((tag.id, name))
        return result


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    @api.multi
    @api.depends('name', 'tag_ids')
    def name_get(self):
        result = []
        for aa in self:
            name = ''
            for tag in aa.tag_ids:
                if name == '':
                    name = tag.display_name + ' > ' + aa.name
                else:
                    name += ', '+tag.display_name + ' > ' + aa.name
            if name == '':
                name = aa.name

            result.append((aa.id, name))
        return result

    @api.multi
    @api.depends('name', 'tag_ids')
    def _get_full_name(self):
        for aa in self:
            name = ''
            for tag in aa.tag_ids:
                if name == '':
                    name = tag.display_name + ' > ' + aa.name
                else:
                    name += ', ' + tag.display_name + ' > ' + aa.name
            if name == '':
                name = aa.name

            aa.full_name = name

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            for block in name.strip().split('>'):
                domain.append('&')
                domain.append('|')
                domain.append(('name', operator, block))
                domain.append(('full_name', operator, block))
            # domain = ['|', ('full_name', operator, name), ('name', operator, name)]
        pos = self.search(domain + args, limit=limit)
        return pos.name_get()

    @api.multi
    @api.depends('tag_ids')
    def _get_tag(self):
        for aa in self:
            for tag in aa.tag_ids:
                aa.main_tag = tag.display_name
                aa.main_tag_parent = tag.parent_id.display_name
                continue

    full_name = fields.Char('Full Name', compute=_get_full_name, store=True)
    main_tag = fields.Char(u'Categoría', compute=_get_tag, store=True)
    main_tag_parent = fields.Char(u'Categoría raíz', compute=_get_tag, store=True)


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.one
    @api.depends('line_ids.analytic_account_id')
    def _get_first_analytic_account(self):
        for line in self.line_ids:
            if line.analytic_account_id:
                self.analytic_account_id = line.analytic_account_id.id
                self.analytic_main_tag = line.analytic_account_id.main_tag
                self.analytic_main_tag_parent = line.analytic_account_id.main_tag_parent
                break

    analytic_account_id = fields.Many2one("account.analytic.account", "Analytic Account", compute=_get_first_analytic_account, store=True)
    analytic_main_tag = fields.Char(u'Categoría', compute=_get_first_analytic_account, store=True)
    analytic_main_tag_parent = fields.Char(u'Categoría raíz', compute=_get_first_analytic_account, store=True)