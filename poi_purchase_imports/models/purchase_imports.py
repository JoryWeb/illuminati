# © 2013 Joaquín Gutierrez
# © 2014-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3


from odoo import models, fields, exceptions, api, tools, SUPERUSER_ID, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError


SPLIT_METHOD = [
    ('equal', 'Igual'),
    ('by_quantity', 'Por Cantidad'),
    ('by_current_cost_price', 'Por Precio de Coste'),
    ('by_weight', 'Por Peso'),
    ('by_volume', 'Por Volumen'),
]
STATE_COLOR_SELECTION = [
    ('0', 'Red'),
    ('1', 'Green'),
    ('2', 'Blue'),
    ('3', 'Yellow'),
    ('4', 'Magenta'),
    ('5', 'Cyan'),
    ('6', 'Black'),
    ('7', 'White'),
    ('8', 'Orange'),
    ('9', 'SkyBlue')
]
class StageImportsDate(models.Model):
    _name = 'stage.imports.date'
    distribution = fields.Many2one("poi.purchase.imports", "Carpeta")
    name = fields.Many2one("imports.stage", string="Situación")
    date = fields.Date(string=u"Fecha Estado")

class PoiPurchaseImports(models.Model):
    _name = "poi.purchase.imports"
    _description = "Importación de productos"
    _order = 'name desc'

    @api.one
    @api.depends('total_expense', 'total_purchase')
    def _compute_amount_total(self):
        self.amount_total = self.total_purchase + self.total_expense

    @api.one
    @api.depends('cost_lines', 'cost_lines.total_amount')
    def _compute_total_purchase(self):
        for imports in self:
            if imports.cost_lines:
                imports.update({
                    'total_purchase':sum([x.total_amount for x in self.cost_lines])
                })
                #self.total_purchase = sum([x.total_amount for x in self.cost_lines])
            else:
                imports.update({
                    'total_purchase': self.invoice_id.amount_total
                })
                #imports.total_purchase = self.invoice_id.amount_total

    @api.one
    @api.depends('cost_lines', 'cost_lines.product_price_unit')
    def _compute_total_price_unit(self):
        self.total_price_unit = sum([x.product_price_unit for x in
                                     self.cost_lines])

    @api.one
    @api.depends('cost_lines', 'cost_lines.product_qty')
    def _compute_total_uom_qty(self):
        self.total_uom_qty = sum([x.product_qty for x in self.cost_lines])

    @api.one
    @api.depends('cost_lines', 'cost_lines.total_weight')
    def _compute_total_weight(self):
        self.total_weight = sum([x.total_weight for x in self.cost_lines])

    @api.one
    @api.depends('cost_lines', 'cost_lines.total_weight_net')
    def _compute_total_weight_net(self):
        self.total_weight_net = sum([x.total_weight_net for x in
                                     self.cost_lines])

    @api.one
    @api.depends('cost_lines', 'cost_lines.total_volume')
    def _compute_total_volume(self):
        self.total_volume = sum([x.total_volume for x in self.cost_lines])

    @api.depends('expense_lines.expense_amount', 'expense_lines.invoice_id')
    def _compute_total_expense(self):
        amount_currency = 0
        for imports in self:
            for expense in imports.expense_lines:
                if self.currency_id:
                    amount_tax = 0
                    taxes = expense.expense_line_tax_ids.compute_all(expense.expense_amount, self.currency_id, 1,
                                                      product=expense.product_id, partner=expense.partner_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))

                    amount_currency = amount_currency + expense.currency_id.compute(expense.expense_amount - amount_tax, self.currency_id)
            # self.total_expense = sum([x.expense_amount for x in self.expense_lines])
            imports.update({
                'total_expense': amount_currency
            })
            #self.total_expense = amount_currency

    # def _expense_lines_default(self):
    #    expenses = self.env['purchase.expense.type'].search(
    #        [('default_expense', '=', True)])
    #    return [{'type': x, 'expense_amount': x.default_amount}
    #            for x in expenses]

    _group_by_full = {
        'stage_id': lambda s, *a, **k: s._read_group_stage_ids(*a, **k),
    }

    name = fields.Char(string='Distribution number', required=True,
                       select=True, default='/')

    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', required=True,
        default=(lambda self: self.env['res.company']._company_default_get(
            'poi.purchase.imports')))
    currency_id = fields.Many2one(comodel_name='res.currency', string='Divisa')
    state = fields.Selection(
        [('draft', 'Borrador'),
         ('calculated', 'Calculado'),
         ('done', 'Realizado'),
         ('error', 'Error'),
         ('cancel', 'Cancelado')], string='Estado',
        index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False)
    cost_update_type = fields.Selection(
        [('direct', 'Direct Update')], string='Cost Update Type',
        default='direct', required=True)
    date = fields.Date(
        string='Date', required=True, readonly=True, select=True,
        states={'draft': [('readonly', False)]},
        default=fields.Date.context_today)
    total_uom_qty = fields.Float(
        compute=_compute_total_uom_qty, readonly=True,
        digits_compute=dp.get_precision('Product UoS'),
        string='Total quantity')
    total_weight = fields.Float(
        compute=_compute_total_weight, string='Total Peso',
        readonly=True,
        digits_compute=dp.get_precision('Stock Weight'))
    total_weight_net = fields.Float(
        compute=_compute_total_weight_net,
        digits_compute=dp.get_precision('Stock Peso'),
        string='Total net weight', readonly=True)
    total_volume = fields.Float(
        compute=_compute_total_volume, string='Total volumen', readonly=True)
    total_purchase = fields.Float(
        compute=_compute_total_purchase,
        digits_compute=dp.get_precision('Account'), string='Total purchase', store=True)
    total_price_unit = fields.Float(
        compute=_compute_total_price_unit, string='Total price unit',
        digits_compute=dp.get_precision('Product Price'))
    amount_total = fields.Float(
        compute=_compute_amount_total,
        digits_compute=dp.get_precision('Account'), string='Total')
    total_expense = fields.Float(
        compute=_compute_total_expense,
        digits_compute=dp.get_precision('Account'), string='Total Gastos', store=True)
    note = fields.Text(string='Documentation for this order')

    cost_lines = fields.One2many(
        comodel_name='poi.purchase.imports.line', ondelete="cascade",
        inverse_name='distribution', string='Distribution lines', readonly=True, states={'draft': [('readonly', False)]})

    picking_lines = fields.One2many(
        comodel_name='poi.purchase.imports.picking', ondelete="cascade",
        inverse_name='distribution', string='Distribution lines', readonly=True, states={'draft': [('readonly', False)]})

    expense_lines = fields.One2many(
        comodel_name='poi.purchase.imports.expense', ondelete="cascade",
        inverse_name='distribution', string='Expenses', readonly=True, states={'draft': [('readonly', False)]})
    # default=_expense_lines_default)

    # Nuevos campos adicionales

    partner_id = fields.Many2one(
        comodel_name='res.partner', string="Proveedor", readonly=True, states={'draft': [('readonly', False)]})

    order_id = fields.Many2one(
        comodel_name='purchase.order', string="Orden de Importaciones", domain=[('imports', '=', False)], readonly=True, required=True, states={'draft': [('readonly', False)]})

    invoice_id = fields.Many2one(
        comodel_name='account.invoice', string="Factura Importaciones", domain=[('imports', '=', False)], readonly=True,
        required=False, states={'draft': [('readonly', False)]})

    journal_id = fields.Many2one(
        comodel_name='account.journal', string="Diario Contable", required=False,
        domain=[('type', 'in', ['purchase', 'general'])], readonly=True, states={'draft': [('readonly', False)]})

    stage_id = fields.Many2one('imports.stage', string=u"Situación", track_visibility='onchange')

    stage_date = fields.One2many('stage.imports.date', 'distribution', string=u"Estados Importación", copy=False)
    state_color = fields.Selection(related='stage_id.state_color',
                                               selection=STATE_COLOR_SELECTION, string="Color", readonly=True)
    @api.onchange('stage_id')
    def onchange_stage_id(self):
        for imports in self and self._origin:
            # Borrar los picking asignados
            stage = self.env['stage.imports.date']
            stage_vals = stage.search([('distribution', '=', self._origin.id), ('name', '=', imports.stage_id.id)])
            if not stage_vals:
                stage.create({'distribution': self._origin.id,
                              'name': imports.stage_id.id,
                              'date': fields.Date.context_today(self)})
            else:
                raise exceptions.Warning(
                    _(u"No puede volver a una situación anterior"))
    @api.multi
    def write(self, vals):
        # Dont allow changing the company_id when account_move_line already exist
        for imports in self:
            if vals.get('stage_id', False):
                stage = self.env['stage.imports.date']
                stage_vals = stage.search([('distribution', '=', imports.id), ('name', '=', vals['stage_id'])])
                if not stage_vals:
                    stage.create({'distribution': imports.id,
                                  'name': vals['stage_id'],
                                  'date': fields.Date.context_today(self)})
                else:
                    raise exceptions.Warning(
                        _(u"No puede volver a una situación anterior"))
        return super(PoiPurchaseImports, self).write(vals)

    @api.multi
    def _read_group_stage_ids(self, domain, read_group_order=None, access_rights_uid=None):
        """ Read group customization in order to display all the category in the
            kanban view, even if they are empty
        """
        stage_obj = self.env['imports.stage']
        order = stage_obj._order
        access_rights_uid = access_rights_uid or self._uid
        if read_group_order == 'sequence desc':
            order = '%s desc' % order

        stage_ids = stage_obj._search([], order=order, access_rights_uid=access_rights_uid)
        result = [stage.name_get()[0] for stage in stage_obj.browse(stage_ids)]
        # restore order of the search
        result.sort(lambda x, y: cmp(stage_ids.index(x[0]), stage_ids.index(y[0])))

        fold = {}
        for stage in stage_obj.browse(stage_ids):
            fold[stage.id] = stage.sequence
        #return result, fold
        return result, None
    @api.multi
    def unlink(self):
        for c in self:
            # Limpiar registros de quants
            quant = self.env['stock.quant'].search([('imports', '=', c.id)])
            for q in quant:
                q.imports = False
            # Limpiar registros de Picking
            picking = self.env['stock.picking'].search([('imports', '=', c.id)])
            for pick in picking:
                pick.imports = False
            c.order_id.imports = False
            c.invoice_id.imports = False
            for line_exp in c.expense_lines:
                line_exp.invoice_id.imports = False
            if c.state not in ('draft', 'calculated'):
                raise exceptions.Warning(
                    _("You can't delete a confirmed cost distribution"))
        return super(PoiPurchaseImports, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'poi.purchase.imports')
        res_id = super(PoiPurchaseImports, self).create(vals)
        if res_id.order_id:
            # La logica cambia a utilizar grupo de abastecimiento para asignar solo el albaran de ingreso de mercaderias
            # a una ubicación interna

            pickings = self.env['stock.picking'].search([('group_id', '=', res_id.order_id.group_id.id), ('state', '=', 'done'), ('imports', '=', False)])
            for picking in pickings:
                value_line = {
                    'picking_id': picking.id,
                    'name': picking.name,
                    'distribution': res_id.id,
                }
                self.env['poi.purchase.imports.picking'].create(value_line)
                picking.imports = res_id.id
                # Cargar Lineas que son Aplicadas a
                # tipo de producto Promedio ponderado
                self.action_import_picking(res_id, picking)
                # Asignar Lote a Carpeta de Importacion para que solo
                # Los quants asignados sean visibles al momento
                # de Seleccionar y no estar buscando todos los quants
                # Definir si va mostrar quants en ubicaciones de clientes??
                for move in picking.move_lines:
                    move.imports = res_id.id
                    for quant in move.quant_ids:
                        quant.imports = res_id.id

            # Asignar carpeta de importación a orden de compra
            res_id.order_id.imports = res_id.id
            if res_id.invoice_id:
                res_id.invoice_id.imports = res_id.id

        return res_id

    @api.model
    def _prepare_expense_line(self, expense_line, cost_line):
        distribution = cost_line.distribution
        if expense_line.split_method == 'amount':
            multiplier = cost_line.total_amount
            if expense_line.affected_lines:
                divisor = sum([x.total_amount for x in
                               expense_line.affected_lines])
            else:
                divisor = distribution.total_purchase
        elif expense_line.split_method == 'by_current_cost_price':
            multiplier = cost_line.product_price_unit
            if expense_line.affected_lines:
                divisor = sum([x.product_price_unit for x in
                               expense_line.affected_lines])
            else:
                divisor = distribution.total_price_unit
        elif expense_line.split_method == 'by_quantity':
            multiplier = cost_line.product_qty
            if expense_line.affected_lines:
                divisor = sum([x.product_qty for x in
                               expense_line.affected_lines])
            else:
                divisor = distribution.total_uom_qty
        elif expense_line.split_method == 'by_weight':
            multiplier = cost_line.total_weight
            if expense_line.affected_lines:
                divisor = sum([x.total_weight for x in
                               expense_line.affected_lines])
            else:
                divisor = distribution.total_weight
        elif expense_line.split_method == 'by_weight_net':
            multiplier = cost_line.total_weight_net
            if expense_line.affected_lines:
                divisor = sum([x.total_weight_net for x in
                               expense_line.affected_lines])
            else:
                divisor = distribution.total_weight_net
        elif expense_line.split_method == 'by_volume':
            multiplier = cost_line.total_volume
            if expense_line.affected_lines:
                divisor = sum([x.total_volume for x in
                               expense_line.affected_lines])
            else:
                divisor = distribution.total_volume
        elif expense_line.split_method == 'equal':
            multiplier = 1
            divisor = (len(expense_line.affected_lines) or
                       len(distribution.cost_lines))
        else:
            raise exceptions.Warning(
                _('No valid distribution type.'))
        if divisor:
            # expense_amount = (expense_line.expense_amount * multiplier /
            #                  divisor)
            amount_currency = expense_line.currency_id.compute(expense_line.price_subtotal,
                                                               self.env.user.company_id.currency_id)
            expense_amount = (amount_currency * multiplier / divisor)

        else:
            raise exceptions.Warning(
                _("The cost for the line '%s' can't be "
                  "distributed because the calculation method "
                  "doesn't provide valid data" % cost_line.split_method))
        return {
            'distribution_expense': expense_line.id,
            'expense_amount': expense_amount,
            'cost_ratio': expense_amount / cost_line.product_qty,
        }

    @api.multi
    def action_calculate(self):
        for distribution in self:
            # Check expense lines for amount 0
            if any([not x.expense_amount for x in distribution.expense_lines]):
                raise exceptions.Warning(
                    _('Please enter an amount for all the expenses'))
            # Check if exist lines in distribution
            if not distribution.cost_lines:
                raise exceptions.Warning(
                    _('There is no picking lines in the distribution'))
            # Calculating expense line
            for cost_line in distribution.cost_lines:
                cost_line.expense_lines.unlink()
                expense_lines = []
                for expense in distribution.expense_lines:
                    if (expense.affected_lines and
                                cost_line not in expense.affected_lines):
                        continue
                    expense_lines.append(
                        self._prepare_expense_line(expense, cost_line))
                cost_line.expense_lines = [(0, 0, x) for x in expense_lines]
            distribution.state = 'calculated'
        return True

    def _product_price_update(self, move, new_price, qty_out):
        """Method that mimicks stock.move's product_price_update_before_done
        method behaviour, but taking into account that calculations are made
        on an already done move, and prices sources are given as parameters.
        """
        if (move.location_id.usage == 'supplier' and
                    move.product_id.cost_method == 'average'):
            product = move.product_id

            qty_available = product.product_tmpl_id.qty_available
            qty_available_date = 0.0
            # Debemos verificar el stock en una fecha determinada en caso de valorar a negavito
            # Necesario hacer con SQL ya que la funcion fecha no funciona en stock
            if qty_out > 0:
                self._cr.execute(
                    """select sum(t0.product_qty) as total
                        from stock_move t0
                        inner join stock_location sl1 on sl1.id = t0.location_id
                        inner join stock_location sl2 on sl2.id = t0.location_dest_id
                        where t0.state in ('done')
                        and t0.product_id = """ + str(move.product_id.id) + """
                        and t0.date <= '""" + str(move.date) + """'
                          and sl1.usage in ('inventory','supplier','customer','procurement','production')
                        group by t0.product_id
                    """)
                incoming_qty = 0.0
                for val in self._cr.fetchall():
                    incoming_qty += val[0]

                self._cr.execute(
                    """select sum(t0.product_qty) as total
                        from stock_move t0
                        inner join stock_location sl1 on sl1.id = t0.location_id
                        inner join stock_location sl2 on sl2.id = t0.location_dest_id
                        and t0.product_id = """ + str(move.product_id.id) + """
                        and t0.date <= '""" + str(move.date) + """'
                          and sl2.usage in ('inventory','supplier','customer','procurement','production')
                        group by t0.product_id
                    """)
                outgoing_qty = 0.0
                for val in self._cr.fetchall():
                    outgoing_qty += val[0]

                qty_available_date = incoming_qty - outgoing_qty

            product_avail = qty_available - move.product_qty

            if product_avail <= 0 and qty_available <= 0:
                new_std_price = new_price
            else:
                domain_quant = [
                    ('product_id', 'in',
                     product.product_tmpl_id.product_variant_ids.ids),
                    ('id', 'not in', move.quant_ids.ids),
                    ('location_id.usage', '=', 'internal')]
                quants = self.env['stock.quant'].search(domain_quant)
                current_valuation = sum([(q.cost * q.qty) for q in quants])

                # Verificar si existen salidas para establecer el nuevo costo del producto
                if qty_out <= 0:
                    new_std_price = (
                        (current_valuation + (new_price * move.product_qty)) / qty_available)
                else:
                    new_std_price = (
                        (current_valuation + (new_price * move.product_qty)) / qty_available_date)
            # Write the standard price, as SUPERUSER_ID, because a
            # warehouse manager may not have the right to write on products
            # ctx = dict(self._context, modelo='poi.purchase.imports', id_modelo=self.id)
            # self.with_context(ctx)
            product.sudo().write({'standard_price': new_std_price})

    @api.one
    def action_done(self):
        if not self.journal_id:
            raise UserError(_('Por favor definir el diario contable'))

        # Confirmar Albaranes no transferidos
        # for line in self.picking_lines:
        #     if line.picking_id.state in ('assigned'):
        #         line.picking_id.do_new_transfer()
        #         stock_immediate_transfer = self.env['stock.immediate.transfer']. \
        #             create({'pick_id': line.picking_id.id})
        #         stock_immediate_transfer.process()

        # Considerando las entregas parciales
        # Actualizamos los precios unitarios de los moves
        for line in self.cost_lines:
            if self.cost_update_type == 'direct':
                # No se crea el asiento solo al transferir el albaran
                #move_id = self._create_account_move()
                qty_out = 0
                # En promedio ponderado es necesario validar el movimiento de existencias
                # antes de realizar los calculos

                #if line.move_id.product_id.cost_method in ('average'):
                #    line.move_id.action_done()

                # Identificar todos los quants que estan
                # en ubicación clientes, bajas inventario, ajustes, perdida
                #for quant in line.move_id.quant_ids:
                #    if quant.location_id.usage != 'internal':
                #        qty_out += quant.qty
                #self._create_accounting_entries(line, move_id, qty_out)
                #move_id.post()
                #line.move_id.quant_ids._price_update(line.standard_price_new)
                #self._product_price_update(line.move_id, line.standard_price_new, qty_out)
                #line.product_price_update = line.product_id.standard_price
                #line.date_update_price = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                # nSolo aplicaria en caso de promedio "Real"
                #line.move_id.product_price_update_after_done()
                line.move_id.cost_ratio = line.cost_ratio
                line.move_id.standard_price_new = line.standard_price_new
        self.state = 'done'

    # Generar Asiento contable de Ajuste de Inventarios

    def _create_account_move(self):
        vals = {
            'journal_id': self.journal_id.id,
            'date': self.date,
            'ref': self.name
        }
        return self.env['account.move'].create(vals)

    def _create_accounting_entries(self, line, move_id, qty_out):
        product_obj = self.env['product.template']
        cost_product = line.move_id.product_id
        if not cost_product:
            return False
        accounts = product_obj.browse(line.product_id.product_tmpl_id.id).get_product_accounts()
        debit_account_id = accounts.get('stock_valuation', False) and accounts['stock_valuation'].id or False
        already_out_account_id = accounts['stock_output'].id
        credit_account_id = cost_product.property_account_expense_id.id or cost_product.categ_id.property_account_expense_categ_id.id

        if not credit_account_id:
            raise UserError(_('Please configure Stock Expense Account for product: %s.') % (cost_product.name))

        return self._create_account_move_line(line, move_id, credit_account_id, debit_account_id, qty_out,
                                              already_out_account_id)

    def _create_account_move_line(self, line, move_id, credit_account_id, debit_account_id, qty_out,
                                  already_out_account_id):
        """
        Generate the account.move.line values to track the landed cost.
        Afterwards, for the goods that are already out of stock, we should create the out moves
        """
        aml_obj = self.env['account.move.line']
        user_obj = self.env['res.users']
        # if context is None:
        #    context = {}
        ctx = self._context.copy()
        ctx['check_move_validity'] = False
        for line_account in line.expense_lines:
            base_line = {
                'name': line.move_id.name,
                'move_id': move_id.id,
                'product_id': line.move_id.product_id.id,
                'quantity': line.move_id.product_uom_qty,
            }
            debit_line = dict(base_line, account_id=debit_account_id)
            credit_line = dict(base_line, account_id=credit_account_id)
            diff = line_account.expense_amount
            if diff > 0:
                debit_line['debit'] = diff
                credit_line['credit'] = diff
            else:
                # negative cost, reverse the entry
                debit_line['credit'] = -diff
                credit_line['debit'] = -diff
            aml_obj.with_context(check_move_validity=False).create(debit_line)
            aml_obj.with_context(check_move_validity=False).create(credit_line)

            # Create account move lines for quants already out of stock
            if qty_out > 0:
                debit_line = dict(base_line,
                                  name=(line.name + ": " + str(qty_out) + _(' already out')),
                                  quantity=qty_out,
                                  account_id=already_out_account_id)
                credit_line = dict(base_line,
                                   name=(line.name + ": " + str(qty_out) + _(' already out')),
                                   quantity=qty_out,
                                   account_id=debit_account_id)
                diff = diff * qty_out / line.move_id.product_uom_qty
                if diff > 0:
                    debit_line['debit'] = diff
                    credit_line['credit'] = diff
                else:
                    # negative cost, reverse the entry
                    debit_line['credit'] = -diff
                    credit_line['debit'] = -diff
                aml_obj.with_context(check_move_validity=False).create(debit_line)
                aml_obj.with_context(check_move_validity=False).create(credit_line)

                if self.env.user.company_id.anglo_saxon_accounting:
                    debit_line = dict(base_line,
                                      name=(line.name + ": " + str(qty_out) + _(' already out')),
                                      quantity=qty_out,
                                      account_id=credit_account_id)
                    credit_line = dict(base_line,
                                       name=(line.name + ": " + str(qty_out) + _(' already out')),
                                       quantity=qty_out,
                                       account_id=already_out_account_id)

                    if diff > 0:
                        debit_line['debit'] = diff
                        credit_line['credit'] = diff
                    else:
                        # negative cost, reverse the entry
                        debit_line['credit'] = -diff
                        credit_line['debit'] = -diff
                    aml_obj.with_context(check_move_validity=False).create(debit_line)
                    aml_obj.with_context(check_move_validity=False).create(credit_line)

        move_id.assert_balanced()
        return True

    def _create_accounting_entries_stock(self, move_line, move_id, qty_out):
        product_obj = self.env['product.template']
        cost_product = move_line.product_id
        if not cost_product:
            return False
        accounts = product_obj.browse(move_line.product_id.product_tmpl_id.id).get_product_accounts()
        debit_account_id = accounts.get('stock_valuation', False) and accounts['stock_valuation'].id or False
        already_out_account_id = accounts['stock_output'].id
        credit_account_id = cost_product.property_account_expense_id.id or cost_product.categ_id.property_account_expense_categ_id.id

        if not credit_account_id:
            raise UserError(_('Please configure Stock Expense Account for product: %s.') % (cost_product.name))

        return self._create_account_move_line_stock(move_line, move_id, credit_account_id, debit_account_id, qty_out,
                                              already_out_account_id)

    def _create_account_move_line_stock(self, move_line, move_id, credit_account_id, debit_account_id, qty_out,
                                  already_out_account_id):
        """
        Generate the account.move.line values to track the landed cost.
        Afterwards, for the goods that are already out of stock, we should create the out moves
        """
        aml_obj = self.env['account.move.line']
        user_obj = self.env['res.users']
        # if context is None:
        #    context = {}
        ctx = self._context.copy()
        ctx['check_move_validity'] = False

        base_line = {
            'name': move_line.name,
            'move_id': move_id.id,
            'product_id': move_line.product_id.id,
            'quantity': move_line.product_uom_qty,
        }
        debit_line = dict(base_line, account_id=debit_account_id)
        credit_line = dict(base_line, account_id=credit_account_id)
        # Aqui calculamos el costo por la cantidad transferida
        diff = move_line.product_uom_qty * move_line.cost_ratio
        if diff > 0:
            debit_line['debit'] = diff
            credit_line['credit'] = diff
        else:
            # negative cost, reverse the entry
            debit_line['credit'] = -diff
            credit_line['debit'] = -diff
        aml_obj.with_context(check_move_validity=False).create(debit_line)
        aml_obj.with_context(check_move_validity=False).create(credit_line)

        # Create account move lines for quants already out of stock
        if qty_out > 0:
            debit_line = dict(base_line,
                              name=(move_line.name + ": " + str(qty_out) + _(' already out')),
                              quantity=qty_out,
                              account_id=already_out_account_id)
            credit_line = dict(base_line,
                               name=(move_line.name + ": " + str(qty_out) + _(' already out')),
                               quantity=qty_out,
                               account_id=debit_account_id)
            diff = diff * qty_out / move_line.move_id.product_uom_qty
            if diff > 0:
                debit_line['debit'] = diff
                credit_line['credit'] = diff
            else:
                # negative cost, reverse the entry
                debit_line['credit'] = -diff
                credit_line['debit'] = -diff
            aml_obj.with_context(check_move_validity=False).create(debit_line)
            aml_obj.with_context(check_move_validity=False).create(credit_line)

            if self.env.user.company_id.anglo_saxon_accounting:
                debit_line = dict(base_line,
                                  name=(move_line.name + ": " + str(qty_out) + _(' already out')),
                                  quantity=qty_out,
                                  account_id=credit_account_id)
                credit_line = dict(base_line,
                                   name=(move_line.name + ": " + str(qty_out) + _(' already out')),
                                   quantity=qty_out,
                                   account_id=already_out_account_id)

                if diff > 0:
                    debit_line['debit'] = diff
                    credit_line['credit'] = diff
                else:
                    # negative cost, reverse the entry
                    debit_line['credit'] = -diff
                    credit_line['debit'] = -diff
                aml_obj.with_context(check_move_validity=False).create(debit_line)
                aml_obj.with_context(check_move_validity=False).create(credit_line)

        move_id.assert_balanced()
        return True

    @api.multi
    def action_draft(self):
        self.write({'state': 'draft'})
        return True

    @api.one
    def action_cancel(self):
        for line in self.cost_lines:
            if self.cost_update_type == 'direct':
                if self.currency_id.compare_amounts(line.move_id.quant_ids[0].cost, line.standard_price_new) != 0:
                    raise exceptions.Warning(
                        _('Cost update cannot be undone because there has '
                          'been a later update. Restore correct price and try '
                          'again.'))
                line.move_id.quant_ids._price_update(line.standard_price_old)
                self._product_price_update(line.move_id, line.standard_price_old, 0)
                line.move_id.product_price_update_after_done()
        self.state = 'draft'

    # Actualización codigo importar picking de una
    # compra de importaciones
    @api.onchange('order_id')
    def onchange_order_id(self):
        if self.order_id and self._origin:
            # Borrar los picking asignados
            self.picking_lines.unlink()
            name = self.order_id.name
            domain_picking = [('origin', '=', name)]
            pickings = self.env['stock.picking'].search(domain_picking)
            for picking in pickings:
                value_line = {
                    'picking_id': picking.id,
                    'name': name + '|' + picking.name,
                    'distribution': self._origin.id,
                }
                picking.imports = self._origin.id
                self.env['poi.purchase.imports.picking'].create(value_line)

            self.order_id.imports = self._origin.id
        elif self.order_id:
            self.partner_id = self.order_id.id

    # Obtener lineas de movimiento de picking importados para la compra
    def _prepare_distribution_line(self, distribution, move):
        return {
            'distribution': distribution.id,
            'move_id': move.id,
        }

    @api.multi
    def action_import_picking(self, distribution, picking):
        # self.ensure_one()
        # distribution = self
        previous_moves = distribution.mapped('cost_lines.move_id')
        # Solo se aplicaran movimientos donde el producto sea "Promedio ponderado"
        for move in picking.move_lines:
            #if move not in previous_moves:
                # Para promedio ponderado solo esta permitido asignar lineas que ingresan a una ubicación
                # interna
            if move.product_id.cost_method == 'average' and move.location_dest_id.usage == 'internal':
                self.env['poi.purchase.imports.line'].create(
                    self._prepare_distribution_line(distribution, move))

    @api.multi
    def action_view_quant(self):
        '''
        Funcion necesaria para obtener los quants asignados a este chasis
        '''
        action = self.env.ref('stock.location_open_quants')
        result = action.read()[0]
        res = self.env.ref('stock.view_stock_quant_tree', False)
        result['views'] = [(res and res.id or False, 'tree')]
        result['res_id'] = self.id
        result['context'] = "{'default_imports': %d}" % self.id
        result['domain'] = "[('imports','in',[" + ','.join(map(str, [self.id])) + "])]"
        return result

    @api.multi
    def action_view_cost(self):
        '''
        Funcion necesaria para ver el reporte de costes de Importacion
        '''
        action = self.env.ref('poi_purchase_imports.action_poi_purchase_imports_report_report_all')
        result = action.read()[0]
        res = self.env.ref('poi_purchase_imports.view_poi_purchase_imports_report_pivot', False)
        result['views'] = [(res and res.id or False, 'tree')]
        result['res_id'] = self.id
        result['context'] = "{'default_order_id': %d}" % self.order_id.id
        result['domain'] = "[('order_id','in',[" + ','.join(map(str, [self.order_id.id])) + "])]"
        return result

    @api.multi
    def action_view_invoice(self):
        '''
        Buscar las polizas de importación que esten asignados
        a la carpeta de importaciones
        '''
        action = self.env.ref('poi_purchase_imports.action_invoice_poliza')
        result = action.read()[0]
        res = self.env.ref('poi_purchase_imports.view_invoice_poliza_tree', False)
        result['views'] = [(res and res.id or False, 'tree')]
        result['res_id'] = self.id
        result['context'] = "{'default_imports': %d}" % self.id
        result['domain'] = "[('imports','in',[" + ','.join(map(str, [self.id])) + "]), ('iva','>',0.0)]"
        return result

    @api.multi
    def action_view_stock_moves(self):
        '''
                Buscar todos los movimientos asignados a todos
                los pickings de la carpeta de importaciones
                '''
        move_ids = []
        for pickings in self.picking_lines:
            for moves in pickings.picking_id.move_lines:
                move_ids.append(moves.id)
        if move_ids:
            return {
                'domain': "[('id','in',[" + ','.join(map(str, list(move_ids))) + "])]",
                'name': _('Movimientos'),
                'view_mode': 'tree,form',
                'view_type': 'form',
                'context': {'tree_view_ref': 'stock.view_move_tree'},
                'res_model': 'stock.move',
                'type': 'ir.actions.act_window',
            }

    def action_your_imports(self, cr, uid, context=None):
        IrModelData = self.pool['ir.model.data']
        action = IrModelData.xmlid_to_object(cr, uid, 'poi_purchase_imports.poi_purchase_imports_tree_view', context=context).read(
            ['name', 'help', 'res_model', 'target', 'domain', 'context', 'type'])
        if not action:
            action = {}
        else:
            action = action[0]

        action_context = eval(action['context'], {'uid': uid})

        tree_view_id = IrModelData.xmlid_to_res_id(cr, uid, 'poi_purchase_imports.view_poi_purchase_imports_tree')
        form_view_id = IrModelData.xmlid_to_res_id(cr, uid, 'poi_purchase_imports.poi_purchase_imports_form')
        kanb_view_id = IrModelData.xmlid_to_res_id(cr, uid, 'poi_purchase_imports.imports_kanban_view')
        action.update({
            'views': [
                [kanb_view_id, 'kanban'],
                [tree_view_id, 'tree'],
                [form_view_id, 'form'],
                [False, 'graph'],
                [False, 'calendar'],
                [False, 'pivot']
            ],
            'context': action_context,
        })
        return action


