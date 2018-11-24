##############################################################################
#    
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2011 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Author: Nicolas Bustillos
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

from openerp.osv import fields, osv
from lxml import etree

class pret_product_type(osv.osv):
    _name = "pret.product.type"
    _description = "Tipo de Producto"
    _columns = {        
        'name': fields.char('Tipo de Producto', size=60, translate=True, required=True, help="Introduzca el tipo de producto"),
        'fields': fields.many2many ("ir.model.fields","product_type_fields_rel","type_fields_id","fields_id","Campos", domain = [('name','like','x_%')]),
        'ref': fields.char('Ref.:', size=64),
        'consideracion': fields.html('Introduzca la consideracion de la propuesta'),
        'punto_uno': fields.char('1.', size=64),
        'impuestos_ley': fields.char('Impuesto de ley', size=64),
        'consideraciones_propuesta': fields.html('Consideraciones sobre la propuesta'),
        'punto_dos': fields.char('2.', size=64),
        'especificaciones': fields.html('Especificaciones'),
        'punto_tres': fields.char('3.', size=64),
        'carpeta': fields.html('Carpeta de Compresion'),
        'plazo_entrega': fields.html('Plazo entrega'),
        'firma': fields.html('Firma'),   
        'img_consideracion' : fields.binary('Foto'),
        'img_footer' : fields.binary('Img. Pie de Página'),
        'img_sociales' : fields.binary('Img. Redes Sociales'),
    }
    #ToDo. Forzar actualización del addon cada que se modifique 'in_rep_ventas'
  
    ###############################
    _order = "name"     
     
pret_product_type()

class product_category(osv.osv):
    _inherit = 'product.category'

    _columns = {
        'in_rep_ventas': fields.boolean('Informe Ventas', help="Visible como columna adicional en el tablero de Informe de Ventas. Requiere reinstalación del addon."),
        'udm_rep_ventas': fields.char('UdM en Reporte', size=8, help=u"Unidad de medida tal como se vera en la cabecera de columna del Reporte de división Ventas"),
        'in_rep_cubiertas': fields.boolean('Agregar al Dashboard de Cubiertas', help="Agrega una Columna adicional al tablero de Informe de Cubiertas, Requiere reinstalar el Addon"),
        'udm_rep_cubiertas': fields.char('UdM en Reporte', size=8, help=u"Unidad de medida tal como se vera en la cabecera de columna del Reporte de división Cubiertas")
    }


class sale_order(osv.osv):
    _inherit = 'sale.order'
    _columns = {
        'product_type': fields.many2one('pret.product.type', 'Tipo producto', required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
    }

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        res = super(sale_order, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        if view_type == 'form':
            x_ids = []
            cr.execute("""select id from ir_model_fields
                          where model = %s and name like %s """,
                           ('sale.order','x%',))
            for record in cr.fetchall():
                x_ids.append(record[0])

            fields_pool=self.pool.get('ir.model.fields') #Selecciona los campos de la tabla pret_product_type_fields
            product_pool=self.pool.get('pret.product.type') #Selecciona los campos de la tabla pret_product_type
            doc = etree.XML(res['arch'])#se asigna a doc el formato arch en xml a formato python para poder manejarlo
            field_ids = x_ids
            product_ids= product_pool.search(cr, uid, [])#ids de pret_product_type - los tipos de productos
            products_type=[]
            products_field={}

            for field in fields_pool.browse(cr,uid,field_ids):
                products_field[field.name]=[]#diccionario vacio de pret_product_type_fields

            for type_product in product_pool.browse(cr,uid,product_ids):
                for field in type_product.fields:
                    products_field[field.name].append(type_product.id) #se llena el diccionario con los tipo de productos q corresponden a cada campo

            ############AÑADE CAMPOS XML DINAMICOS#########################
            for field in fields_pool.browse(cr,uid,field_ids):#recorre los campos pret_product_type_fields
                placeholder = doc.xpath("//field[@name='product_type']")
                if len(placeholder):
                    placeholder = placeholder[0]
                    field_bdids = x_ids
                    fields_bd = self.pool.get('ir.model.fields')
                    for ret_line in fields_bd.browse(cr,uid,field_bdids):
                        if ret_line['name']==field.name:
                            loc_id = ret_line['id']
                            loc_field = ret_line['name']
                            loc_desc = ret_line['field_description']
                            loc_type = ret_line['ttype']

                            if loc_type=='selection':
                                loc_selection=ret_line['selection']
                                loc_selection=loc_selection.replace("',", "', u")

                            if str(loc_field):
                                placeholder.addnext(etree.Element('field', {'name': str(loc_field), 'readonly': "1"}))
                                placeholder = placeholder.getnext()
                                if loc_type == 'selection':
                                    res['fields'][str(loc_field)] = {'digits': (16, 3), 'selectable': True, 'readonly': True, 'type': str(loc_type), 'selection': eval(loc_selection), 'string': str(loc_desc), 'views': {}}
                                else:
                                    res['fields'][str(loc_field)] = {'digits': (16, 3), 'selectable': True, 'readonly': True, 'type': str(loc_type), 'string': str(loc_desc), 'views': {}}

                                res['fields'][str(str(loc_desc))] = {'digits': (16, 3), 'selectable': True, 'readonly': True, 'type': str(loc_type), 'string': str(loc_desc), 'views': {}}
                                doc.xpath("//field[@name='"+str(field.name)+"']")[0].attrib['attrs']="{'invisible': [('state','in',('draft','sent'))]}"#Aplica condición al campo especificado
                                doc.xpath("//field[@name='"+str(field.name)+"']")[0].attrib['modifiers'] = '{"invisible": [["product_type","not in",%s]]}' % (str(products_field[field.name]))
            res['arch'] = etree.tostring(doc)#vuelve al formato xml
        return res

sale_order()    
########################################################################################