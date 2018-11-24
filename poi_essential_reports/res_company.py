##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

import datetime
import pytz

import openerp
from openerp import tools, api
from openerp.osv import osv, fields
from openerp.tools.translate import _

@api.model
def _tz_get(self):
    # put POSIX 'Etc/*' entries at the end to avoid confusing users - see bug 1086728
    return [(tz,tz) for tz in sorted(pytz.all_timezones, key=lambda tz: tz if not tz.startswith('Etc/') else '_')]

class res_company(osv.Model):
    _description = 'Partner'
    _inherit = "res.company"

    @api.multi
    def _get_tz_offset(self, name, args):
        return dict(
            (p.id, datetime.datetime.now(pytz.timezone(p.tz or 'GMT')).strftime('%z'))
            for p in self)

    _columns = {
        'tz': fields.selection(_tz_get,  'Timezone', size=64,
            help="The partner's timezone, used to output proper date and time values inside printed reports. "
                 "It is important to set a value for this field. You should use the same timezone "
                 "that is otherwise used to pick and render date and time values: your computer's timezone.", store=True),
        'tz_offset': fields.function(_get_tz_offset, type='char', size=5, string='Timezone offset', invisible=True, store=True),
    }


    #THIS COLUMNS ARE GOING TO HELP US TO HAVE A BETTER CONTROL OF TIMEZONES
    #SELECT id, cast(substring(tz_offset from 1 for 3)||':'||substring(tz_offset from 4 for 2) as interval) as c_interval FROM res_company
    #TO MAKE IT WORK JUST NEED THIS
    #SELECT cast('2016-01-21 00:00:00' as timestamp) + c_interval