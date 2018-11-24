odoo.define('poi_pos_base.base', function (require) {
    "use strict";
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var models = require('point_of_sale.models');
    var data = require('web.data')
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var PopupWidget = require('point_of_sale.popups');
    var gui = require('point_of_sale.gui');
    var utils = require('web.utils');
    var _t = core._t;
    var round_di = utils.round_decimals;
    var round_pr = utils.round_precision;

    gui.Gui = gui.Gui.extend({
        init: function (options) {
            this._super(options);
            this.keyboard_locked = true; // Added because payment screen locks this part by default without any option
        },

        close_other_tabs: function () {
            var self = this;
            var ds = new data.DataSet(this, 'pos.session');

            ds.call('open_session_available', [this.pos.pos_session.id]).then(function (available) {
                if (!available) {
                    alert("No puede abrir dos ventanas de la misma sesion. Cierre la otra sesion y vuelva a intentar.");
                    self._close();
                }
            }, function (err, event) {
                event.preventDefault();
                self.show_popup('error', {
                    'title': _t('Error: We could not connect to server'),
                    'body': _t('Your Internet connection is probably down.'),
                });
            });


            window.addEventListener('beforeunload', function () {
                //do something
                ds.call('close_session_on_use', [self.pos.pos_session.id]).then(function (available) {
                }, function (err, event) {
                    event.preventDefault();
                    self.show_popup('error', {
                        'title': _t('Error: We could not connect to server'),
                        'bo dy': _t('Your Internet connection is probably down.'),
                    });
                });
            });
        },
        close: function () {
            var self = this;
            this._super();

            var ds = new data.DataSet(this, 'pos.session');

            ds.call('close_session_on_use', [this.pos.pos_session.id]).then(function (available) {
            }, function (err, event) {
                event.preventDefault();
                self.show_popup('error', {
                    'title': _t('Error: We could not connect to server'),
                    'body': _t('Your Internet connection is probably down.'),
                });
            });
        },
        lock_keyboard: function () {
            this.keyboard_locked = true;
        },
        unlock_keyboard: function () {
            this.keyboard_locked = false;
        },
    });

    screens.PaymentScreenWidget.include({
        init: function (parent, options) {
            var self = this;
            this._super(parent, options);

            // keyboard_keydown_handler and keyboard_handler overriden to check if keyboard is locked or not

            this.keyboard_keydown_handler = function (event) {
                if (self.gui.keyboard_locked) {
                    if (event.keyCode === 8 || event.keyCode === 46) { // Backspace and Delete
                        event.preventDefault();

                        // These do not generate keypress events in
                        // Chrom{e,ium}. Even if they did, we just called
                        // preventDefault which will cancel any keypress that
                        // would normally follow. So we call keyboard_handler
                        // explicitly with this keydown event.
                        self.keyboard_handler(event);
                    }
                }
            };
            this.keyboard_handler = function (event) {
                if (self.gui.keyboard_locked) {
                    var key = '';

                    if (event.type === "keypress") {
                        if (event.keyCode === 13) { // Enter
                            self.validate_order();
                        } else if (event.keyCode === 190 || // Dot
                            event.keyCode === 110 ||  // Decimal point (numpad)
                            event.keyCode === 188 ||  // Comma
                            event.keyCode === 46) {  // Numpad dot
                            key = self.decimal_point;
                        } else if (event.keyCode >= 48 && event.keyCode <= 57) { // Numbers
                            key = '' + (event.keyCode - 48);
                        } else if (event.keyCode === 45) { // Minus
                            key = '-';
                        } else if (event.keyCode === 43) { // Plus
                            key = '+';
                        }
                    } else { // keyup/keydown
                        if (event.keyCode === 46) { // Delete
                            key = 'CLEAR';
                        } else if (event.keyCode === 8) { // Backspace
                            key = 'BACKSPACE';
                        }
                    }

                    self.payment_input(key);
                    event.preventDefault();
                }

            };
        },
    });

})
;