class PoiPurchaseImportsLine(models.Model):
    _name = "poi.purchase.imports.line"
    _description = "Purchase cost distribution Line"

    @api.one
    @api.depends('product_price_unit', 'product_qty')
    def _compute_total_amount(self):
        self.total_amount = self.product_price_unit * self.product_qty

    @api.one
    @api.depends('product_id', 'product_qty')
    def _compute_total_weight(self):
        self.total_weight = self.product_weight * self.product_qty

    @api.one
    @api.depends('product_id', 'product_qty')
    def _compute_total_weight_net(self):
        self.total_weight_net = self.product_weight_net * self.product_qty

    @api.one
    @api.depends('product_id', 'product_qty')
    def _compute_total_volume(self):
        self.total_volume = self.product_volume * self.product_qty

    @api.one
    @api.depends('expense_lines', 'expense_lines.cost_ratio')
    def _compute_cost_ratio(self):
        self.cost_ratio = sum([x.cost_ratio for x in self.expense_lines])

    @api.one
    @api.depends('expense_lines', 'expense_lines.expense_amount')
    def _compute_expense_amount(self):
        self.expense_amount = sum([x.expense_amount for x in
                                   self.expense_lines])

    @api.one
    @api.depends('standard_price_old', 'cost_ratio')
    def _compute_standard_price_new(self):
        self.standard_price_new = self.standard_price_old + self.cost_ratio

    @api.one
    @api.depends('move_id', 'move_id.picking_id', 'move_id.product_id',
                 'move_id.product_qty')
    def _compute_display_name(self):
        self.name = '%s / %s / %s' % (
            self.move_id.picking_id.name, self.move_id.product_id.display_name,
            self.move_id.product_qty)

    @api.one
    @api.depends('move_id', 'move_id.product_id')
    def _get_product_id(self):
        # Cannot be done via related field due to strange bug in update chain
        self.product_id = self.move_id.product_id.id

    @api.one
    @api.depends('move_id', 'move_id.product_qty')
    def _get_product_qty(self):
        # Cannot be done via related field due to strange bug in update chain
        self.product_qty = self.move_id.product_qty

    @api.one
    @api.depends('move_id')
    def _get_standard_price_old(self):
        self.standard_price_old = (
            self.move_id and self.move_id.get_price_unit(self.move_id) or 0.0)

    name = fields.Char(
        string='Name', compute='_compute_display_name')
    distribution = fields.Many2one(
        comodel_name='poi.purchase.imports', string='Cost distribution',
        ondelete='cascade', required=True)
    move_id = fields.Many2one(
        comodel_name='stock.move', string='Linea de Picking', ondelete="restrict",
        required=True)
    purchase_line_id = fields.Many2one(
        comodel_name='purchase.order.line', string='Purchase order line',
        related='move_id.purchase_line_id')
    purchase_id = fields.Many2one(
        comodel_name='purchase.order', string='Purchase order', readonly=True,
        related='move_id.purchase_line_id.order_id', store=True)
    partner = fields.Many2one(
        comodel_name='res.partner', string='Supplier', readonly=True,
        related='move_id.purchase_line_id.order_id.partner_id')
    picking_id = fields.Many2one(
        'stock.picking', string='Picking', related='move_id.picking_id',
        store=True)
    product_id = fields.Many2one(
        comodel_name='product.product', string='Product', store=True,
        compute='_get_product_id')

    account_id = fields.Many2one(
        comodel_name='account.account', string='Cuenta de Gastos')

    product_qty = fields.Float(
        string='Quantity', compute='_get_product_qty', store=True)
    product_uom = fields.Many2one(
        comodel_name='product.uom', string='Unit of measure',
        related='move_id.product_uom')
    product_uos_qty = fields.Float(
        string='Quantity (UoS)', related='move_id.product_uom_qty')
    product_uos = fields.Many2one(
        comodel_name='product.uom', string='Product UoS',
        related='move_id.product_uom')
    product_price_unit = fields.Float(
        string='Precio Unitario', related='move_id.price_unit')
    expense_lines = fields.One2many(
        comodel_name='poi.purchase.imports.line.expense',
        inverse_name='distribution_line', string='Expenses distribution lines')
    product_volume = fields.Float(
        string='Volume', help="The volume in m3.",
        related='product_id.product_tmpl_id.volume')
    product_weight = fields.Float(
        string='Gross weight', related='product_id.product_tmpl_id.weight',
        help="The gross weight in Kg.")
    product_weight_net = fields.Float(
        string='Net weight', related='product_id.product_tmpl_id.weight',
        help="The net weight in Kg.")
    standard_price_old = fields.Float(
        string='Costo Previo', compute="_get_standard_price_old", store=True,
        digits_compute=dp.get_precision('Product Price'))
    expense_amount = fields.Float(
        string='Costo Total Aplicado', digits_compute=dp.get_precision('Account'),
        compute='_compute_expense_amount', store=True)
    cost_ratio = fields.Float(
        string='Unit cost', compute='_compute_cost_ratio')
    standard_price_new = fields.Float(
        string='Nuevo Costo', digits_compute=dp.get_precision('Product Price'),
        compute='_compute_standard_price_new')
    # Campo requerido para verificar fecha de actualización del producto y su costo unitario
    product_price_update = fields.Float(
        string='Nuevo Costo', digits_compute=dp.get_precision('Product Price'))
    date_update_price = fields.Datetime(string="Costo Actualizado")

    total_amount = fields.Float(
        compute=_compute_total_amount, string='Amount line',
        digits_compute=dp.get_precision('Account'), store=True)
    total_weight = fields.Float(
        compute=_compute_total_weight, string="Line weight", store=True,
        digits_compute=dp.get_precision('Stock Weight'),
        help="The line gross weight in Kg.")
    total_weight_net = fields.Float(
        compute=_compute_total_weight_net, string='Line net weight',
        digits_compute=dp.get_precision('Stock Weight'), store=True,
        help="The line net weight in Kg.")
    total_volume = fields.Float(
        compute=_compute_total_volume, string='Line volume', store=True,
        help="The line volume in m3.")
    company_id = fields.Many2one(
        comodel_name="res.company", related="distribution.company_id",
        store=True,
    )

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, "%s / %s" % (
                record.picking_id.name, record.product_id.name_get()[0][1])))
        return res


