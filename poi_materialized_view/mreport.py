##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2014 Poiesis Consulting (<http://www.poiesisconsulting.com>).
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

from openerp import models, fields, api, _, SUPERUSER_ID
import psutil
import datetime
import time


class MReport(models.Model):
    _name = 'm.report'
    _description = 'Materialized Reports'

    name = fields.Char(string='Name')
    active = fields.Boolean(string='Active')
    cron = fields.Many2one('ir.cron', string='Assigned Cron')
    maximum_cpu_percentage = fields.Float(string='Max. CPU Percentage')
    retry_interval = fields.Integer(string='Retry Interval (seconds)')
    view_ids = fields.One2many('m.report.view', 'report_id', 'Materialized Views')


    def refresh_materialized_views(self, cr, uid, ids=None, mat_ids=[]):

        view_obj = self.pool.get('m.report.view')
        cpu_percent = psutil.cpu_percent()
        print "CPU PERCENT"
        print str(cpu_percent)

        if ids:
            if ids=="s":
                ids=mat_ids
                print "REFRESHING MATERIALIZED VIEWS -- (CPU: %s, time: %s)" % (str(cpu_percent),str(datetime.datetime.now()))
                for ref in self.browse(cr, uid, ids):
                    not_executed = True
                    while (not_executed):
                        if(cpu_percent <= ref.maximum_cpu_percentage):
                            for view in ref.view_ids:
                                view_obj.refresh_materialized_view(cr, uid, view.technical_name)
                                not_executed = False
                        else:
                            time.sleep(ref.retry_interval)
        return True

class MReportViews(models.Model):
    _name = 'm.report.view'

    name = fields.Char(string='Description', required=True)
    technical_name = fields.Char(string='Materialized View Name', required=True)
    report_id = fields.Many2one('m.report',string='Materialized Report List')
    max_valid_report = fields.Integer(string='Maximum Valid Report (seconds)', required=True)
    last_refresh = fields.Datetime(string='Last Refresh')

    def refresh_materialized_view(self, cr, uid, technical_name):
        #It doesn't matter who is going to refresh. We're just going to refresh it on demand
        uid = SUPERUSER_ID
        if technical_name:
            try:
                cr.execute("REFRESH MATERIALIZED VIEW %s" % (technical_name))
                view_id = self.search(cr, uid, [('technical_name','=',technical_name)])
                if view_id:
                    self.write(cr, uid, view_id, {'last_refresh': datetime.datetime.now()})
                print "MATERIALIZED VIEW %s has been refreshed at %s" % (str(technical_name),str(datetime.datetime.now()))
            except:
                pass
        return True

    def check_and_refresh_materialized_view(self, cr, uid, technical_name):
        #It doesn't matter who is going to refresh. We're just going to refresh it on demand
        uid = SUPERUSER_ID
        view_id = self.search(cr, uid, [('technical_name','=',technical_name)])
        if view_id:
            for view in self.browse(cr, uid, view_id):
                if view.last_refresh:
                    last_ref = datetime.datetime.strptime(view.last_refresh,"%Y-%m-%d %H:%M:%S")
                    diff = datetime.datetime.now() - last_ref
                    print "SEGUNDOS DE DIFERENCIA %s" % (diff.total_seconds())
                    if diff.total_seconds() > view.max_valid_report:
                        self.refresh_materialized_view(cr, uid, technical_name)
                else:
                    self.refresh_materialized_view(cr, uid, technical_name)
        else:
            self.refresh_materialized_view(cr, uid, technical_name)

        return True