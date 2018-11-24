##############################################################################
#
#    Poiesis Consulting, Odoo Partner
#    Copyright (C) 2017 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Developed by: Grover Menacho
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

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval

OPERATORS = [('ilike', 'contains'),
             ('not_ilike', 'does not contain'),
             ('equal', 'is equal to'),
             ('not_equal', 'is not equal to'),
             ('set', 'is set'),
             ('not_set', 'is not set'),
             ('greater', 'greater than'),
             ('less', 'less than'),
             ('greater_equal', 'greater or equal than'),
             ('less_equal', 'less or equal than')]


def remove_duplicates(values):
    output = []
    seen = set()
    for value in values:
        # If value has not been encountered yet,
        # ... add it to both list and set.
        if value not in seen:
            output.append(value)
            seen.add(value)
    return output

class PoiAuthAuth(models.Model):
    _name = 'poi.auth.auth'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', size=32, required=True,
                       help='The authorization code will be used for internal calls. Please do not change it')
    model_id = fields.Many2one('ir.model', 'Model', required=True)
    circuit_id = fields.Many2one('poi.auth.circuit', 'Authorization Circuit', required=True)
    message = fields.Html('Message to Personal Approval')
    generic_message = fields.Html('Message for Other Users')
    rule_ids = fields.One2many('poi.auth.auth.rule', 'auth_id', 'Rules')

    def prepare_document_log(self, circuit_id, model, res_ids, description='',data=''):
        doc_obj = self.env['poi.auth.document.log']
        doc_line_obj = self.env['poi.auth.document.log.line']
        doc_id = doc_obj.create({'circuit_id': circuit_id,
                                 'auth_id': self.id,
                                 'user_id': self.env.uid,
                                 'res_id': res_ids[0],
                                 'extra_data': data,
                                 'description': description})

        circuit_obj = self.env['poi.auth.circuit'].browse(circuit_id)
        num = 1
        for lc in circuit_obj.auth_lines:
            doc_line_obj.create({'log_id': doc_id.id,
                                 'user_id': lc.user_id.id,
                                 'state': 'to_be_notified'}) #We're going to send notifications in other part

        doc_id.send_notifications() #THIS WILL SEND ALL THE NOTIFICATIONS

        self.env[model].browse(res_ids).write({'auth_log_id': doc_id.id,
                                               'auth_locked': True})

        return True

    @api.multi
    def execute_rules(self, res_ids=[], data=''):
        # Let's start saying that our rule doesn't apply
        result = False

        last_rule = False
        model = False

        #This variable will contain the reason of why rule applies to user!
        description = ''

        for rule in self.rule_ids:
            if not rule.rule_applies():
                continue
            last_rule = rule
            model = rule.model_id.model
            if rule.type == 'rules':
                fields = remove_duplicates([o.field_id.name for o in rule.line_ids])
                for object in self.env[rule.model_id.model].browse(res_ids).read(fields):

                    temp_res = True
                    for line in rule.line_ids:
                        if temp_res:
                            temp_res = line.eval_condition(object)
                            result = temp_res
                        else:
                            break
                if temp_res:
                    description = rule.description
                    break
            elif rule.type == 'advanced':
                object = self.env[rule.model_id.model].browse(res_ids)
                temp_res = True
                for advline in rule.advanced_line_ids:
                    if temp_res:
                        pcode = advline.get_python_code()
                        localdict = {'object': object}
                        safe_eval(pcode, localdict, mode="exec", nocopy=True)
                        temp_res = localdict.get('result', False)
                        result = temp_res
                    else:
                        break
                if temp_res:
                    description = rule.description
                    break
            else:
                # If there is any rule type we are supposing that a rule must be triggered
                result = True

        if result and res_ids:
            circuit_id = last_rule.circuit_id
            self.prepare_document_log(circuit_id.id, model, res_ids, description=description,data=data)
        elif not res_ids:
            raise ValueError(_('There is no document to apply authorization rules'))


class PoiAuthAuthRule(models.Model):
    _name = 'poi.auth.auth.rule'

    name = fields.Char('Description')
    description = fields.Text('Rule Description (will appear to users)')
    sequence = fields.Integer('Sequence', default=5)
    circuit_id = fields.Many2one('poi.auth.circuit', 'Authorization Circuit',
                                 help="If this field is not filled header circuit is going to be applied")
    auth_id = fields.Many2one('poi.auth.auth', 'Auth ID')
    model_id = fields.Many2one('ir.model', related='auth_id.model_id', string='Model')

    type = fields.Selection([('rules', 'Reglas de Modelo'),
                             ('advanced', 'Reglas Avanzadas')], 'Type', default='rules')

    line_ids = fields.One2many('poi.auth.auth.rule.lines', 'rule_id', 'Rule Lines')
    advanced_line_ids = fields.One2many('poi.auth.auth.advanced.rule.lines', 'rule_id', 'Advanced Rule Lines')

    group_ids = fields.Many2many('res.groups', 'auth_rule_group_rel', 'rule_id', 'group_id', 'Groups')
    user_ids = fields.Many2many('res.users', 'auth_rule_user_rel', 'rule_id', 'user_id', 'Users')

    _rec_name = 'name'
    _order = 'sequence'

    @api.multi
    def rule_applies(self):
        in_group = False
        if not self.user_ids and not self.group_ids:
            return True
        if self.env.uid in self.user_ids.ids:
            return True
        for g in self.group_ids:
            g_eid = g.get_external_id()[g.id]
            if self.env.user.has_group(g_eid):
                in_group = True
                break
        return in_group


