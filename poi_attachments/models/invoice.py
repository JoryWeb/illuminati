
from odoo import api, fields, models, _

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def poi_attachments_name(self):
        """ This opens the xml view specified in xml_id for the current vehicle """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window'].for_xml_id('poi_attachments', xml_id)
            res.update(
                context=dict(self.env.context,
                             default_res_id=self.id,
                             default_res_model='account.invoice',
                             default_create_uid=self._uid,
                             default_company_id=self.company_id.id,
                             group_by=False),
                domain=[('res_id', '=', self.id), ('res_model', '=', 'account.invoice')]
            )
            return res
        return False