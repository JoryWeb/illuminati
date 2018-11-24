import odoo
from odoo import api, fields, _
from odoo.models import BaseModel, Model
from odoo.exceptions import ValidationError

@api.model
def _add_magic_auth_fields(self):
    res = BaseModel._add_magic_fields(self)

    def add(name, field):
        """ add ``field`` with the given ``name`` if it does not exist yet """
        if name not in self._fields:
            BaseModel._add_field(self, name, field)

    if self._authmode:
        add('auth_locked', fields.Boolean(string='Authorization Locked', automatic=True, default=False))
        self.env.cr.execute("SELECT * FROM ir_model WHERE model='poi.auth.document.log'")
        if self.env.cr.rowcount:
            add('auth_log_id', fields.Many2one('poi.auth.document.log', string='Auth Log', automatic=True))
    return res

@api.model
def fields_view_auth_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    res = BaseModel.fields_view_get(self, view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    if self._authmode:
        res['fields']['auth_locked'] = {'searchable': True, 'views': {}, 'required': False, 'manual': False, 'depends': (), 'company_dependent': False, 'sortable': False, 'type': 'boolean', 'store': True, 'string': 'Authorization Required'}
        res['fields']['auth_log_id'] = {'domain': [], 'change_default': False, 'string': 'Auth Log', 'searchable': True, 'views': {}, 'required': False, 'manual': False, 'readonly': False, 'depends': (), 'relation': 'poi.auth.document.log', 'context': {}, 'company_dependent': False, 'sortable': True, 'type': 'many2one', 'store': True}
    return res

@api.multi
def check_authorization(self, code=None, data=''):
    data = str(data)
    if not code:
        raise ValidationError(_("There is an authorization without code to call. Please contact your developer"))
    auth_codes = self.env['poi.auth.auth'].search([('code','=',code)])
    if not auth_codes:
        raise ValidationError(_("We can't find %s code. Please contact your developer") % str(code))
    else:
        for ac in auth_codes:
            doc_found = self.env['poi.auth.document.log'].search([('res_id','=',self.ids[0]),('auth_id','=',ac.id)])
            doc_approved = False
            for d in doc_found:
                if d.state == 'approved':
                    doc_approved = True
                    break
            if not doc_approved:
                ac.execute_rules(res_ids=self.ids, data=data)

        if self.auth_log_id:
            return False
        elif self.auth_log_id:
            return False
        else:
            return True
    return True

@api.multi
def on_authorized(self):
    self.write({'auth_log_id': False, 'auth_locked': False})
    return True

@api.multi
def on_rejected(self):
    self.write({'auth_log_id': False, 'auth_locked': False})
    return True


Model._authmode = False
Model._add_magic_fields = _add_magic_auth_fields
Model.fields_view_get = fields_view_auth_get
Model.check_authorization = check_authorization
Model.on_authorized = on_authorized
Model.on_rejected = on_rejected
