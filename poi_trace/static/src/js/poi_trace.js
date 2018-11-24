odoo.define('poi_trace', function (require) {
    'use strict';

    var core = require('web.core');
    var data = require('web.data');
    var ListView = require('web.ListView');
    var FormView = require('web.FormView');
    var _t = core._t;
    var _lt = core._lt;

    ListView.include({
        render_sidebar: function ($node) {
            this._super($node);
            if (typeof this.view_assets_button === "undefined") {
                this.view_assets_button = false;
            }
            if (this.sidebar && !this.view_assets_button && this.model != "account.move" && this.model != "account.move.line") {
                this.sidebar.add_items('other', _.compact([
                    {
                        label: _t("View Generated Assets"),
                        callback: this.on_button_view_assets
                    },
                    {
                        label: _t("View Generated Journal Items"),
                        callback: this.on_button_view_journal_items
                    },
                ]));
                this.view_assets_button = true;
            }
        },
        on_button_view_assets: function () {
            var ids = this.groups.get_selection().ids;
            var res_model = this.model;
            var res_ids = [];
            $.each(ids, function (idl, res_id) {
                res_ids.push(res_model + ',' + res_id);
            });
            if (res_ids.length) {
                var action = {
                    name: _t("Account Entries Generated"),
                    res_model: 'account.move',
                    domain: [['src', 'in', res_ids]],
                    views: [[false, 'list'], [false, 'form']],
                    type: 'ir.actions.act_window',
                    view_type: "form",
                    view_mode: "list",
                    target: "current"
                };
                this.do_action(action);
                ;
            } else {
                this.do_warn(_t("Warning"), _t("You must select at least one record."));
            }
        },
        on_button_view_journal_items: function () {
            var ids = this.groups.get_selection().ids;
            var res_model = this.model;
            var res_ids = [];
            $.each(ids, function (idl, res_id) {
                res_ids.push(res_model + ',' + res_id);
            });
            if (res_ids.length) {
                var action = {
                    name: _t("Journal Items Generated"),
                    res_model: 'account.move.line',
                    domain: [['move_id.src', 'in', res_ids]],
                    views: [[false, 'list'], [false, 'form']],
                    type: 'ir.actions.act_window',
                    view_type: "form",
                    view_mode: "list",
                    target: "current"
                };
                this.do_action(action);
                ;
            } else {
                this.do_warn(_t("Warning"), _t("You must select at least one record."));
            }
        }
    });


    FormView.include({
        render_sidebar: function ($node) {
            this._super($node);
            if (typeof this.view_assets_button === "undefined") {
                this.view_assets_button = false;
            }
            if (this.sidebar && !this.view_assets_button && this.model != "account.move" && this.model != "account.move.line") {
                this.sidebar.add_items('other', _.compact([
                    {
                        label: _t("View Generated Assets"),
                        callback: this.on_button_view_assets
                    },
                    {
                        label: _t("View Generated Journal Items"),
                        callback: this.on_button_view_journal_items
                    },
                ]));
                this.view_assets_button = true;
            }
        },
        on_button_view_assets: function () {
            var self = this;
            var res_id = self.datarecord.id;
            var res_model = self.model;
            var action = {
                name: _t("Account Entries Generated"),
                res_model: 'account.move',
                domain: [['src', '=', res_model + ',' + res_id]],
                views: [[false, 'list'], [false, 'form']],
                type: 'ir.actions.act_window',
                view_type: "form",
                view_mode: "list",
                target: "current"
            };
            self.do_action(action);


        },
        on_button_view_journal_items: function () {
            var self = this;
            var res_id = self.datarecord.id;
            var res_model = self.model;
            var action = {
                name: _t("Journal Items Generated"),
                res_model: 'account.move.line',
                domain: [['move_id.src', '=', res_model + ',' + res_id]],
                views: [[false, 'list'], [false, 'form']],
                type: 'ir.actions.act_window',
                view_type: "form",
                view_mode: "list",
                target: "current"
            };
            self.do_action(action);


        },
        // for icons
        load_record: function (record) {
            var self = this;
            if (this.model == 'account.move') {
                this.hide_notification_message();
                return $.when(self._super.apply(self, arguments)).then(function () {
                    self.refresh_automove();
                })
            }
            else {
                return this._super(record);
            }

        },
        refresh_automove: function () {
            this.hide_notification_message();

            if (this.model == 'account.move') {
                if (this.datarecord.automove == true && this.datarecord.state == 'draft') {
                    this.show_notification_message(_t('This is an automatic move. Please post this asset.'), '#de4343');
                }
                ;
                if (this.datarecord.automove == true && this.datarecord.state == 'posted') {
                    this.show_notification_message(_t('This is an automatic move. You cannot make changes here.'), '#4ea5cd');
                }
                ;
                if (this.datarecord.automove == false) {
                    this.hide_notification_message();
                }
                ;
            }
        },
        hide_notification_message: function () {
            var notification_bar = this.$el.find('#notify_assets');
            notification_bar.empty();
            notification_bar.addClass('oe_hidden');
        },
        show_notification_message: function (message, color) {
            var notification_bar = this.$el.find('#notify_assets');
            notification_bar.append("<p>" + message + "</p>");
            notification_bar.removeClass('oe_hidden');
            notification_bar.css({'background-color': color});
        },
    })

});