# -*- coding: utf-8 -*-

import openerp
from openerp import api, fields, _
from openerp.models import BaseModel, Model
from openerp.exceptions import ValidationError

import requests
import urllib2

PM_HOST = ''
PM_TOKEN = ''
PM_SECRET = ''
SUFFIX_LOGIN = '/workflow/oauth2/token'

@api.model
def _add_magic_fields_pm(self):
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
def fields_view_get_pm(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
    res = BaseModel.fields_view_get(self, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
    if self._authmode:
        res['fields']['auth_locked'] = {'searchable': True, 'views': {}, 'required': False, 'manual': False, 'depends': (), 'company_dependent': False, 'sortable': False, 'type': 'boolean', 'store': True, 'string': 'Authorization Required'}
        res['fields']['auth_log_id'] = {'domain': [], 'change_default': False, 'string': 'Auth Log', 'searchable': True, 'views': {}, 'required': False, 'manual': False, 'readonly': False, 'depends': (), 'relation': 'poi.auth.document.log', 'context': {}, 'company_dependent': False, 'sortable': True, 'type': 'many2one', 'store': True}
    return res


def pm_login(self, host):

    PM_TOKEN = self.env['ir.config_parameter'].sudo().get_param('poi_processmaker.pm_token')
    PM_SECRET = self.env['ir.config_parameter'].sudo().get_param('poi_processmaker.pm_secret')
    url_login = host + SUFFIX_LOGIN
    data_login = {
        'grant_type': 'password',
        'scope': '*',
        'client_id': PM_TOKEN,
        'client_secret': PM_SECRET,
        'username': 'admin',
        'password': 'poies1s',
    }
    response = requests.post(url_login, data_login)
    if response.ok:
        return response
    else:
        raise ValidationError(_("Login method failed: [%s] %s") % (response.status_code, response.text))

@api.multi
def enable_process(self):
    #add all necessary fields and functions for this Object to be able to run and relate processes from BPM
    self.write({'auth_log_id': False, 'auth_locked': False})
    return True

@api.multi
def invoke_case(self):
    PM_HOST = self.env['ir.config_parameter'].sudo().get_param('poi_processmaker.pm_host')
    #ToDo: Implement timeout session
    log_token = self.pm_login(PM_HOST)
    if log_token:
        suffix_case = '/api/1.0/workflow/cases'
        url_invoke = PM_HOST + suffix_case

        data_invoke = {
            'pro_uid': '2532110915a07c7ef089310066986744', #'4433352135a07dd2a3cf7b0090056110',
            'tas_uid': '3327536475a07c818252085009796824',  #'6537506945a07dd534e2f43011670629',
        }   #            'variables': {'res_id': self.id},
        headers = {'Authorization':'Bearer ' + eval(log_token.text)['access_token']}
        response = requests.post(url_invoke, data_invoke, headers=headers) #, eval(log_token.text)['access_token']
        if response.ok:
            return response
        else:
            raise ValidationError(_("Case method failed: [%s] %s") % (response.status_code, response.text))
    #self.write({'auth_log_id': False, 'auth_locked': False})
    return True

@api.multi
def get_cases(self):
    PM_HOST = self.env['ir.config_parameter'].sudo().get_param('poi_processmaker.pm_host')
    log_token = self.pm_login(PM_HOST)
    if log_token:
        suffix_case = '/api/1.0/workflow/cases'
        url_invoke = PM_HOST + suffix_case

        data_invoke = {
            'pro_uid': '4433352135a07dd2a3cf7b0090056110',
            'tas_uid': '6537506945a07dd534e2f43011670629',
            'variables': {'res_id': self.id},
        }
        headers = {'Authorization':'Bearer ' + eval(log_token.text)['access_token']}
        response = requests.get(url_invoke, headers=headers) #, eval(log_token.text)['access_token']
        if response.ok:
            return response
        else:
            raise ValidationError(_("Case method failed: [%s] %s") % (response.status_code, response.text))
    #self.write({'auth_log_id': False, 'auth_locked': False})
    return True


Model._pm_mode = False
#Model._add_magic_fields = _add_magic_fields_pm
#Model.fields_view_get = fields_view_get_pm
Model.pm_login = pm_login
Model.invoke_case = invoke_case
Model.get_cases = get_cases