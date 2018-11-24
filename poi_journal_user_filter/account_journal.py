#!/usr/bin/env python
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Poiesis Consulting (<http://www.poiesisconsulting.com>).
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

from openerp.osv import expression
from openerp import models, fields, api, _



class account_journal(models.Model):
    _inherit = ['account.journal']

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if ['type','in',['bank','cash']] in args:
            journal_filter = [('id','in',[journal.id for journal in self.env['res.users'].browse(self.env.uid).journal_ids])]
            newargs = expression.AND([args]+[journal_filter])
            res = super(account_journal, self).name_search(name=name, args=newargs, operator=operator, limit=limit)
            if not res:
                res = super(account_journal, self).name_search(name=name, args=args, operator=operator, limit=limit)
        else:
            res = super(account_journal, self).name_search(name=name, args=args, operator=operator, limit=limit)
        return res