class PoiAuthAuthRuleLine(models.Model):
    _name = 'poi.auth.auth.rule.lines'

    @api.onchange('model_id')
    def onchange_model(self):
        return {'domain': {'field_id': [('model_id', '=', self.model_id.id)]}}

    rule_id = fields.Many2one('poi.auth.auth.rule', 'Rule')
    model_id = fields.Many2one('ir.model', string='Model', related='rule_id.model_id')
    field_id = fields.Many2one('ir.model.fields', 'Field')
    operator = fields.Selection(OPERATORS, 'Operator')
    value = fields.Text('Value')

    def eval_condition(self, dict_data):
        result = False
        condition = self
        value_data = dict_data.get(condition.field_id.name)
        value_to_compare = condition.value
        operator = condition.operator
        field_type = condition.field_id.ttype

        # ToDo: Conditions for; char, datetime, date, selection, boolean
        # ToDO: Done: integer, float, many2one(partially)

        if field_type == 'char':
            if operator == 'ilike':
                operator
            elif operator == 'not_ilike':
                operator
            elif operator == 'equal':
                operator
            elif operator == 'not_equal':
                operator
            elif operator == 'set':
                operator
            elif operator == 'not_set':
                operator
            else:
                raise osv.except_osv(
                    _('Error!'),
                    _('Operator not supported.'))

        elif field_type == 'datetime' or field_type == 'date':
            if operator == 'equal':
                operator
            elif operator == 'not_equal':
                operator
            elif operator == 'set':
                operator
            elif operator == 'not_set':
                operator
            elif operator == 'greater':
                operator
            elif operator == 'less':
                operator
            elif operator == 'greater_equal':
                operator
            elif operator == 'less_equal':
                operator
            else:
                raise osv.except_osv(
                    _('Error!'),
                    _('Operator not supported.'))

        elif field_type in ['integer', 'float', 'monetary']:
            if operator == 'equal':
                if float(value_data) == float(value_to_compare): result = True
            elif operator == 'not_equal':
                if float(value_data) != float(value_to_compare): result = True
            elif operator == 'set':
                if value_data: result = True
            elif operator == 'not_set':
                if not value_data: result = True
            elif operator == 'greater':
                if float(value_data) > float(value_to_compare): result = True
            elif operator == 'less':
                if float(value_data) < float(value_to_compare): result = True
            elif operator == 'greater_equal':
                if float(value_data) >= float(value_to_compare): result = True
            elif operator == 'less_equal':
                if float(value_data) <= float(value_to_compare): result = True
            else:
                raise osv.except_osv(
                    _('Error!'),
                    _('Operator not supported.'))

        elif field_type == 'selection':
            if operator == 'equal':
                operator
            elif operator == 'not_equal':
                operator
            elif operator == 'set':
                operator
            elif operator == 'not_set':
                operator
            else:
                raise osv.except_osv(
                    _('Error!'),
                    _('Operator not supported.'))

        elif field_type == 'boolean':
            if operator == 'equal':
                operator
            elif operator == 'not_equal':
                operator
            else:
                raise osv.except_osv(
                    _('Error!'),
                    _('Operator not supported.'))
        elif field_type == 'many2one':
            if operator == 'equal':
                if float(value_data[0]) == float(value_to_compare): result = True
            elif operator == 'not_equal':
                if float(value_data[0]) != float(value_to_compare): result = True
            # ToDo: Add like or not ilike
            else:
                raise osv.except_osv(
                    _('Error!'),
                    _('Operator not supported.'))
        return result


class PythonCode(models.Model):
    _name = 'poi.auth.auth.python.code'

    name = fields.Char('Name')
    code = fields.Text('Code')


class PoiAuthAuthAdvancedRuleLine(models.Model):
    _name = 'poi.auth.auth.advanced.rule.lines'

    rule_id = fields.Many2one('poi.auth.auth.rule', 'Rule')
    python_rule = fields.Many2one('poi.auth.auth.python.code', 'Python Rule')
    operator = fields.Selection(OPERATORS, 'Operator')
    value = fields.Text('Value')

    @api.model
    def get_python_code(self):
        if self.operator == 'equal':
            operator = "=="
        elif self.operator == "not_equal":
            operator = "<>"
        elif self.operator == "set":
            operator = "IS NOT NULL"
        elif self.operator == "not_set":
            operator = "IS NULL"
        elif self.operator == "greater":
            operator = ">"
        elif self.operator == "less":
            operator = "<"
        elif self.operator == "greater_equal":
            operator = ">="
        elif self.operator == "less_equal":
            operator = "<="
        else:
            operator = self.operator
        return self.python_rule.code % {'operator': operator,
                                        'value': self.value}
