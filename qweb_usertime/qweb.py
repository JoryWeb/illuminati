# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2015 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
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

""" QWeb usertime : adds support for t-usertime on qweb reports """

from datetime import datetime
import logging
import pytz
import ast

from odoo import models, api, fields
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.http import request
from odoo.tools import pycompat, freehash

_logger = logging.getLogger(__name__)


class QWeb(models.AbstractModel):
    _inherit = 'ir.qweb'


    def _compile_directive_usertime(self, el, options):
        body = []
        str = ''
        if 't-usertime' in el.attrib:
            str = self.tag_usertime(el.attrib.pop('t-usertime'))
        body.append(self._append(ast.Str(pycompat.to_text(str))))
        if el.getchildren():
            for item in el:
                # ignore comments & processing instructions
                if isinstance(item, etree._Comment):
                    continue
                body.extend(self._compile_node(item, options))
                body.extend(self._compile_tail(item))
        return body

    def _directives_eval_order(self):
        directives = super(QWeb, self)._directives_eval_order()
        directives.insert(directives.index('call'), 'usertime')
        return directives

    def tag_usertime(self, tformat):
        tformat = tformat
        qwebcontext = self.env.context
        if not tformat:
            # No format, use default time and date formats from qwebcontext
            lang = self.env.lang or False
            if lang:
                lang = self.env['res.lang'].search(
                    [('code', '=', lang)]
                )
                tformat = "{0.date_format} {0.time_format}".format(lang)
            else:
                tformat = DEFAULT_SERVER_DATETIME_FORMAT

        now = datetime.now()

        tz_name = self.env.user.tz
        if tz_name:
            try:
                utc = pytz.timezone('UTC')
                context_tz = pytz.timezone(tz_name)
                utc_timestamp = utc.localize(now, is_dst=False)  # UTC = no DST
                now = utc_timestamp.astimezone(context_tz)
            except Exception:
                _logger.debug(
                    "failed to compute context/client-specific timestamp, "
                    "using the UTC value",
                    exc_info=True)
        return now.strftime(tformat)
