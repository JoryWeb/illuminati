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

class ResCurrency(models.Model):
    _inherit = "res.currency"

    @api.model
    def exchange_rate_ws(self, date):
        currency = 'USD'
        currency_ids = self.search([('name', '=', 'USD')], limit=1)
        if currency_ids:
            rate_id = currency_ids[0]
            tc = 1/rate_id.rate
            msj = False
        else:
            tc = 0
            msj = 'Error no se encuetra tipo de Cambio'

        res = {
            "Empresa" : "ALINA",
            "Error" : False,
            "Mensaje" : msj,
            "Cambio_oficial" : tc,
            "Cambio_venta" : tc
        }
        return res
