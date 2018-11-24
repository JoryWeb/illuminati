# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # @api.depends('product_variant_ids', 'product_variant_ids.volume')
    # def _compute_volume(self):
    #     unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
    #     for template in unique_variants:
    #         template.volume = template.product_variant_ids.volume
    #     for template in (self - unique_variants):
    #         template.volume = 0.0
    #
    # @api.one
    # def _set_volume(self):
    #     if len(self.product_variant_ids) == 1:
    #         self.product_variant_ids.volume = self.volume

    property_stock_account_import = fields.Many2one(
        'account.account', u'Cuenta Importación de Existencias',
        company_dependent=True, domain=[('deprecated', '=', False)],
        help="Definir las cuentas contables de transito de stock para importaciones "
             "Aplicables a los productos que ingresan por orden de importacion.")

    @api.multi
    def _get_product_accounts(self):
        """ Add the stock accounts related to product to the result of super()
        @return: dictionary which contains information regarding stock accounts and super (income+expense accounts)
        """
        accounts = super(ProductTemplate, self)._get_product_accounts()
        res = self._get_asset_accounts()
        accounts.update({
            'import_stock_input': self.property_stock_account_import or self.categ_id.property_stock_account_import_categ_id,
        })
        return accounts

class ProductCategory(models.Model):
    _inherit = 'product.category'
    property_stock_account_import_categ_id = fields.Many2one(
        'account.account', u'Cuenta Importación de Existencias', company_dependent=True,
        domain = [('deprecated', '=', False)], oldname="property_stock_account_import_categ",
        help = u"La cuenta es aplicable a metodos real y ponderado y aplica a todos los productos asignados bajo esta categoría")

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_fifo_candidates_in_move_location(self, location_id):
        """ Buscar movimientos por ubicacion
        """
        self.ensure_one()
        domain = [('product_id', '=', self.id), ('remaining_qty', '>', 0.0), ('location_dest_id', '=', location_id)] + self.env['stock.move']._get_in_base_domain()
        candidates = self.env['stock.move'].search(domain, order='date, id')
        return candidates

    def _get_fifo_candidates_in_move_location_lot(self, location_id, lot_id):
        """ Buscar movimientos por ubicacion
        """
        self.ensure_one()
        domain = [('product_id', '=', self.id), ('remaining_qty', '>', 0.0), ('location_dest_id', '=', location_id)] + self.env['stock.move']._get_in_base_domain()
        candidates = self.env['stock.move'].search(domain, order='date, id')
        for candi in candidates:
            for lines in candi.move_line_ids:
                if lines.lot_id.id == lot_id:
                    return candi
        return candidates