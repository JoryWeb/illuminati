# (c) 2015 Oihane Crucelaegui - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api, exceptions, _

class StockInventoryFake(object):
    def __init__(self, inventory, product=None, lot=None):
        self.id = inventory.id
        self.location_id = inventory.location_id
        self.product_id = product
        self.lot_id = lot
        self.partner_id = inventory.partner_id
        self.package_id = inventory.package_id
        self.company_id = inventory.company_id

class StockInventory(models.Model):
    _inherit = "stock.inventory"

    @api.model
    def _get_available_filters(self):
        res = super(StockInventory, self)._get_available_filters()
        res.append(('file', _('By File')))
        res.append(('category', _(u'Por Categoría')))
        return res

    @api.multi
    @api.depends('import_lines')
    def _file_lines_processed(self):
        for record in self:
            processed = True
            if record.import_lines:
                processed = any((not line.fail or
                                 (line.fail and
                                  line.fail_reason != _('No processed')))
                                for line in record.import_lines)
            record.processed = processed

    imported = fields.Boolean('Imported')
    import_lines = fields.One2many('stock.inventory.import.line',
                                   'inventory_id', string='Imported Lines')
    filter = fields.Selection(_get_available_filters,
                              string='Selection Filter',
                              required=True)
    processed = fields.Boolean(string='Has been processed at least once?',
                               compute='_file_lines_processed')

    categ_ids = fields.Many2many(
        comodel_name='product.category', relation='rel_inventories_categories',
        column1='inventory_id', column2='category_id', string='Categories')
    category_id = fields.Many2one("product.category", string=u"Categoría")

    barcode = fields.Char(u"Código Barras", help=u"Mantenga el cursor sobre este campo al momento de seleccionar los productos,"
                                                 u"En caso de lotes es necesario escaner el codigo de lote para registrar la cantidad")


    # Load all unsold PO lines
    @api.onchange('barcode')
    def barcode_change(self):
        if self.barcode:
            # Encontrar barcode producto
            product = self.env['product.product'].search([('barcode', '=', self.barcode)])
            # Encontrar barcode Lote
            lot_id = self.env['stock.production.lot'].search([('name', '=', self.barcode)])
            if product:
                new_lines = self.env['stock.inventory.line']
                ban = True
                for lines in self.line_ids:
                    if lines.product_id.id == product.id:
                        lines.product_qty = lines.product_qty + 1
                        ban = False
                        break

                if ban:
                    location_obj = self.env['stock.location']
                    location_ids = location_obj.search([('id', 'child_of', [self.location_id.id])])
                    domain = ' location_id in %s'
                    args = (tuple(location_ids.ids),)

                    domain += ' and product_id = %s'
                    args += (product.id,)

                    self._cr.execute('''SELECT product_id, sum(qty) as product_qty,
                                                     location_id,
                                                     lot_id as prod_lot_id,
                                                     package_id,
                                                     owner_id as partner_id
                                              FROM stock_quant WHERE''' + domain + '''
                                              GROUP BY product_id, location_id, lot_id, package_id, partner_id
                                           ''', args)
                    bal2 = True
                    for product_line in self._cr.dictfetchall():
                        # replace the None the dictionary by False, because falsy values are tested later on
                        for key, value in product_line.items():
                            if not value:
                                product_line[key] = False

                        qty_inicial = 0
                        if product.tracking == 'none':
                            qty_inicial = 1

                        data = {'product_id': product.id,
                                'theoretical_qty': product_line['product_qty'],
                                'prod_lot_id': product_line['prod_lot_id'],
                                'package_id': product_line['package_id'],
                                'product_uom_id': product.uom_id.id,
                                'product_qty': qty_inicial,
                                'inventory_id': self.id,
                                'location_id': self.location_id.id,
                                'company_id': self.company_id.id}
                        new_line = new_lines.new(data)
                        new_lines += new_line
                        self.line_ids += new_line
                        bal2 = False
                    if bal2:
                        data = {'product_id': product.id,
                                'theoretical_qty': 0,
                                'product_uom_id': product.uom_id.id,
                                'product_qty': 1,
                                'inventory_id': self.id,
                                'location_id': self.location_id.id,
                                'company_id': self.company_id.id}
                        new_line = new_lines.new(data)
                        new_lines += new_line
                        self.line_ids += new_line

            if lot_id:
                new_lines = self.env['stock.inventory.line']
                ban = True
                for lines in self.line_ids:
                    if lines.product_id.id == lot_id.product_id.id and lines.prod_lot_id.id == lot_id.id:
                        lines.product_qty = lines.product_qty + 1
                        ban = False
                        break
                if ban:
                    location_obj = self.env['stock.location']
                    location_ids = location_obj.search([('id', 'child_of', [self.location_id.id])])
                    domain = ' location_id in %s'
                    args = (tuple(location_ids.ids),)

                    domain += ' and lot_id = %s'
                    args += (lot_id.id,)

                    self._cr.execute('''SELECT product_id, sum(qty) as product_qty,
                                                     location_id,
                                                     lot_id as prod_lot_id,
                                                     package_id,
                                                     owner_id as partner_id
                                              FROM stock_quant WHERE''' + domain + '''
                                              GROUP BY product_id, location_id, lot_id, package_id, partner_id
                                           ''', args)
                    bal2 = True
                    for product_line in self._cr.dictfetchall():
                        # replace the None the dictionary by False, because falsy values are tested later on
                        for key, value in product_line.items():
                            if not value:
                                product_line[key] = False

                        qty_inicial = 0

                        data = {'product_id': product_line['product_id'],
                                'theoretical_qty': product_line['product_qty'],
                                'prod_lot_id': product_line['prod_lot_id'],
                                'package_id': product_line['package_id'],
                                'product_uom_id': product.uom_id.id,
                                'product_qty': qty_inicial,
                                'inventory_id': self.id,
                                'location_id': self.location_id.id,
                                'company_id': self.company_id.id}
                        new_line = new_lines.new(data)
                        new_lines += new_line
                        self.line_ids += new_line
                        bal2 = False
                    if bal2:
                        data = {'product_id': lot_id.product_id.id,
                                'theoretical_qty': 0,
                                'product_uom_id': lot_id.product_id.uom_id.id,
                                'product_qty': 0,
                                'inventory_id': self.id,
                                'location_id': self.location_id.id,
                                'company_id': self.company_id.id}
                        new_line = new_lines.new(data)
                        new_lines += new_line
                        self.line_ids += new_line

            self.barcode = ''
        return {}

    @api.multi
    def process_import_lines(self):
        """Process Inventory Load lines."""
        import_lines = self.mapped('import_lines')
        if not import_lines:
            raise exceptions.Warning(_("No existe lineas para procesar"))
        inventory_line_obj = self.env['stock.inventory.line']
        stk_lot_obj = self.env['stock.production.lot']
        product_obj = self.env['product.product']
        for line in import_lines:
            if line.fail:
                if not line.product:
                    prod_lst = product_obj.search([('default_code', '=',
                                                    line.code)])
                    if prod_lst:
                        product = prod_lst[0]
                    else:
                        line.fail_reason = _('No existe el codigo de producto')
                    continue
                else:
                    product = line.product
                lot_id = None
                if line.lot:
                    lot_lst = stk_lot_obj.search([('name', '=', line.lot)])
                    if lot_lst:
                        lot_id = lot_lst[0].id
                    else:
                        lot = stk_lot_obj.create({'name': line.lot,
                                                  'product_id': product.id})
                        lot_id = lot.id
                inventory_line_obj.create({
                    'product_id': product.id,
                    'product_uom_id': product.uom_id.id,
                    'product_qty': line.quantity,
                    'inventory_id': line.inventory_id.id,
                    'location_id': line.location_id.id,
                    'prod_lot_id': lot_id,
                    'company_id': self.company_id.id})
                line.write({'fail': False, 'fail_reason': _('Procesado')})
        return True

    @api.multi
    def action_done(self):
        for inventory in self:
            if not inventory.processed:
                raise exceptions.Warning(
                    _("Loaded lines must be processed at least one time for "
                      "inventory : %s") % (inventory.name))
            super(StockInventory, inventory).action_done()

    @api.model
    def _get_inventory_lines(self, inventory):
        if inventory.category_id:
            vals = []
            product_tmpl_obj = self.env['product.template']
            product_obj = self.env['product.product']
            cat_ids = []
            if inventory.category_id.type == 'normal':
                cat_ids.append(inventory.category_id.id)
            for cat in inventory.category_id.child_id:
                if cat.type == 'normal':
                    cat_ids.append(cat.id)
                for cat2 in cat.child_id:
                    if cat2.type == 'normal':
                        cat_ids.append(cat2.id)
                    for cat3 in cat2.child_id:
                        if cat3.type == 'normal':
                            cat_ids.append(cat3.id)
                        for cat4 in cat3.child_id:
                            if cat4.type == 'normal':
                                cat_ids.append(cat4.id)
                            for cat5 in cat4.child_id:
                                if cat5.type == 'normal':
                                    cat_ids.append(cat5.id)
                                for cat6 in cat5.child_id:
                                    if cat6.type == 'normal':
                                        cat_ids.append(cat6.id)
            product_tmpls = product_tmpl_obj.search(
                [('categ_id', 'in', cat_ids)])
            products = product_obj.search(
                [('product_tmpl_id', 'in', product_tmpls.ids)])
            for product in products:
                fake_inventory = StockInventoryFake(inventory, product=product)
                vals += super(StockInventory, self)._get_inventory_lines(
                    fake_inventory)
            return vals
        else:
            return super(StockInventory, self)._get_inventory_lines(inventory)