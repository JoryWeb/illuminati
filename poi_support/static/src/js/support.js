/* Poiesis Consulting Support
   License: LGPL
*/

/* Copyright 2015 Sylvain Calador <sylvain.calador@akretion.com>
   Copyright 2015 Javi Melendez <javi.melendez@algios.com>
   Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
   Copyright 2017 Thomas Binsfeld <thomas.binsfeld@acsone.eu>
   Copyright 2017 Xavier Jiménez <xavier.jimenez@qubiq.es>
   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl). */

odoo.define('web_environment_ribbon.ribbon', function(require) {
"use strict";

    var $ = require('jquery');
    var rpc = require('web.rpc');
    var core = require('web.core');

    var Widget = require('web.Widget');
    var Dashboard = require('web_settings_dashboard');

    // Code from: http://jsfiddle.net/WK_of_Angmar/xgA5C/
    function validStrColour(strToTest) {
        if (strToTest === "") { return false; }
        if (strToTest === "inherit") { return true; }
        if (strToTest === "transparent") { return true; }
        var image = document.createElement("img");
        image.style.color = "rgb(0, 0, 0)";
        image.style.color = strToTest;
        if (image.style.color !== "rgb(0, 0, 0)") { return true; }
        image.style.color = "rgb(255, 255, 255)";
        image.style.color = strToTest;
        return image.style.color !== "rgb(255, 255, 255)";
    }

    core.bus.on('web_client_ready', null, function () {
        var ribbon = $('<div class="test-ribbon"/>');
        $('body').append(ribbon);
        ribbon.hide();
        // Get ribbon data from backend
        rpc.query({
            model: 'web.environment.ribbon.backend',
            method: 'get_environment_ribbon',
        }).then(
            function (ribbon_data) {
                // Ribbon name
                if (ribbon_data.name && ribbon_data.name != 'False') {
                    ribbon.html(ribbon_data.name);
                    ribbon.show();
                }
                // Ribbon color
                if (ribbon_data.color && validStrColour(ribbon_data.color)) {
                    ribbon.css('color', ribbon_data.color);
                }
                // Ribbon background color
                if (ribbon_data.background_color && validStrColour(ribbon_data.background_color)) {
                    ribbon.css('background-color', ribbon_data.background_color);
                }
            }
        );
    });

    Dashboard.Dashboard.include({
        init: function(parent, data) {
            this._super.apply(this, arguments);
            this.all_dashboards = ['apps', 'invitations', 'planner', 'share', 'orgInfo'];
        },
        load_orgInfo: function(data) {
            return new DashboardOrgInfo(this, data.orgInfo).replace(this.$('.o_dashboard_org_info'));
        },
    });
    var DashboardOrgInfo = Widget.extend({
        template: 'DashboardOrgInfo',
        init: function(parent, data) {
            this.data = data;
            this.parent = parent;
            return this._super.apply(this, arguments);
        },
        start: function() {
            var self = this;
            this._super.apply(this, arguments);
            setTimeout(function() {
                self._rpc({
                    model: 'ir.config_parameter',
                    method: 'get_param',
                    args: ['database.uuid'],
                }).then(function(dbuuid) {
                        var apps = $('.org_logo_with_uuid_name').attr('data-app-name');
                        var src = 'https://srv.openeducat.org/get-org-logo';
                        /* $('.org_logo_with_uuid_name').attr('src', src + '?dbuuid=' + dbuuid + '&apps=' + apps);  */
                });
            }, 1500);
        },
    });

}); // odoo.define



odoo.define('poi_support.support', function (require) {
    "use strict";
    /*---------------------------------------------------------
     * Poiesis Support handler
     *---------------------------------------------------------*/
    /**
     * handles editability case for lists, because it depends on form and forms already depends on lists it had to be split out
     * @namespace
     */
    var core = require('web.core')
    var rpc = require('web.rpc');
    var Dialog = require('web.Dialog');
    var weContext = require('web_editor.context');

    var QWeb = core.qweb;
    var _t = core._t;


    Dialog.include({

        events: {
            'click #submit_error': function () {
                var self = this;
                var error_name = self.$modal.find('.o_error_detail')[0].firstChild.nextSibling.innerText;
                var error_message = self.$modal.find('.o_error_detail')[0].children[1].innerText;
                var error_url = self.$modal.find('.o_error_detail')[0].baseURI;

                rpc.query({
                    model: 'poi.support.ticket',
                    method: 'log_ticket',
                    args: [error_name,error_message,error_url],
                    context: weContext.get(),
                }).then(
                    function () {
                        self.close()
                    }
                );

            },
        },

    });


});