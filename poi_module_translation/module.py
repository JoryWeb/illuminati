##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2014 OpenERP S.A. (<http://openerp.com>).
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
from docutils import nodes
from docutils.core import publish_string
from docutils.transforms import Transform, writer_aux
from docutils.writers.html4css1 import Writer
import importlib
import logging
from operator import attrgetter
import os
import re
import shutil
import tempfile
import urllib
import urllib2
import urlparse
import zipfile
import zipimport
import lxml.html

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO   # NOQA

import openerp
import openerp.exceptions
from openerp import modules, tools
from openerp.tools.translate import _
from openerp.osv import osv, orm, fields


class module(osv.osv):
    _inherit = "ir.module.module"

    def button_upgrade_translation(self, cr, uid, ids, context=None):
        self.update_translations(cr, uid, ids, None, {'overwrite': True})
        return True