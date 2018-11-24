# -*- encoding: utf-8 -*-
from openerp import models, api, fields, registry, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError
from psycopg2 import OperationalError

import logging
import threading

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _compute_total_weight(self):
        for s in self:
            s.total_weight = s.weight * s.total_dimension
