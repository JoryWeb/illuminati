# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#    Copyright (C) 2013-2016 CodUP (<http://codup.com>).
#
##############################################################################

{
    'name': 'Costeo de Productos Periodico',
    'version': '1.10',
    'summary': 'Costes en Destino',
    'description': """
Costeo de productos en valoriación periódica.
===========================

 Las categorías de productos que aplican periodico y costo Real
 pueden valorarse en el inventario pero no generar el asiento contable

 Una vez instalado el Addons todo el inventario se cambio a periodico manual
 Verificar la configuración de las categorias de los productos esten establecidas en
 'Precio Real' y 'Periodico (Manual)'

 En caso de querer volver a costear en real desinstalar este addons
 y configurar nuevamente las categorias de productos a 	"Perpetuo (automatizado)"
    """,
    'author': 'PoiesisConsulting',
    'website': 'http://www.poiesisconsulting.com',
    'category': 'Industries',
    'sequence': 0,
    'depends': ['stock_landed_costs'],
    #'demo': ['asset_demo.xml'],
    'data': [
    ],
    'installable': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: