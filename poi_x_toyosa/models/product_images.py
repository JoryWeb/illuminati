# coding: utf-8
#########################################################################
# Copyright (C) 2009  Sharoon Thomas, Open Labs Business solutions      #
#                                                                       #
# This program is free software: you can redistribute it and/or modify   #
# it under the terms of the GNU General Public License as published by   #
# the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
# This program is distributed in the hope that it will be useful,        #
# but WITHOUT ANY WARRANTY; without even the implied warranty of         #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
# GNU General Public License for more details.                           #
#                                                                       #
# You should have received a copy of the GNU General Public License      #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################
from odoo import models, fields, api, exceptions, _
import base64
import urllib


class ProductImages(models.Model):

    "Products Image gallery"
    _name = "product.images"

    def get_image(self, cr, uid, id):
        each = self.read(cr, uid, id, ['link', 'filename', 'image'])
        if each['link']:
            try:
                (filename, header) = urllib.urlretrieve(each['filename'])
                f = open(filename, 'rb')
                img = base64.encodestring(f.read())
                f.close()
            except:
                img = ''
        else:
            img = each['image']
        return img

    def _get_image(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        for each in ids:
            res[each] = self.get_image(cr, uid, each)
        return res

    name = fields.Char('Image Title', size=100, required=True)
    link = fields.Boolean('Link?',
                           help="""Images can be linked from files on your
                                   file system or remote (Preferred)""")
    image = fields.Binary('Image', filters='*.png,*.jpg,*.gif')
    filename = fields.Char('File Location', size=250)
    #preview = fields.function(_get_image, type="binary", method=True)
    comments = fields.Text('Comments')
    product_id = fields.Many2one('product.product', 'Product')
