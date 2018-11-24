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
{
'name': 'Ordenes de Trabajo Vehiculos',
    'version': '1.7',
    'summary': 'Mantenimiento',
    'description': """
Manage Maintenance process in OpenERP
=====================================

Asset Maintenance, Repair and Operation.
Support Breakdown Maintenance and Corrective Maintenance.

Main Features
-------------
    * Request Service/Maintenance Management
    * Maintenance Orders Management
    * Work Orders Management (group MO)
    * Parts Management
    * Tasks Management (standard job)
    * Convert Maintenance Order to Task
    * Print Maintenance Order
    * Print Maintenance Request

Required modules:
    * asset
    """,
    'author': 'PoiesisConsulting',
    'website': 'http://www.poiesisconsulting.com',
    'category': 'Industries',
    'sequence': 0,
    'depends': ['base', 'poi_vehicle', 'purchase', 'stock', 'account', 'poi_x_toyosa'],
    'data': [
        'security/workshop_security.xml',
        'security/ir.model.access.csv',
        'wizard/reject_view.xml',
        'wizard/convert_order.xml',
        'wizard/invoice_onworkshop_view.xml',
        'wizard/picking_workshop_view.xml',
        'views/stock_view.xml',
        'views/poi_vehicle_view.xml',
        'views/product_view.xml',
        #'views/workshop_workflow.xml',
        #'views/workshop_request_workflow.xml',
        'views/workshop_sequence.xml',
        'workshop_data.xml',
        'views/workshop_view.xml',
        #'workshop_report.xml',
        'views/report_workshop_order.xml',
        'views/report_workshop_request.xml',
        'views/workshop_workorder_view.xml',
        #'report/workshop_order_report_view.xml',
    ],
    'installable': True,
}