class PoiPurchaseImportsPicking(models.Model):
    _name = "poi.purchase.imports.picking"
    _description = "Purchase cost distribution Line"

    @api.one
    @api.depends('picking_id')
    def _compute_total_amount(self):
        total = 0.0
        for moves in self.picking_id.move_lines_related:
            total += moves.price_unit * moves.product_qty
        self.total_amount = total

    company_id = fields.Many2one(related='distribution.company_id', string=u'Compañia', readonly=True)
    name = fields.Char(string='Nombre')
    picking_id = fields.Many2one(
        'stock.picking', string='Transferencia')
    distribution = fields.Many2one(
        comodel_name='poi.purchase.imports', string='Cost distribution',
        ondelete='cascade', required=True)
    location_id = fields.Many2one(
        'stock.location', string='Origen', related='picking_id.location_id',
        store=True)
    location_dest_id = fields.Many2one(
        'stock.location', string='Destino', related='picking_id.location_dest_id',
        store=True)
    state = fields.Selection(string="Estado", related='picking_id.state')
    currency_id = fields.Many2one('res.currency', string='Divisa',
                                  required=True, readonly=True,
                                  related='distribution.currency_id', track_visibility='always')
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True,
                                          help='Utility field to express amount currency', string="Divisa")
    total_amount = fields.Monetary(
        compute=_compute_total_amount, string='Total Compra',
        digits_compute=dp.get_precision('Account'))


