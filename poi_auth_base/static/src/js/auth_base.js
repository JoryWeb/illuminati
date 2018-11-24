odoo.define('poi_auth_base.authorization', function (require) {
    "use strict";

    var core = require('web.core')
    var FormRenderer = require('web.FormRenderer');
    // var KanbanRecord = require('web_kanban.Record');
    var Model = require('web.dom');
    var BasicModel = require('web.BasicModel');
    var Context = require('web.Context');
    var utils = require('web.utils');
    var session = require('web.session');
    var FormController = require('web.FormController');
    var qweb = core.qweb;
    var _t = core._t;

    BasicModel.include({
        _fetchRecord: function (record, options) {
            var self = this;
            options = options || {};
            var fieldNames = options.fieldNames || record.getFieldNames(options);
            fieldNames = _.uniq(fieldNames.concat(['display_name']));
            fieldNames = _.uniq(fieldNames.concat(['auth_locked', 'auth_log_id']));
            return this._rpc({
                    model: record.model,
                    method: 'read',
                    args: [[record.res_id], fieldNames],
                    context: _.extend({}, record.getContext(), {bin_size: true}),
                })
                .then(function (result) {
                    if (result.length === 0) {
                        return $.Deferred().reject();
                    }
                    result = result[0];
                    if (result["auth_locked"] === null) {
                      this.auth_log_id = result["auth_log_id"];
                      this.auth_locked = result["auth_locked"];
                      delete result["auth_log_id"];
                      delete result["auth_locked"];
                    }
                    record.data = _.extend({}, record.data, result);
                })
                .then(function () {
                    if (!("auth_locked" in record.data) || (record.data["auth_locked"] === null)) {
                      var index = fieldNames.indexOf('auth_log_id');
                      if (index > -1) {
                        fieldNames.splice(index, 1);
                      }
                      index = fieldNames.indexOf('auth_locked');
                      if (index > -1) {
                        fieldNames.splice(index, 1);
                      }
                    }
                    self._parseServerData(fieldNames, record, record.data);
                })
                .then(function () {
                    return $.when(
                        self._fetchX2Manys(record, options),
                        self._fetchReferences(record, options)
                    ).then(function () {
                        return self._postprocess(record, options);
                    });
                });
        },

    });



    // KanbanRecord.include({
    //     events: _.defaults({
    //         'click .auth_message': 'on_auth_message_click',
    //     }, KanbanRecord.prototype.events),
    //
    //     on_auth_message_click: function (ev) {
    //         ev.preventDefault();
    //
    //         this.$auth_message = this.$('.auth_message')
    //         this.$auth_message.focus();
    //
    //         var self = this;
    //         this.$auth_message.blur(function () {
    //             var value = self.$auth_message.val();
    //             new Model('poi.auth.document.log').call('write', [[self.id], {'auth_text': value}]).done(function () {
    //                 /*self.trigger_up('kanban_record_update', {id: self.id});*/
    //             });
    //         });
    //     },
    // });


    FormRenderer.include({

        _view_authorization_log: function(){
            return this.do_action({
                res_id: this.state.data['auth_log_id']['res_id'],
                res_model : 'poi.auth.document.log',
                name: _t('Authorization Status'),
                //domain : [['osv', '=', this.dataset.model]],
                views: [[false, 'form']],
                type : 'ir.actions.act_window',
                view_type : 'list',
                view_mode : 'list',
                target: 'new',
            });
        },

        _aprove_document: function () {
          var self = this;
          var auth_message = this.$auth_area.find('#auth_message').val();
          return this._rpc({
                  model: 'poi.auth.document.log',
                  method: 'approval_click',
                  args: [[this.state.data['auth_log_id']['res_id']], auth_message],
                  // context: _.extend({}, record.getContext(), {bin_size: true}),
              })
              .then(function () {
                self._renderView();

              });
        },

        _deny_document: function () {
          var self = this;
          var auth_message = this.$auth_area.find('#auth_message').val();
          return this._rpc({
                  model: 'poi.auth.document.log',
                  method: 'denial_click',
                  args: [[this.state.data['auth_log_id']['res_id']], auth_message],
                  // context: _.extend({}, record.getContext(), {bin_size: true}),
              })
              .then(function () {
                self._renderView();
              });
        },

        _renderView: function () {
          var self = this;
          if (('auth_locked' in self.state.data) && (self.state.data['auth_locked'] == true)){
              self.mode = "readonly";
          }
          // render the form and evaluate the modifiers
          var defs = [];
          this.defs = defs;
          var $form = this._renderNode(this.arch).addClass(this.className);
          delete this.defs;

          return $.when.apply($, defs).then(function () {
              self._updateView($form.contents());
              if (('auth_locked' in self.state.data) && (self.state.data['auth_locked'] == true)){
                  self.disableButtons();
              }
          }, function () {
              $form.remove();
          });
      },

      _updateView: function ($newContent) {
        var self = this;
        this._super($newContent);
        if (('auth_locked' in self.state.data) && (self.state.data['auth_locked'] == true)){
            this._rpc({
               model: 'poi.auth.document.log',
               method: 'get_doc_data',
               args: [[self.state.data['auth_log_id']['res_id']]],
               // context: _.extend({}, self.getContext(), {bin_size: true}),
             }).then(function (r) {
               self.message = r.message;
               self.to_approve = r.to_approve;
               var $buttonsArea = self.$el.find('.o_form_statusbar');
               self.$el.find('.oe_auth_area').remove();
               self.$auth_area = $(qweb.render("AuthBase.area", {widget: self}));
               self.$auth_area.insertAfter($buttonsArea);
               self.$auth_area.on('click', '.o_form_button_auth_log', self._view_authorization_log.bind(self));
               self.$auth_area.on('click', '.auth_approve_button', self._aprove_document.bind(self));
               self.$auth_area.on('click', '.auth_deny_button', self._deny_document.bind(self));
            });
          }
      },

        // non_auth_document: function () {
        //     var self = this;
        //     this.require_auth = false;
        //     var $buttons_bar = self.$el.find('.o_statusbar_buttons');
        //     $buttons_bar.show();
        // },


    });


});
