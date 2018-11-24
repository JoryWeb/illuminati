# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, exceptions, _


# Neumaticos
class ModeloNeumaticosToyosa(models.Model):
    _name = 'modelo.neumaticos.toyosa'
    name = fields.Char("Name")
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "El nombre ya existe !"),
    ]


class MarcaNeumaticosToyosa(models.Model):
    _name = 'marca.neumaticos.toyosa'
    name = fields.Char("Name")
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "El nombre ya existe !"),
    ]


class PrNeumaticosToyosa(models.Model):
    _name = 'pr.neumaticos.toyosa'
    name = fields.Char("Name")
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "El nombre ya existe !"),
    ]


class SbuNeumaticosToyosa(models.Model):
    _name = 'sbu.neumaticos.toyosa'
    name = fields.Char("Name")
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "El nombre ya existe !"),
    ]


class UsoNeumaticosToyosa(models.Model):
    _name = 'uso.neumaticos.toyosa'
    name = fields.Char("Nombre de Uso")
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "El nombre ya existe !"),
    ]


# Atributos Neumaticos

class AtributoListaNeumaticosToyosa(models.Model):
    _name = 'atributo.lista.neumaticos.toyosa'
    name = fields.Char("Name")
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "El nombre ya existe !"),
    ]


class AtributoNeumaticosToyosa(models.Model):
    _name = 'atributo.neumaticos.toyosa'
    product_id = fields.Many2one("product.template", "Producto")
    atributo = fields.Many2one("atributo.lista.neumaticos.toyosa", "Atributo")
    valor = fields.Char("Valor")
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "El nombre ya existe !"),
    ]


# Check lists
class CheckListToyosa(models.Model):
    _name = 'check.list.toyosa'
    product_id = fields.Many2one("product.template", "Producto")
    name = fields.Char("Nombre")
    item_id = fields.Many2one("check.list.toyosa.items", 'Items')
    activo = fields.Boolean("Aplica")
    imp = fields.Boolean('Importado', default=False)
    price = fields.Float('Precio', default=0)

    @api.model
    def _install_poi_x_toyosa_checklist(self):
        items_obj = self.env['check.list.toyosa.items']
        items_ids = items_obj.search([])
        items = {}
        for i in items_ids:
            items.update({i.name: i.id})
        # Find records with empty firstname and lastname
        records = self.search([("item_id", "=", False),
                               ("name", "!=", False), ])
        for r in records:
            if r.name in items:
                r.item_id = items[r.name]
            else:
                item_id = items_obj.create({'name': r.name})
                items.update({item_id.name: item_id.id})
        # Force calculations there


class CheckListToyosaItems(models.Model):
    _name = 'check.list.toyosa.items'

    name = fields.Char("Nombre")


# Atributos Vehiculos
class AtributoNombreToyosa(models.Model):
    _name = 'atributo.nombre.toyosa'
    name = fields.Char("Nombre")
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "El nombre ya existe !"),
    ]


class AtributoValorToyosa(models.Model):
    _name = 'atributo.valor.toyosa'
    name = fields.Char("Nombre")


class AtributoToyosa(models.Model):
    _name = 'atributo.toyosa'
    product_id = fields.Many2one("product.template", "Producto")
    name = fields.Many2one("atributo.nombre.toyosa", string="Nombre")
    atributo_ids = fields.Char(string=u"Valor")


class ModeloRepuestosToyosa(models.Model):
    _name = 'modelo.repuestos.toyosa'
    name = fields.Char("Nombre")
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "El nombre ya existe !"),
    ]


class MarcaToyosa(models.Model):
    _name = 'marca.toyosa'
    name = fields.Char("Nombre")
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "El nombre ya existe !"),
    ]


class ModeloToyosa(models.Model):
    _name = 'modelo.toyosa'
    image = fields.Binary("Imagen", attachment=True,
                          help="This field holds the image used as image for the product, limited to 1024x1024px.")
    image_medium = fields.Binary("Medium-sized image", attachment=True,
                                 help="Medium-sized image of the product. It is automatically " \
                                      "resized as a 128x128px image, with aspect ratio preserved, " \
                                      "only when the image exceeds one of those sizes. Use this field in form views or some kanban views.")
    image_small = fields.Binary("Small-sized image", attachment=True,
                                help="Small-sized image of the product. It is automatically " \
                                     "resized as a 64x64px image, with aspect ratio preserved. " \
                                     "Use this field anywhere a small image is required.")
    name = fields.Char(u"Modelo")
    marca = fields.Many2one("marca.toyosa", "Marca")


class KatashikiModel(models.Model):
    _name = 'katashiki.model'
    name = fields.Char("Nombre")


class KatashikiProperty(models.Model):
    _name = 'katashiki.property'
    code = fields.Char(u"Código")
    name = fields.Char("Nombre")


