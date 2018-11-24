# -*- coding: utf-8 -*-
from odoo import http
class citasrmam(http.Controller):
     @http.route('/citasrmam/citasrmam/', auth='public')
     def index(self, **kw):
         return "Hello, world"

#     @http.route('/citasrmam/citasrmam/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('citasrmam.listing', {
#             'root': '/citasrmam/citasrmam',
#             'objects': http.request.env['citasrmam.citasrmam'].search([]),
#         })

#     @http.route('/citasrmam/citasrmam/objects/<model("citasrmam.citasrmam"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('citasrmam.object', {
#             'object': obj
#         })
