# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape

import json


class FinancialReportController(http.Controller):

    #THIS WILL PRINT
    @http.route('/poi_account_reports/<string:output_format>/<string:report_name>/<string:report_id>', type='http', auth='user')
    def report(self, output_format, report_name, token, report_id=None, **kw):
        uid = request.session.uid
        domain = [('create_uid', '=', uid)]
        report_model = request.env['account.report.context.common'].get_full_report_name_by_report_name(report_name)
        report_obj = request.env[report_model].sudo(uid)
        if report_name == 'financial_report':
            report_id = int(report_id)
            domain.append(('report_id', '=', report_id))
            report_obj = report_obj.browse(report_id)
        context_obj = request.env['account.report.context.common'].get_context_by_report_name(report_name)
        context_id = context_obj.sudo(uid).search(domain, limit=1)
        try:
            if output_format == 'xls':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition', 'attachment; filename=' + report_obj.get_name() + '.xls;')
                    ]
                )
                context_id.get_xls(response)
                response.set_cookie('fileToken', token)
                return response
            if output_format == 'pdf':
                response = request.make_response(
                    context_id.get_pdf(),
                    headers=[
                        ('Content-Type', 'application/pdf'),
                        ('Content-Disposition', 'attachment; filename=' + report_obj.get_name() + '.pdf;')
                    ]
                )
                response.set_cookie('fileToken', token)
                return response
            if output_format == 'xml':
                content = context_id.get_xml()
                response = request.make_response(
                    content,
                    headers=[
                        ('Content-Type', 'application/vnd.sun.xml.writer'),
                        ('Content-Disposition', 'attachment; filename=' + report_obj.get_name() + '.xml;'),
                        ('Content-Length', len(content))
                    ]
                )
                response.set_cookie('fileToken', token)
                return response
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))
        else:
            return request.not_found()


