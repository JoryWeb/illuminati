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
'name': 'Vehiculos',
    'version': '1.10',
    'summary': 'Administracion Mantenimiento',
    'description': """
Managing Assets in Odoo.
===========================
Support following feature:
    * Vehiculos
    * Asignar vehiculo a empleado
    * Seguimiento de la información de garantía
    * Estados Personalizados del vehiculo
    * States of Asset for different team: Finance, Warehouse, Manufacture, Maintenance and Accounting
    * Drag&Drop manage states of Asset
    * Asset Tags
    * Search by main fields
    """,
    'author': 'PoiesisConsulting',
    'website': 'http://www.poiesisconsulting.com',
    'category': 'Industries',
    'sequence': 0,
    'depends': ['stock', 'poi_x_toyosa'],
    'data': [
        'security/asset_security.xml',
        'security/ir.model.access.csv',
        'views/poi_vehicle_view.xml',
        'stock_data.xml',
        'views/vehicle.xml',
    ],
    'installable': True,
    'application': True,
}
