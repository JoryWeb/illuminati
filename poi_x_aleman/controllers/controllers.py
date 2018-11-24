# -*- coding: utf-8 -*-
from odoo import http

# class Extra-addons/poi-educat(http.Controller):
#     @http.route('/extra-addons/poi-educat/extra-addons/poi-educat/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/extra-addons/poi-educat/extra-addons/poi-educat/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('extra-addons/poi-educat.listing', {
#             'root': '/extra-addons/poi-educat/extra-addons/poi-educat',
#             'objects': http.request.env['extra-addons/poi-educat.extra-addons/poi-educat'].search([]),
#         })

#     @http.route('/extra-addons/poi-educat/extra-addons/poi-educat/objects/<model("extra-addons/poi-educat.extra-addons/poi-educat"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('extra-addons/poi-educat.object', {
#             'object': obj
#         })