odoo.define('poi_bol_base', function (require) {
    'use strict';

    var core = require('web.core');
    var data = require('web.data');
    var ListView = require('web.ListView');
    var FormView = require('web.FormView');
    var _t = core._t;
    var _lt = core._lt;

    FormView.include({

        load_record: function(record) {
            var self = this;
            if (this.model=='account.invoice'){
                this.clear_estado_fac();
                return $.when(self._super.apply(self,arguments)).then(function(){
                    self.refresh_estado_fac();
                })
            }
            else
            {
                return this._super(record);
            }

        },
        refresh_estado_fac: function(){
            var icon_box = this.$el.find('.info-box-icon > i');

            this.clear_estado_fac();

            if (this.model=='account.invoice') {
                if (this.datarecord.estado_fac == 'V'){
                    this.set_estado_fac_color('#00a65a');
                    this.set_estado_fac_icon("fa-check");
                };
                if (this.datarecord.estado_fac == 'A'){
                    this.set_estado_fac_color('#dd4b39');
                    this.set_estado_fac_icon("fa-times");
                };
                if (this.datarecord.estado_fac == 'na'){
                    this.set_estado_fac_color('#f39c12');
                    this.set_estado_fac_icon("fa-flag");
                };
            }
        },
        clear_estado_fac: function(){
            var icon_box = this.$el.find('.info-box-icon > i');
            //Removing color
            this.set_estado_fac_color('#FFFFFF');
            icon_box.removeClass();
        },
        set_estado_fac_color: function(color){
            this.$el.find('.oe_invoice_state').css({'background-color': color});
        },
        set_estado_fac_icon: function(icon){
            this.$el.find('.info-box-icon > i').removeClass().addClass("fa ".concat(icon));
        },

    })

});
