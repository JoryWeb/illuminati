import logging
from odoo import api, fields, models, tools
from odoo.exceptions import Warning, ValidationError
_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    contact_name = fields.Char(
        compute="_compute_name",
        required=False,
        store=True)
    lastname2 = fields.Char("A. Materno")
    lastname = fields.Char("A. Paterno")
    firstname2 = fields.Char("Segundo Nombre")
    firstname = fields.Char("Primer Nombre")
    ci = fields.Char('Carnet de Identidad')
    ci_dept = fields.Selection([
        ('lp','LP'),
        ('sc','SC'),
        ('be','BE'),
        ('cb','CB'),
        ('ch','CH'),
        ('or','OR'),
        ('pa','PA'),
        ('po','PO'),
        ('tj','TJ'),
        ('ex', 'Extranjero')], string='Dept. CI', help="Lugar de emision Carnet de Identidad")
    extension = fields.Char('Extension', help="Campo usado para las Extesiones alfanumericas(Casos Duplicados).")
    nit = fields.Char('Nit')
    razon = fields.Char(u'Razón')
    warehouse_id = fields.Many2one('stock.warehouse', u"Ubicación/Almacen", default=lambda self:(self.env.user.shop_assigned and self.env.user.shop_assigned.id) or self.env['stock.warehouse'])


    @api.onchange('date_action')
    def _onchange_date_action(self):
        if not self.date_action >= fields.Date.today():
            self.date_action = fields.Date.today()


    @api.onchange('ci', 'nit', 'ci_dept', 'extension')
    def _onchange_search_cinit(self):
        partner_obj = self.env['res.partner']
        partner_id = False

        if self.ci and self.ci_dept and not self.ci == 0:
            partner_id = partner_obj.search([('ci', '=', self.ci), ('ci_dept', '=', self.ci_dept)], limit=1)
        if self.ci and self.ci_dept and self.extension and not self.ci == 0:
            partner_id = partner_obj.search([('ci', '=', self.ci), ('ci_dept', '=', self.ci_dept), ('extension', '=', self.extension)], limit=1)
        elif self.nit:
            partner_id = partner_obj.search([('nit', '=', self.nit)], limit=1)

        if partner_id:
            self.partner_id = partner_id[0].id


    @api.model
    def _get_computed_name(self, lastname, lastname2, firstname, firstname2):
        """Compute the 'name' field according to splitted data.
        You can override this method to change the order of lastname and
        firstname the computed name"""
        return u" ".join((p for p in (lastname, lastname2, firstname, firstname2) if p))

    @api.multi
    @api.depends("lastname2", "lastname", "firstname", "firstname2")
    def _compute_name(self):
        """Write the 'name' field according to splitted data."""
        for s in self:
            s.contact_name = s._get_computed_name(s.lastname, s.lastname2, s.firstname, s.firstname2)

    @api.onchange('partner_id')
    def on_change_partner_id(self):
        if self.partner_id:
            self.street = self.partner_id.street
            self.partner_name = self.partner_id.name
            self.contact_name = (not self.partner_id.is_company and self.partner_id.name) or False
            self.title = self.partner_id.title and self.partner_id.title.id or False
            self.street = self.partner_id.street
            self.street2 = self.partner_id.street2
            self.city = self.partner_id.city
            self.state_id = self.partner_id.state_id and self.partner_id.state_id.id or False
            self.country_id = self.partner_id.country_id and self.partner_id.country_id.id or False
            self.email_from = self.partner_id.email
            self.phone = self.partner_id.phone
            self.mobile = self.partner_id.mobile
            self.zip = self.partner_id.zip
            self.function = self.partner_id.function
            self.nit = self.partner_id.nit
            self.razon = self.partner_id.razon
            self.ci = self.partner_id.ci
            self.ci_dept = self.partner_id.ci_dept and self.partner_id.ci_dept or False
            self.extension = self.partner_id.extension
            if not self.partner_id.is_company:
                self.lastname = self.partner_id.lastname
                self.lastname2 = self.partner_id.lastname2
                self.firstname = self.partner_id.firstname
                self.firstname2 = self.partner_id.firstname2
                self.partner_name = False
            else:
                self.lastname = False
                self.lastname2 = False
                self.firstname = False
                self.firstname2 = False

    @api.model
    def _create_lead_partner(self, lead):
        if lead.partner_id:
            raise Warning('No se puede Crear el Cliente, porque usted ya selecciono uno en la Inciativa. Seleccione Enlace a Cliente existente para poder continuar.')
        partner_id = super(CrmLead, self)._create_lead_partner(lead)
        partner_id = self.env['res.partner'].browse(partner_id)
        # partner_id.ci = lead.ci
        # partner_id.ci_dept = lead.ci_dept
        # partner_id.extension = lead.extension
        if  partner_id.parent_id:
            # partner_id.parent_id.nit = lead.nit
            partner_id.parent_id.razon = lead.razon
            if hasattr(partner_id, 'is_company2'):
                partner_id.parent_id.is_company2 = True
        else:
            # partner_id.nit = lead.nit
            partner_id.razon = lead.razon
        return partner_id.id


    @api.model
    def _create_lead_partner_data(self, lead, name, is_company, parent_id=False):
        res = super(CrmLead, self)._create_lead_partner_data(self, lead, name, is_company, parent_id)
        if is_company:
            res.update({
                'name': lead.partner_name,
                'nit':lead.nit
            })
        else:
            res.update({
                'firstname': lead.firstname,
                'firstname2': lead.firstname2,
                'lastname': lead.lastname,
                'lastname2': lead.lastname2,
                'ci': lead.ci,
                'ci_dept': lead.ci_dept,
                'extension': lead.extension,
            })
        return res
