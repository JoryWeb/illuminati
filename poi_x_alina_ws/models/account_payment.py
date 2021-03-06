#########################################################################
#                                                                       #
# Copyright (C) 2015  Agile Business Group                              #
#                                                                       #
# This program is free software: you can redistribute it and/or modify  #
# it under the terms of the GNU Affero General Public License as        #
# published by the Free Software Foundation, either version 3 of the    #
# License, or (at your option) any later version.                       #
#                                                                       #
# This program is distributed in the hope that it will be useful,       #
# but WITHOUT ANY WARRANTY; without even the implied warranty of        #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
# GNU Affero General Public Licensefor more details.                    #
#                                                                       #
# You should have received a copy of the                                #
# GNU Affero General Public License                                     #
# along with this program.  If not, see <http://www.gnu.org/licenses/>. #
#                                                                       #
#########################################################################
import logging
from openerp import fields, models, api, _
from openerp.exceptions import Warning, ValidationError
from openerp import tools

_logger = logging.getLogger(__name__)

class AccountPayment(models.Model):
    _inherit = "account.payment.term"

    days = fields.Integer('Dias', default=0)

    @api.model
    def get_payment_term(self, company_id='ALINA'):
        term_ids = self.search([])
        terms = []
        for t in term_ids:
            terms.append({
                "CondPagoId": t.id,
                "CondPago_Nombre": t.name,
                "Dias": t.days
            })


        res = {
            "Empresa" : "ALINA",
            "Error" : False,
            "Mensaje" : False,
            "Resultado" : False,
            "Condiciones_de_Pago" : terms
        }

        return res
