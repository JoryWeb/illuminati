# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp import models, fields, api, exceptions, _


class StockProductioLot(models.Model):
    _inherit = 'stock.production.lot'

    @api.one
    @api.constrains('removal_date', 'alert_date', 'life_date', 'use_date')
    def _check_dates(self):
        dates = filter(lambda x: x, [self.alert_date, self.removal_date,
                                     self.use_date, self.life_date])
        sort_dates = list(dates)
        sort_dates.sort()
        if dates != sort_dates:
            raise exceptions.Warning(
                _('Dates must be: Alert Date < Removal Date < Best Before '
                  'Date < Expiry Date'))

    @api.one
    @api.depends('removal_date', 'alert_date', 'life_date', 'use_date')
    def _get_product_state(self):
        now = fields.Datetime.now()
        self.expiry_state = 'normal'
        if self.life_date and self.life_date < now:
            self.expiry_state = 'expired'
        elif (self.alert_date and self.removal_date and
                self.removal_date >= now > self.alert_date):
            self.expiry_state = 'alert'
        elif (self.removal_date and self.use_date and
                self.use_date >= now > self.removal_date):
            self.expiry_state = 'to_remove'
        elif (self.use_date and self.life_date and
                self.life_date >= now > self.use_date):
            self.expiry_state = 'best_before'

    expiry_state = fields.Selection(
        compute=_get_product_state,
        selection=[('expired', 'Expired'),
                   ('alert', 'In alert'),
                   ('normal', 'Normal'),
                   ('to_remove', 'To remove'),
                   ('best_before', 'After the best before')],
        string='Expiry state')
    mrp_date = fields.Date(string='Manufacturing Date')


class StockQuant(models.Model):

    _inherit = "stock.quant"

    expiry_state = fields.Selection(string="Expiry State",
                                    related="lot_id.expiry_state")

class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def create_lots_for_picking(self):
        super(StockPicking, self).create_lots_for_picking()
        for picking in self:
            # Contralamos que no sea un ubicacion de cliente para actualizar los lotes
            if picking.location_dest_id.usage in ('internal', 'transit'):
                for ops in picking.pack_operation_ids:
                    for opslot in ops.pack_lot_ids:
                        opslot.lot_id.use_date = opslot.lot_id.use_date or opslot.use_date
                        opslot.lot_id.life_date = opslot.lot_id.life_date or opslot.life_date

    # Control de Stock para la venta por lotes expirados

    @api.multi
    def do_transfer(self):
        res = super(StockPicking, self).do_transfer()
        now = fields.Datetime.now()
        for picking in self:
            if picking.location_dest_id.usage in ('customer'):
                for operation in picking.pack_operation_ids:
                    for pack_lot in operation.pack_lot_ids:
                        if pack_lot.lot_id.life_date <= now:
                            raise exceptions.Warning(
                                _('No puede sacar el producto %s del lote %s la fecha de vencimiento es %s' %
                                  (pack_lot.lot_id.product_id.name,
                                   pack_lot.lot_id.name,
                                   pack_lot.lot_id.life_date)))
        return res