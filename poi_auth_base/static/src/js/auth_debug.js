odoo.define('poi_auth_base.authorization_debug', function (require) {
    "use strict";

    var ActionManager = require('web.ActionManager');
    var core = require('web.core');
    var data = require('web.data');
    var DebugManager = require('web.DebugManager');
    var Dialog = require('web.Dialog');
    var formats = require('web.formats');
    var Registry = require('web.Registry');
    var session = require('web.session');
    var utils = require('web.utils');
    var Widget = require('web.Widget');

    var QWeb = core.qweb;
    var _t = core._t;

    if (core.debug) {
        DebugManager.include({
            view_authorization_status: function() {
                return this.do_action({
                    res_model : 'auth.log',
                    name: _t('View Authorization Status'),
                    domain : [['osv', '=', this.dataset.model]],
                    views: [[false, 'list'], [false, 'form'], [false, 'diagram']],
                    type : 'ir.actions.act_window',
                    view_type : 'list',
                    view_mode : 'list'
                });
            },
        });
    }

});