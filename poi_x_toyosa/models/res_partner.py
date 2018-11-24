import logging
from odoo import api, fields, models
from odoo.exceptions import Warning, ValidationError

_logger = logging.getLogger(__name__)

try:
    from unidecode import unidecode
except ImportError:
    _logger.debug('Can not import unidecode`.')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def _compute_ci_plus_ext(self):
        for s in self:
            s.ci_plus_ext = ''
            if s.ci:
                s.ci_plus_ext += (s.ci + ' ')
            if s.extension:
                s.ci_plus_ext += s.extension

    @api.multi
    @api.depends('category_id')
    def _compute_person_root_type(self):
        for s in self:
            for c in s.category_id:
                if c.id in (7, 8, 9):
                    s.person_root_type = c.name

    ci_plus_ext = fields.Char('Ci + Extencion', compute="_compute_ci_plus_ext")
    pricelist_id = fields.Many2one('product.pricelist', 'Tarifa de Venta (Con Seguro)')
    is_company2 = fields.Boolean(u'es Compañia', default=False)
    is_wallet = fields.Boolean('Es Cartera', compute="_compute_is_wallet")
    born_date = fields.Date('Fecha de Nacimiento')
    person_root_type = fields.Char('Tipo de Cliente', compute="_compute_person_root_type", store=True)


    @api.multi
    @api.depends("name")
    def _compute_is_wallet(self):
        for s in self:
            if s.customer:
                if not s.create_uid or self.env.user.is_wallet:
                    s.is_wallet = True
                else:
                    s.is_wallet = False
            else:
                s.is_wallet = True

    _sql_constraints = [
        ('name', 'unique(name)', 'Este Nombre se Encuentra Registrado. Digite otro.'),
        ('ref', 'unique(ref)', 'El campo REF se Encuentra Registrado. Digite otro.'),
    ]

    @api.model
    def create(self, vals):
        if not self.env.context.get('import_file', False):
            partner_obj = self.env['res.partner']
            nit = vals.get('nit', False)
            ci = vals.get('ci', False)
            ci_dept = vals.get('ci_dept', False)
            extension = vals.get('extension', False)
            if not ci and not nit:
                raise Warning('El contacto Creado debe llevar el campo Ci o NIT llenado.')
            if nit:
                nit = nit.strip()
                vals.update({'nit': nit})
                partner_id = partner_obj.search([('nit', '=', nit), ('nit', '!=', 99001)])
                if partner_id:
                    raise Warning('El NIT ya se encuentra registrado en la base de datos a Nombre de %s' % (partner_id[0].name))
            if ci:
                ci = ci.strip()
                vals.update({'ci': ci})
                partner_id = partner_obj.search([('ci', '=', ci), ('ci', '!=', 99001)])
                if partner_id and ci:
                    partner_id = partner_obj.search([('id', 'in', partner_id.ids), ('ci_dept', '=', ci_dept), ('ci', '!=', 99001)])
                    if partner_id:
                        partner_id = partner_obj.search([('id', 'in', partner_id.ids), ('extension', '=', extension), ('ci', '!=', 99001)])
                    if partner_id:
                        raise Warning('El CI introducido ya se encuentra registrado a nombre de %s' % (partner_id[0].name))
        for  v in vals:
            if (v == 'name' or v == 'firstname' or v == 'firstname2' or v == 'lastname' or  v == 'lastname2') and isinstance(vals[v], str):
                vals[v] = vals[v].replace('á', 'A').replace('é', 'E').replace('í', 'I').replace('ó', 'O').replace('ú', 'U').replace('ñ', 'Ñ').upper()

        result = super(ResPartner, self).create(vals)
        return result

    @api.multi
    def write(self, vals):
        partner_obj = self.env['res.partner']
        nit = vals.get('nit', False)
        ci = vals.get('ci', False)
        ci_dept = vals.get('ci_dept', False)
        extension = vals.get('extension', False)
        if not nit:
            nit = self.nit
        if not ci:
            ci = self.ci
        if not ci_dept:
            ci_dept = self.ci_dept
        if not extension:
            extension = self.extension
        if nit:
            nit = nit.strip()
            vals.update({'nit': nit})
            partner_id = partner_obj.search([('nit', '=', nit), ('nit', '!=', 99001), ('id', '!=', self.id)])
            if partner_id:
                raise Warning('El NIT ya se encuentra registrado en la base de datos a Nombre de %s' % (partner_id[0].name))
        if ci:
            ci = ci.strip()
            vals.update({'ci': ci})
            partner_id = partner_obj.search([('ci', '=', ci),('id', '!=', self.id), ('ci', '!=', 99001)])
            if partner_id and ci:
                partner_id = partner_obj.search([('id', 'in', partner_id.ids), ('ci_dept', '=', ci_dept), ('id', '!=', self.id), ('ci', '!=', 99001)])
                if partner_id:
                    partner_id = partner_obj.search([('id', 'in', partner_id.ids), ('extension', '=', extension), ('id', '!=', self.id), ('ci', '!=', 99001)])
                if partner_id:
                    raise Warning('El CI introducido ya se encuentra registrado a nombre de %s' % (partner_id[0].name))
        for  v in vals:
            if (v == 'name' or v == 'firstname' or v == 'firstname2' or v == 'lastname' or  v == 'lastname2') and isinstance(vals[v], str):
                vals[v] = vals[v].replace('á', 'A').replace('é', 'E').replace('í', 'I').replace('ó', 'O').replace('ú', 'U').replace('ñ', 'Ñ').upper()
        result = super(ResPartner, self).write(vals)
        return result

    @api.multi
    def on_change_company_type(self, company_type):
        res = super(ResPartner, self).on_change_company_type(company_type)
        return {'value': {'is_company': False,
                          'is_company2': company_type == 'company'}}


    @api.onchange("name")
    def onchange_name(self):
        if self.company_type == 'person':
            self.razon = ''
            if self.firstname:
                self.razon += self.firstname + ' '
            if self.firstname2:
                self.razon += self.firstname2 + ' '
            if self.lastname:
                self.razon += self.lastname + ' '
            if self.lastname2:
                self.razon += self.lastname2
            self.razon_invoice = self.razon
        else:
            self.razon = self.name
            self.razon_invoice = self.name

    @api.model
    def _install_partner(self):
        partner_ids = self.env['res.partner'].search([('company_type', '=', 'person')])
        if partner_ids:
            for p in partner_ids:
                p.onchange_name()

    @api.model
    def _install_partner_category_root(self):
        partner_ids = self.env['res.partner'].search([])
        for p in partner_ids:
            p._compute_person_root_type()
