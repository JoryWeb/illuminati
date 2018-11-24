#!/usr/bin/env python
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2012 Poiesis Consulting (<http://www.poiesisconsulting.com>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import fields, models, api
from openerp.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_type = fields.Many2one('res.partner.type', 'Categoría Socio')
    nit = fields.Char('NIT', help=u"Número de Identificación Tributaria (o CI para facturación).")
    razon = fields.Char(u'Razón Social', help=u"Razón Social del cliente/proveedor.")
    razon_invoice = fields.Char(u'Razón Social para facturación', help=u"Razón Social para Facturación.")
    # Contactos
    ci = fields.Char('CI', size=8, help="Carnet de Identidad.")
    ci_dept = fields.Selection(
        [('lp', 'LP'), ('sc', 'SC'), ('ben', 'BE'), ('cb', 'CB'), ('ch', 'CH'), ('or', 'OR'), ('pa', 'PA'),
         ('po', 'PO'), ('tj', 'TJ'), ('ex', 'Extranjero')], 'Dept. CI', help="Lugar de emision Carnet de Identidad")
    extension = fields.Char(u'Extensión', help="Campo usado para las extesiones alfanumericas (Casos Duplicados).")
    fundaempresa = fields.Char('Registro Fundempresa', help="Numero de Registro en Fundempresa")

    def _check_unique_val(self):

        # ir_conf_pool=self.env['ir.config_parameter']
        # validate_unique_nit = ir_conf_pool.get_param('validate_unique_nit', False)
        # if not validate_unique_nit:
        #     return True

        if self.company_id.validate_unique_nit == 'not_valid':
            return True
        fields_check = [('nit', 'NIT'), ('ci', 'CI')]
        for partner in self:
            for field in fields_check:
                field_name = field[0]
                field_desc = field[1]

                val = getattr(partner, field_name)
                if val:
                    iden_ids = self.search_read([(field_name, '=', val), ('id', '!=', partner.id)])
                    if iden_ids:
                        iden_name = ''
                        for iden in iden_ids:
                            iden_name = iden_name + iden['display_name'] + '\n'
                        raise UserError(u'Ya existe un socio con el mismo %s. Puede buscarlo como: \n "%s"' % (
                            field_desc, iden_name))

        return True

    _constraints = [
        (_check_unique_val, 'Invalido. Los campos NIT y CI deben ser únicos', ['nit', 'ci']),
    ]

    @api.onchange('name')
    def onchange_name(self):
        self.razon = self.name
        self.razon_invoice = self.name

    @api.onchange('razon')
    def onchange_razon(self):
        self.razon_invoice = self.razon

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not args:
            args = []
        recs = self.browse()
        if name:
            recs = self.search(args + [('name', operator, name)], limit=limit)
            if len(recs) == 0:
                recs = self.search(args + [('nit', operator, name)], limit=(limit and (limit - len(recs)) or False))
                if len(recs) == 0:
                    recs = self.search(args + [('ci', operator, name)], limit=(limit and (limit - len(recs)) or False))
        else:
            recs = self.search(args, limit=limit)

        return recs.name_get()


class ResPartnerType(models.Model):
    _name = "res.partner.type"
    _description = "Partner Type"

    @api.multi
    @api.depends('type')
    def name_get(self):
        if isinstance(self._ids, (list, tuple)) and not len(self._ids):
            return []
        if isinstance(self._ids, (int)):
            ids = [self._ids]

        res = []
        for record in self:
            name = record.type
            if record.parent_id:
                name = record.parent_id.name + ' / ' + name
            res.append((record.id, name))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(' / ')[-1]
            recs = self.search([('type', operator, name)] + args, limit=limit)
        else:
            recs = self.search(args, limit=limit)
        return recs.name_get()

    @api.model
    def _name_get_fnc(self, prop, unknow_none):
        res = self.name_get()
        return dict(res)

    # _rec_name="type"
    type = fields.Char('Type', size=32, translate=True, required=True, index=True, help="Partner Type")
    short = fields.Char(u'Abreviación', size=5, translate=True, required=True,
                        help=u"Abreviación corta de la Categoría.")
    complete_name = fields.Char(compute="_name_get_fnc", string='Name')
    parent_id = fields.Many2one('res.partner.type', 'Parent Category', index=True, ondelete='cascade')
    child_id = fields.One2many('res.partner.type', 'parent_id', string='Child Categories')
    sequence = fields.Integer('Sequence', index=True,
                              help="Gives the sequence order when displaying a list of product categories.")
    parent_left = fields.Integer('Left Parent', index=1)
    parent_right = fields.Integer('Right Parent', index=1)
    for_customer = fields.Boolean('Applicable for customers')
    for_supplier = fields.Boolean('Applicable for suppliers')

    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'sequence, type'
    _order = 'parent_left'

    _constraints = [
        (models.Model._check_recursion, 'Error ! You cannot create recursive categories.', ['parent_id'])
    ]

    # TODO: Add a domain on res_partner form depending on for_customer or for_supplier


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


class BolCustomer(models.Model):
    _name = 'bol.customer'

    nit = fields.Char('NIT', size=10, help="NIT o CI del cliente.")
    razon = fields.Char('Razón Social', help="Nombre o Razón Social para la Factura.")

    @api.model
    def get_razon(self, nit):
        partner_pool = self.env['res.partner']

        partner_ids = partner_pool.search(['|', ('nit', '=', nit), ('ci', '=', nit)])
        if partner_ids:
            for partner in partner_ids:
                if partner.commercial_partner_id.razon_invoice and partner.commercial_partner_id.razon_invoice != '':
                    razon = partner.commercial_partner_id.razon_invoice
                elif partner.commercial_partner_id.razon and partner.commercial_partner_id.razon != '':
                    razon = partner.commercial_partner_id.razon
                else:
                    razon = partner.commercial_partner_id.name
            if razon:
                return razon
            else:
                return False
        else:
            customer_ids = self.search([('nit', '=', nit)])
            if customer_ids:
                return customer_ids[0].razon
            else:
                return False

    @api.model
    def set_razon(self, nit, razon):

        customer_ids = self.search([('nit', '=', nit)])
        if customer_ids:
            customer_obj = customer_ids[0]
            if customer_obj.razon != razon:
                customer_obj.write({'razon': razon})
            return customer_ids[0]
        else:
            customer_id = self.create({'nit': nit, 'razon': razon})
            return customer_id


class res_bank(models.Model):
    _inherit = 'res.bank'

    nit = fields.Char('NIT', size=11, help="NIT de la entidad financiera.")
