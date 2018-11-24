# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from openerp.osv import fields, osv

_logger = logging.getLogger(__name__)


class ir_actions_report_xml(osv.osv):

    _inherit = 'ir.actions.report.xml'
    _columns = {
        'report_type': fields.selection([('qweb-pdf', 'PDF'),
                    ('qweb-html', 'HTML'),
                    ('controller', 'Controller'),
                    ('pdf', 'RML pdf (deprecated)'),
                    ('sxw', 'RML sxw (deprecated)'),
                    ('webkit', 'Webkit (deprecated)'),
                    ('html2html', 'html2html'),
                    ('mako2html', 'Mako2'),
                    ], 'Report Type', required=True, help="HTML will open the report directly in your browser, PDF will use wkhtmltopdf to render the HTML into a PDF file and let you download it, Controller allows you to define the url of a custom controller outputting any kind of report."),
    }