class KatashikiToyosa(models.Model):
    _name = 'katashiki.toyosa'
    name = fields.Char(u"Código")
    # model = fields.Many2one("modelo.toyosa", "Modelo")
    modelo = fields.Many2one("modelo.toyosa", "Modelo")
    property_1 = fields.Many2one("katashiki.property", "Propiedad 1")
    property_2 = fields.Many2one("katashiki.property", "Propiedad 2")
    property_3 = fields.Many2one("katashiki.property", "Propiedad 3")
    property_4 = fields.Many2one("katashiki.property", "Propiedad 4")
    property_5 = fields.Many2one("katashiki.property", "Propiedad 5")
    property_6 = fields.Many2one("katashiki.property", "Propiedad 6")
    property_7 = fields.Many2one("katashiki.property", "Propiedad 7")
    property_8 = fields.Many2one("katashiki.property", "Propiedad 8")
    property_9 = fields.Many2one("katashiki.property", "Propiedad 9")
    property_10 = fields.Many2one("katashiki.property", "Propiedad 10")
    property_11 = fields.Many2one("katashiki.property", "Propiedad 11")
    property_12 = fields.Many2one("katashiki.property", "Propiedad 12")


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.one
    @api.depends('categ_id')
    def _get_category_root(self):

        last_categ = self.categ_id
        while last_categ.parent_id:
            last_categ = last_categ.parent_id

        self.category_root = last_categ.id

    accessory = fields.Boolean("Accesorio")
    grupo = fields.Char("Grupo",
                        help="Este campo es utilizado para agrupar los repuestos TOYOTA de acuerdo al área y función que cumplen")
    katashiki = fields.Many2one("katashiki.toyosa", string=u"Código Modelo")
    modelo = fields.Many2one("modelo.toyosa", "Modelo")
    marca = fields.Many2one("marca.toyosa", string=u"Marca",
                            related='modelo.marca', readonly=True, store=True)
    master_padre = fields.Many2many("product.product", "master_padre_toyosa_rel", "model_id", "parent_id",
                                    "Master Asociados")
    n_llaves = fields.Integer(u"N° de llaves")
    atributo_line = fields.One2many('atributo.toyosa', 'product_id', string="Atributos", copy=True)
    checklist_line = fields.One2many('check.list.toyosa', 'product_id', string="Check List", copy=True)
    atributo_neumaticos_line = fields.One2many('atributo.neumaticos.toyosa', 'product_id',
                                               string=u"Atributo Neumáticos", copy=True)
    modelo_neumatico = fields.Many2one("modelo.neumaticos.toyosa", "Modelo Neumáticos")
    marca_neumatico = fields.Many2one("marca.neumaticos.toyosa", "Marca")
    origen_neumatico = fields.Many2one("res.country", "Origen")
    pr_neumatico = fields.Many2one("pr.neumaticos.toyosa", "Pr")
    sbu_neumatico = fields.Many2one("sbu.neumaticos.toyosa", "Sbu")
    uso_neumatico_e = fields.Many2many("uso.neumaticos.toyosa", 'product_neumatico_uso_rel', 'product_id', 'uso_id',
                                       string="Uso")
    aro_neumatico = fields.Float("Aro")
    largo = fields.Float("Largo")
    uom_largo = fields.Many2one("product.uom", "Unidad de Medida")
    alto = fields.Float("Alto")
    uom_alto = fields.Many2one("product.uom", "Unidad de Medida")
    ancho = fields.Float("Ancho")
    uom_ancho = fields.Many2one("product.uom", "Unidad de Medida")
    uom_volumen = fields.Many2one("product.uom", "Unidad de Medida")
    uom_peso = fields.Many2one("product.uom", "Unidad de Medida")
    segmento = fields.Char("Segmento")
    garantia_km = fields.Char("Garantía en Kilometros")
    garantia_horas = fields.Integer("Garantía por Horas")
    activity_id = fields.Many2one('company.activity', string="Actividad Economica permitida",
                                  help="Actividad Economica permitida al momento de facturar los productos")
    category_root = fields.Many2one("product.category", string=u'Categoría raíz', compute='_get_category_root',
                                    readonly=True, store=True)
    product_dis_id = fields.One2many('product.template.discount', 'product_tmpl_id',
                                     'Productos Validos Para el Descuento')

    @api.one
    @api.constrains('name', 'default_code')
    def _check_name(self):
        if self.name:
            count = self.search_count([("name", "=", self.name)])
            if count > 1 and self.name:
                raise exceptions.ValidationError(
                    _("Producto %s ya existe!") % (self.name))
        if self.default_code:
            count = self.search_count([("default_code", "=", self.default_code)])
            if count > 1 and self.default_code:
                raise exceptions.ValidationError(
                    _("Producto %s con referencia %s ya existe!") % (self.name, self.default_code))

    @api.multi
    def action_view_lot_chasis(self):
        result = self._get_act_window_dict('poi_x_toyosa.action_poi_chasis_inventory_report_report_all')
        result['context'] = "{'default_product_id': %d}" % self.id
        result['domain'] = "[('product_id.product_tmpl_id','in',[" + ','.join(map(str, [self.id])) + "])]"
        return result


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def action_view_lot_chasis(self):
        result = self.product_tmpl_id._get_act_window_dict('poi_x_toyosa.action_poi_chasis_inventory_report_report_all')
        result['context'] = "{'default_product_id': %d}" % self.product_tmpl_id.id
        result['domain'] = "[('product_id.product_tmpl_id','in',[" + ','.join(
            map(str, [self.product_tmpl_id.id])) + "])]"
        return result


# Categoria de producto para establecer actividad economica restringida
class ProductCategory(models.Model):
    _inherit = "product.category"

    activity_id = fields.Many2one('company.activity', string="Actividad Economica permitida",
                                  help="Actividad Economica permitida al momento de facturar los productos")

    type_product = fields.Selection(
        string="Tipo de Producto",
        selection=[
            ('neu', 'Neumaticos'),
            ('rep', 'Repuesto'),
            ('aut', 'Automovil'),
        ],
    )


class ProductTemplateDiscount(models.Model):
    _name = 'product.template.discount'

    product_tmpl_id = fields.Many2one('product.template', 'Producto')
    year_id = fields.Many2one('anio.toyosa', 'Año')
    discount = fields.Boolean('Sin Descuento', default=True)
    price = fields.Float('Precio', readonly=True)