# Mas usado para el calculo intermedio
class PoiPurchaseImportsLineExpense(models.Model):
    _name = "poi.purchase.imports.line.expense"
    _description = "Purchase cost distribution line expense"

    distribution_line = fields.Many2one(
        comodel_name='poi.purchase.imports.line',
        string='Cost distribution line', ondelete="cascade")
    distribution_expense = fields.Many2one(
        comodel_name='poi.purchase.imports.expense',
        string='Distribution expense', ondelete="cascade")

    split_method = fields.Selection(SPLIT_METHOD, string='Metodo de Calculo', default='by_quantity')
    # type = fields.Many2one(
    #    'purchase.expense.type', string='Expense type',
    #    related='distribution_expense.type')
    expense_amount = fields.Float(
        string='Costo Aplicado', default=0.0,
        digits_compute=dp.get_precision('Account'))
    cost_ratio = fields.Float('Unit cost', default=0.0)
    company_id = fields.Many2one(
        comodel_name="res.company", related="distribution_line.company_id",
        store=True,
    )


class PoiPurchaseImportsExpense(models.Model):
    _name = "poi.purchase.imports.expense"
    _description = "Purchase cost distribution expense"
    _rec_name = "display_name"

    @api.one
    @api.depends('distribution', 'distribution.cost_lines')
    def _get_imported_lines(self):
        self.imported_lines = self.env['poi.purchase.imports.line']
        self.imported_lines |= self.distribution.cost_lines

    distribution = fields.Many2one(
        comodel_name='poi.purchase.imports', string='Cost distribution',
        select=True, ondelete="cascade", required=True)

    ref = fields.Char(string="Reference")

    # type = fields.Many2one(
    #    comodel_name='purchase.expense.type', string='Expense type',
    #    select=True, ondelete="restrict", required=True)

    calculation_method = fields.Selection(
        string='Calculation method', related='split_method',
        readonly=True)

    imported_lines = fields.Many2many(
        comodel_name='poi.purchase.imports.line',
        string='Imported lines', compute='_get_imported_lines')

    affected_lines = fields.Many2many(
        comodel_name='poi.purchase.imports.line', column1="expense_id",
        relation="poi_distribution_expense_aff_rel", column2="line_id",
        string='Affected lines',
        help="Put here specific lines that this expense is going to be "
             "distributed across. Leave it blank to use all imported lines.",
        domain="[('id', 'in', imported_lines[0][2])]")
    expense_amount = fields.Float(
        string='Costo Aplicado', digits_compute=dp.get_precision('Account'),
        required=True)
    invoice_line = fields.Many2one(
        comodel_name='account.invoice.line', string="Lineas de Factura",
        domain="[('invoice_id.type', '=', 'in_invoice'),"
               "('invoice_id.state', 'in', ('open', 'paid'))]")
    invoice_id = fields.Many2one(
        comodel_name='account.invoice', string="Invoice")
    display_name = fields.Char(compute="_compute_display_name", store=True)
    company_id = fields.Many2one(
        comodel_name="res.company", related="distribution.company_id",
        store=True,
    )
    # Nuevos campos adicionados
    product_qty = fields.Float(
        string='Cantidad', digits_compute=dp.get_precision('Product Unit of Measure'),
        required=True, default=1.0)
    partner_id = fields.Many2one(comodel_name='res.partner', string="Proveedor",
                                 domain=[('supplier', '=', True), ('active', '=', True)])
    product_id = fields.Many2one(comodel_name='product.product', string="Producto/Servicio",
                                 domain=[('landed_cost_ok', '=', True), ('active', '=', True)])
    name = fields.Char(string="Descripción de Gasto", required=True)
    date = fields.Date(string='Fecha', required=True, readonly=False, select=True, default=fields.Date.context_today)
    currency_id = fields.Many2one('res.currency', string='Divisa', required=True, readonly=False, default=lambda self: self.env.user.company_id.currency_id)
    expense_line_tax_ids = fields.Many2many('account.tax', string='Impuestos',
                                            domain=[('type_tax_use', '=', 'purchase'), '|', ('active', '=', False),
                                                    ('active', '=', True)], oldname='expense_line_tax_id')

    split_method = fields.Selection(SPLIT_METHOD, string='Metodo de Calculo', default='by_quantity')
    state = fields.Selection(string="Estado Factura", related='invoice_id.state')
    price_subtotal = fields.Monetary(string="Aplicado A Gasto", related='invoice_line.price_subtotal')
    quants_id = fields.Many2many('stock.quant', string='Stock')
    pickings_id = fields.Many2many('stock.picking', string='Transferencia')

    landed_cost_id = fields.Many2one("stock.landed.cost", string="Costos en Destino")
    opcion_gasto = fields.Selection([
        ('lote', 'Stock'),
        ('picking', 'Transferencia'),
    ], default=lambda self: self._context.get('opcion_gasto', 'picking'))
    # @api.one
    # @api.depends('distribution', 'type', 'expense_amount')
    # def _compute_display_name(self):
    #    self.display_name = "%s: %s (%s)" % (
    #        self.distribution.name, self.split_method,
    #        formatLang(self.env, self.expense_amount,
    #                   currency_obj=self.distribution.currency_id))

    # @api.onchange('type')
    # def onchange_type(self):
    #    if self.type and self.type.default_amount:
    #        self.expense_amount = self.type.default_amount

    @api.multi
    def unlink(self):
        for c in self:
            if c.invoice_id:
                if c.invoice_id.state in ('open', 'paid') and c.landed_cost_id:
                    raise UserError(_('No puede borrar el gasto su factura esta en estado "Abierto" o se ha registrado su gasto'))
                elif c.invoice_id.state in ('open', 'paid'):
                    c.invoice_id.imports = False
                    c.invoice_line.imports = False
                else:
                    c.invoice_id.imports = False
                    c.invoice_line.imports = False
                    c.invoice_id.unlink()
        return super(PoiPurchaseImportsExpense, self).unlink()

    @api.onchange('invoice_line')
    def onchange_invoice_line(self):
        self.invoice_id = self.invoice_line.invoice_id.id
        self.expense_amount = self.invoice_line.price_subtotal

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.split_method = self.product_id.split_method
        self.name = self.product_id.name
        self.expense_amount = self.product_id.standard_price
        self.expense_line_tax_ids = self.product_id.supplier_taxes_id.ids

    # @api.multi
    # def button_duplicate(self):
    #     for expense in self:
    #         expense.copy()

    ## Crear Factura por Linea de Gasto de Importación que no ha sido
    # importado desde facturas normales
    def _prepare_invoice_line_from_po_line(self, line):
        qty = line.product_qty
        taxes = line.expense_line_tax_ids
        invoice_line_tax_ids = self.invoice_id.fiscal_position_id.map_tax(taxes)
        invoice_line = self.env['account.invoice.line']
        data = {
            # 'purchase_line_id': line.id,
            'name': line.name,
            'origin': self.distribution.name,
            'uom_id': line.product_id.uom_id.id,
            'product_id': line.product_id.id,
            'account_id': invoice_line.with_context(
                {'journal_id': self.distribution.journal_id.id, 'type': 'in_invoice'})._default_account(),
            'price_unit': line.currency_id.compute(line.expense_amount, self.invoice_id.currency_id, round=False),
            'quantity': 1,
            'discount': 0.0,
            # 'account_analytic_id': line.account_analytic_id.id,
            'invoice_line_tax_ids': [(6, 0, invoice_line_tax_ids.ids)],
            'invoice_id': self.invoice_id.id,
        }
        account = invoice_line.get_invoice_line_account('in_invoice', line.product_id,
                                                        self.invoice_id.fiscal_position_id, self.env.user.company_id)
        if account:
            data['account_id'] = account.id
        return data

    # Load all unsold PO lines
    @api.multi
    def create_invoice(self):
        ctx = self._context.copy()
        if not self.distribution.journal_id:
            raise UserError(_('Por favor definir el Diario Contable'))

        if self.invoice_id:
            view_id = self.env.ref('account.invoice_supplier_form').id
            return {
                'name': _('Create invoice/bill'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.invoice',
                'view_id': view_id,
                'context': ctx,
                'res_id': self.invoice_id.id,
                'target': 'current',
            }
        val_invoice = {
            'partner_id': self.partner_id.id,
            'type': 'in_invoice',
            'imports': self.distribution.id,
            'currency_id': self.currency_id.id,
            'journal_id': self.distribution.journal_id.id,
            'razon': self.partner_id.razon,
            'nit': self.partner_id.nit
        }
        invoice_id = self.env['account.invoice'].create(val_invoice)
        invoice_id.partner_id = self.partner_id.id
        self.invoice_id = invoice_id.id
        invoice_id.currency_id = self.currency_id.id
        new_lines = self.env['account.invoice.line']
        for line in self:
            # Load a PO line only once
            data = self._prepare_invoice_line_from_po_line(line)
            self.env['account.invoice.line'].create(data)
            #new_line = new_lines.new(data)
            #new_line._set_additional_fields(invoice_id)
            #new_lines += new_line
        #invoice_id.invoice_line_ids += new_lines
        invoice_id.compute_taxes()
        for invoice_line in invoice_id.invoice_line_ids:
            self.invoice_line = invoice_line.id
            if self.distribution.cost_lines:
                self.affected_lines = [(6, 0, self.distribution.cost_lines.ids)]

        return {}

        # Load all unsold PO lines

    @api.multi
    def apply_landed_cost(self):
        if not self.distribution.journal_id:
            raise UserError(_('Por favor definir el Diario Contable'))

        if not self.invoice_id:
            raise UserError(
                _('Antes de Aplicar el costo al inventario\nDebe generar la factura de Costo de Importaciones'))

        if not self.invoice_id.state in ('open', 'paid'):
            raise UserError(
                _(u'Antes de Aplicar el gasto la factura tiene que estar en estado válido o pagado'))

        ctx = self._context.copy()
        if self.landed_cost_id:
            view_id = self.env.ref('stock_landed_costs.view_stock_landed_cost_form').id
            return {
                'name': _('Costos en Destino'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.landed.cost',
                'view_id': view_id,
                'context': ctx,
                'res_id': self.landed_cost_id.id,
                'target': 'new',
            }

        # Ejecutar si tienes costos en destino por picking
        # Evitar que se valore por dos casos en caso de ser ambos no permite generar el coste en destino
        if self.pickings_id and not self.quants_id:
            # Verificar si los quants a valorar ya corresponden a
            # Una ubicación de valoración de inventarios
            # 05.02.2017 No es necesario aplicar funcionalidad de transito
            # Odoo aplica las ubicaciónes en transito donde de forma
            # Nativa ya no genera contabilidad y los costos aplicados
            # Al albaran en transito solo genera el asiento contra la cuenta de valoración de las ventas
            # En el entendido que cuando se venda el producto la cuenta de valoración de las ventas se vea afectado tambien
            for picking in self.pickings_id:
                for moves in picking.move_lines:
                    for quant in moves.quant_ids:
                        if quant.location_id.usage == 'transit':
                            raise UserError(_(
                                'No puede aplicar costos al chasis "%s" en la ubicación "%s" ya que es una ubicación de transito') % (
                                            quant.lot_id.name, quant.location_id.name))
                        if self.invoice_id.tipo_fac == '12':
                            self.invoice_id.lot_dui_id = quant.lot_id.id

            # Crear cabezara de costos en destinos
            val_landed = {
                'date': self.distribution.date,
                'picking_ids': [(6, 0, self.pickings_id.ids)],
                'quant_ids': [(6, 0, self.quants_id.ids)],
                'account_journal_id': self.distribution.journal_id.id,
            }
            cost_id = self.env['stock.landed.cost'].create(val_landed)
            amount_currency = self.currency_id.compute(self.price_subtotal * self.product_qty,
                                                       self.env.user.company_id.currency_id)
            val_lines_landed = {
                'cost_id': cost_id.id,
                'name': self.product_id.name,
                'product_id': self.product_id.id,
                'split_method': self.split_method and self.split_method or self.product_id.split_method,
                'price_unit': amount_currency,
                'account_id': self.product_id.property_account_expense_id and self.product_id.property_account_expense_id.id or self.product_id.categ_id.property_account_expense_categ_id.id,
                'imports_expense': self.id,
            }
            self.env['stock.landed.cost.lines'].create(val_lines_landed)
            cost_id.compute_landed_cost()
            cost_id.button_validate()
            self.landed_cost_id = cost_id.id
            # Al generar el costo en destino
            # visualizamos el resultado
            view_id = self.env.ref('stock_landed_costs.view_stock_landed_cost_form').id
            return {
                'name': _('Costos en Destino'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.landed.cost',
                'view_id': view_id,
                'context': ctx,
                'res_id': cost_id.id,
                'target': 'new',
            }

        # Ejecutar si tiene costos en destino por
        # Lote
        elif self.quants_id and not self.pickings_id:
            for quants in self.quants_id:
               if quants.location_id.usage == 'transit':
                   raise UserError(_('No puede aplicar costos al chasis "%s" en la ubicación "%s" ya que es una ubicación de transito') % (quants.lot_id.name, quants.location_id.name))
            ## Asignar Lote Chasis a Factura DUI
            for quant in self.quants_id:
                if self.invoice_id.tipo_fac == '12':
                    self.invoice_id.lot_dui_id = quant.lot_id.id
                    quant.invoice_id = self.invoice_id.id
            # Crear cabezara de costos en destinos
            val_landed = {
                'date': self.distribution.date,
                'picking_ids': [(6, 0, self.pickings_id.ids)],
                'quant_ids': [(6, 0, self.quants_id.ids)],
                'account_journal_id': self.distribution.journal_id.id,
            }
            cost_id = self.env['stock.landed.cost'].create(val_landed)
            amount_currency = self.currency_id.compute(self.price_subtotal * self.product_qty,
                                                       self.env.user.company_id.currency_id)
            val_lines_landed = {
                'cost_id': cost_id.id,
                'name': self.product_id.name,
                'product_id': self.product_id.id,
                'split_method': self.split_method and self.split_method or self.product_id.split_method,
                'price_unit': amount_currency,
                'account_id': self.product_id.property_account_expense_id and self.product_id.property_account_expense_id.id or self.product_id.categ_id.property_account_expense_categ_id.id,
                'imports_expense': self.id,
            }
            self.env['stock.landed.cost.lines'].create(val_lines_landed)
            cost_id.compute_landed_cost_quant()
            cost_id.button_validate_quant()
            self.landed_cost_id = cost_id.id

            # Al generar el costo en destino
            # visualizamos el resultado
            view_id = self.env.ref('stock_landed_costs.view_stock_landed_cost_form').id
            return {
                'name': _('Costos en Destino'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.landed.cost',
                'view_id': view_id,
                'context': ctx,
                'res_id': cost_id.id,
                'target': 'new',
            }
        else:
            raise UserError(
                _('No puede aplicar el costeo a un albarán y serie al mismo tiempo!\nSolo debe estar seleccionado uno'))




