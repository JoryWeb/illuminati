##############################################################################
#
#    odoo, Open Source Management Solution
#    Copyright (C) 2010 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Autor: Nicolas Bustillos
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

import re
from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo import SUPERUSER_ID

from odoo.exceptions import UserError, RedirectWarning, ValidationError

import odoo.addons.decimal_precision as dp
import logging


class PosSession(models.Model):
    _inherit = 'pos.session'

    on_use = fields.Boolean("On Use")

    @api.model
    def open_session_available(self, session_id):
        session = self.browse(session_id)
        if session.on_use:
            return False
        else:
            session.mark_on_use()
            return True

    @api.model
    def close_session_on_use(self, session_id):
        session = self.browse(session_id)
        if session.on_use:
            session.unmark_on_use()
            return True


    @api.multi
    def force_close_on_use(self):
        for session in self:
            if session.on_use:
                session.on_use = False

    @api.multi
    def mark_on_use(self):
        for session in self:
            session.on_use = True

    @api.multi
    def unmark_on_use(self):
        for session in self:
            session.on_use = False
