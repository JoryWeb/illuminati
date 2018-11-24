# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.tools.float_utils import float_round


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    contract_nr = fields.Char(u'Nr. de contrato', help=u"El número de contrato registrado para fines de Bancarización.")


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.multi
    def _get_stock_move_price_unit(self):
        # price_unit = super(PurchaseOrderLine, self)._get_stock_move_price_unit()
        # SuperCopyCheck
        self.ensure_one()
        amount_ex = 0.0
        line = self[0]
        order = line.order_id
        price_unit = line.price_unit
        if line.taxes_id:
            taxes_all = line.taxes_id.with_context(round=False).compute_all(price_unit,
                                                                            currency=line.order_id.currency_id,
                                                                            quantity=1.0)
            price_unit = taxes_all['total_excluded']
            for atax in taxes_all['taxes']:
                tax = self.env['account.tax'].browse(atax['id'])
                if tax and tax.price_include and tax.cost_include:
                    price_unit += atax['amount']
                    amount_ex += atax['amount']

        if line.product_uom.id != line.product_id.uom_id.id:
            price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
        if order.currency_id != order.company_id.currency_id:
            price_unit = order.currency_id.compute(price_unit, order.company_id.currency_id, round=False)

        # Check rounding issue. Ocurre cuando este costo calculado por impuesto unitario no cuadra con los montos calculados en la factura como totales
        # Anticipar los calculos que hara la Factura para asegurar que finalmente la cuenta puente de Inventarios por facturar si cuadre
        if line.taxes_id:
            precision = self.env['decimal.precision'].precision_get('Account')
            price_total = float_round(price_unit * line.product_qty, precision_digits=precision)
            cost_ex = float_round(amount_ex * line.product_qty, precision_digits=precision)
            cost_add = float_round(taxes_all['total_excluded'] * line.product_qty, precision_digits=precision)
            total_cost = cost_ex + cost_add
            if total_cost != price_total and abs(total_cost - price_total) < 0.1:
                # Aplicar solo en caso de diferencia minima
                price_unit = total_cost / line.product_qty

        return price_unit
