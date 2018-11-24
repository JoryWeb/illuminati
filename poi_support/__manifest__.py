#!/usr/bin/env python
# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Poiesis Consulting (<http://www.poiesisconsulting.com>).
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
    'name' : 'Soporte Poiesis',
    'version' : '9.0.0.1',
    'category': 'Administration',
    'depends' : ['base'],
    'author' : 'Poiesis Consulting',
    'summary' : 'Modulo para el soporte remoto de Poiesis Consulting',
    'description': """
    * Rol especifico para el area de Sistemas del cliente para su soporte interno 
    * Branding (footer y about page)
    * Boton de "Enviar error" en mensajes de error Python o Javascript
    * Liston para diferenciar bases de pruebas
    
INSTRUCCIONES
    * Para determinar una base de datos como PRODUCTIVA, ir a Configuración>Técnico>Parámetros>Parámetros del sistema y copiar el Valor del parámetro 'database.uuid' al parámetro 'database.production.uuid'.
      Esto hará que todo backup que se saque de esta base lleve un listón con la etiqueta 'TEST' y el nombre de la base de datos.
    
ROADMAP
    * Sistema de tickets interno (por ahora visible solo admin)
    * Envio de tickets al portal de Poiesis
    * Envio de estadisticas al portal de Poiesis (cantidad de usuarios, dimensiones tecnicas, espacio en disco duro, etc.)
    * Interceptar mensajes de error Python (capturar pantalla y trace completo de python)
    """,
    'author': 'Poiesis Consulting',
    'website': 'http://www.poiesisconsulting.com',
    'data': [
        'security/poiesis_security.xml',
        'security/ir.model.access.csv',
        'data.xml',
        'views/support_view.xml',
    ],
    'qweb' : [
        'static/src/xml/*.xml',
    ],
    'installable': True,
    'active': False,
}
