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
from openerp.exceptions import ValidationError
from openerp.tools import float_compare, float_round
from openerp.report import report_sxw
from openerp.tools import float_is_zero
import openerp.addons.decimal_precision as dp
from openerp import osv

class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_prepaid_account_payable_id = fields.Many2one('account.account', company_dependent=True,
                                                          string="Prepaid Account Payable",
                                                          domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False)]",
                                                          help="This account will be used instead of the default one as the prepaid payable account for the current partner")
    property_prepaid_account_receivable_id = fields.Many2one('account.account', company_dependent=True,
                                                             string="Prepaid Account Receivable",
                                                             domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False)]",
                                                             help="This account will be used instead of the default one as the prepaid receivable account for the current partner")