##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import itertools
from lxml import etree

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp


class BolBankPaymentType(models.Model):
    _name = "bol.bank.payment.type"

    name = fields.Char('Name', size=32)
    payment_model = fields.Selection([('check', 'Check'),
                                      ('bank_card', 'Debit,Credit or Prepaid Card'),
                                      ('bank_transfer', 'Bank Transfer'),
                                      ('sigma', 'Sigma'),
                                      ('other', 'Other')], string='Model of fields')
    payment_document_type = fields.Selection([(1, u'1. Cheque de cualquier naturaleza'),
                                              (2, u'2. Orden de Transferencia'),
                                              (3, u'3. Ordenes de transferencia electrónica de fondos'),
                                              (4, u'4. Transferencia de fondos'),
                                              (5, u'5. Tarjeta de Débito'),
                                              (6, u'6. Tarjeta de Crédito'),
                                              (7, u'7. Tarjeta Prepagada'),
                                              (8, u'8. Depósito en cuenta'),
                                              (9, u'9. Cartas de Crédito'),
                                              (10, u'10. Otros')], string='Payment Document Type',
                                             help="Tipo de documento para bancarizacion")
