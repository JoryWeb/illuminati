openerp.poi_bank = function (instance) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    instance.web.account = instance.web.account || {};

    instance.web.client_actions.add('poi_bank_statement_reconciliation_view', 'instance.web.account.poiBankStatementReconciliation');


    instance.web.account.poiBankStatementReconciliation = instance.web.Widget.extend({
        className: 'oe_bank_statement_reconciliation',

        events: {},

        init: function (parent, context) {
            this._super(parent);
            //WE CAN GET BY CONTEXT (statement_id, statement_ids, bank_account_id, bank_account_ids)
            //Note: We're getting the statements by context. Optional
            if (context.context.statement_id) this.statement_ids = [context.context.statement_id];
            if (context.context.statement_ids) this.statement_ids = context.context.statement_ids;
            //Note: We're getting the bank_accounts. Optional
            if (context.context.bank_account_id) this.bank_account_ids = [context.context.bank_account_id];
            if (context.context.bank_account_ids) this.bank_account_ids = context.context.bank_account_ids;
            //We are going to store the tible
            this.title = context.context.title || _t("Bank Statement Reconciliation");
            //MAP THE CURRENCY ROUNDINGS
            this.map_currency_id_rounding = {};

            this.model_bank_statement = new instance.web.Model("account.bank.statement");
            this.model_bank_statement_line = new instance.web.Model("account.bank.statement.line");
            this.model_account_move = new instance.web.Model("account.move");
            this.model_account_move_line = new instance.web.Model("account.move.line");
            this.reconciliation_menu_id = false; // Used to update the needaction badge
            this.monetaryIsZero; // Method that tests if a monetary amount == 0 ; loaded from the server
            this.formatCurrency; // Method that formats the currency ; loaded from the server

            //INICIEMOS UN DICCIONARIO DE STATEMENTS
            this.statement_by_id = {};
            //ESTO IRA CAMBIANDO Y EN BASE A ESTO SE HARAN LAS CONCILIACIONES
            this.unreconciled_lines = [];
            this.selected_lines = [];
            this.prereconciled_lines = [];
            //TOTALES SUMAS
            this.bankStatementTotal = 0.0;

            //INICIEMOS UN DICCIONARIO DE LINEAS DE MOVIMIENTO
            this.move_line_by_id = {};
            //ESTO IRA CAMBIANDO
            this.unreconciled_move_lines = [];
            this.selected_move_lines = [];
            this.prereconciled_move_lines = [];
            //TOTALES
            this.moveLinesTotal = 0.0;

            //LET's start with any st_line
            this.st_lines = [];
            //LET's start with any move line
            this.move_lines = [];
        },

        start: function () {
            this._super();
            var self = this;
            //Note: We need to get the conciliations based on bank_reconcile_id
            var lines_filter = [['bank_reconcile_id', '=', false], ['bank_account_id', '!=', false]];
            var move_lines_filter = [['bank_reconcile_id', '=', false], ['bank_account_id', '!=', false]];

            //PROMISES!
            var deferred_promises = [];

            // Working on specified statement(s)
            if (self.statement_ids && self.statement_ids.length > 0) {
                lines_filter.push(['statement_id', 'in', self.statement_ids]);
            }

            // Working on specified statement(s)
            if (self.bank_account_ids && self.bank_account_ids.length > 0) {
                lines_filter.push(['bank_account_id', 'in', self.bank_account_ids]);
                move_lines_filter.push(['bank_account_id', 'in', self.bank_account_ids]);
            }

            // Get the function to format currencies
            deferred_promises.push(new instance.web.Model("res.currency")
                .call("get_format_currencies_js_function")
                .then(function (data) {
                    self.formatCurrency = new Function("amount, currency_id", data);
                })
            );

            // Get the function to compare monetary values
            deferred_promises.push(new instance.web.Model("decimal.precision")
                .call("precision_get", ["Account"])
                .then(function (digits) {
                    self.monetaryIsZero = _.partial(instance.web.float_is_zero, _, digits);
                })
            );

            // Get statement lines
            deferred_promises.push(self.model_bank_statement_line
                .query(['id'])
                .filter(lines_filter)
                .all().then(function (data) {
                    self.st_lines = _(data).map(function (o) {
                        return o.id
                    });
                })
            );

            // Get move lines
            deferred_promises.push(self.model_account_move_line
                .query(['id'])
                .filter(move_lines_filter)
                .all().then(function (data) {
                    self.move_lines = _(data).map(function (o) {
                        return o.id
                    });
                })
            );


            // When queries are done, render template and reconciliation lines
            return $.when.apply($, deferred_promises).then(function () {

                // If there is no statement line to reconcile, stop here
                if (self.st_lines.length === 0) {
                    self.$el.prepend(QWeb.render("poi_bank_statement_nothing_to_reconcile"));
                    return;
                }

                // Create a dict currency id -> rounding factor
                new instance.web.Model("res.currency")
                    .query(['id', 'rounding'])
                    .all().then(function (data) {
                    _.each(data, function (o) {
                        self.map_currency_id_rounding[o.id] = o.rounding
                    });
                });

                new instance.web.Model("ir.model.data")
                    .call("xmlid_to_res_id", ["account.menu_bank_reconcile_bank_statements"])
                    .then(function (data) {
                        self.reconciliation_menu_id = data;
                        self.doReloadMenuReconciliation();
                    });

                // Bind keyboard events TODO : méthode standard ?
                /*$("body").on("keypress", function (e) {
                    self.keyboardShortcutsHandler(e);
                });*/

                // Render and display
                self.$el.prepend(QWeb.render("poi_bank_statement_reconciliation", {
                    title: self.title,
                    //single_statement: self.single_statement,
                    //total_lines: self.already_reconciled_lines+self.st_lines.length
                }));

                return self.model_bank_statement_line
                    .call("get_bank_reconciliation_lines", [self.st_lines], {context: self.session.user_context})
                    .then(function (data) {
                        console.log('DATA', data);

                        if (data.unreconciled.length > 0) {
                            self.addStatements(data.unreconciled)
                            console.log("STATEMENTS STORED",self.statement_by_id);
                            self.displayUnreconciledStatementsTable();


                            //STICKY TOTALS
                            /*self.$el.find('.unreconciled_lines_total').hcSticky({
                                                                                top: 35,
                                                                                bottomEnd: 100,
                                                                                wrapperClassName: 'sidebar-sticky'
                                                                            });*/
                            self.doReloadTotals();
                        }

                        return self.model_bank_statement_line.call("get_account_move_lines", [self.move_lines], {context: self.session.user_context})
                    }).then(function(data) {
                        console.log("MOVE LINE DATA", data);

                        if (data.unreconciled.length > 0) {
                            self.addMoveLines(data.unreconciled)

                            self.displayUnreconciledMoveLinesTable();


                            //STICKY TOTALS
                            self.$el.find('.unreconciled_lines_total').hcSticky({
                                                                                top: 35,
                                                                                bottomEnd: 100,
                                                                                wrapperClassName: 'sidebar-sticky'
                                                                            });
                            self.doReloadTotals();
                            self.set_callbacks();
                        }
                    });
            });
        },
        //CREATE STATEMENTS
        addStatements: function(statements){
            var self = this;
            if(!statements instanceof Array){
                statements = [statements];
            }
            for(var i = 0, len = statements.length; i < len; i++){
                self.statement_by_id[statements[i].st_line.id] = statements[i].st_line;
                self.unreconciled_lines.push(statements[i].st_line.id);
            }
        },
        get_statement_by_id: function(id){
            return this.statement_by_id[id];
        },
        add_selected_statement: function (id) {
            this.selected_lines.push(id);
            this.doReloadTotals()
        },
        remove_selected_statement: function(id){
            this.selected_lines = $.grep(this.selected_lines, function(value) {
                return value != id;
            });
            this.doReloadTotals();
        },
        displayUnreconciledStatementsTable: function(){
            var self = this;
            var widget = new instance.web.account.poiBankUnreconciledStatementLines(self, {});
            return widget.appendTo(self.$(".unreconciled_bank_statements"));
        },
        refreshUnreconciledStatementsTable: function(){

        },
        //MOVE LINES
        addMoveLines: function(move_lines){
            var self = this;
            if(!move_lines instanceof Array){
                move_lines = [move_lines];
            }
            for(var i = 0, len = move_lines.length; i < len; i++){
                self.move_line_by_id[move_lines[i].move_line.id] = move_lines[i].move_line;
                self.unreconciled_move_lines.push(move_lines[i].move_line.id);
            }
        },
        get_move_line_by_id: function(id){
            return this.move_line_by_id[id];
        },
        add_selected_move_line: function (id) {
            this.selected_move_lines.push(id);
            this.doReloadTotals()
        },
        remove_selected_move_line: function(id){
            this.selected_move_lines = $.grep(this.selected_move_lines, function(value) {
                return value != id;
            });
            this.doReloadTotals();
        },
        displayUnreconciledMoveLinesTable: function(){
            var self = this;
            var widget = new instance.web.account.poiBankUnreconciledMoveLines(self, {});
            return widget.appendTo(self.$(".unreconciled_move_lines"));
        },
        refreshUnreconciledMoveLinesTable: function(){

        },
        //CREAMOS LAS CONCILIACIONES
        set_callbacks: function(){
            var self = this;
            $('#add_to_conciliate_area').click(function() {
                if (self.test_non_zero()){
                    if (self.test_equal()){
                        self.addToConciliationArea();

                    }
                    else {
                        alert(_t("Totals must match. You cannot conciliate statements with moves when their sum is not equal."));
                    }
                }
                else{
                    alert(_t("You must select some lines to conciliate them"));
                }
            });
        },
        test_non_zero: function(){
            if (this.bankStatementTotal == 0.0 || this.moveLinesTotal == 0.0)
            {
                return false;
            }
            else {
                return true;
            }
        },
        test_equal: function(){
            if (this.bankStatementTotal == this.moveLinesTotal){
                return true;
            }
            else{
                return false;
            }
        },
        addToConciliationArea: function(){

        },






        //OTHER FUNCTIONS
        displayUnreconciledBankStatementLines: function (st_line_id, animate_entrance, st_line) {
            var self = this;
            animate_entrance = (animate_entrance === undefined ? true : animate_entrance);

            var context = {
                st_line_id: st_line_id,
                animate_entrance: animate_entrance,
                st_line: st_line,
            };
            var widget = new instance.web.account.poiBankUnreconciledStatementLine(self, context);
            return widget.appendTo(self.$(".unreconciled_bank_statements > table > tbody"));
        },
        /* reloads the needaction badge */
        doReloadMenuReconciliation: function () {
            var menu = instance.webclient.menu;
            if (!menu || !this.reconciliation_menu_id) {
                return $.when();
            }
            return menu.rpc("/web/menu/load_needaction", {'menu_ids': [this.reconciliation_menu_id]}).done(function(r) {
                menu.on_needaction_loaded(r);
            }).then(function () {
                menu.trigger("need_action_reloaded");
            });
        },
        doReloadTotals: function () {
            var self = this;
            var total = 0.0;
            $.each(this.selected_lines, function( index, value ) {
                line = self.get_statement_by_id(value);
                total+=line.amount;
            });
            this.bankStatementTotal = total;
            this.$el.find('#bsl_total').text(self.bankStatementTotal);

            var move_lines_total = 0.0;
            $.each(this.selected_move_lines, function( index, value ) {
                line = self.get_move_line_by_id(value);
                move_lines_total+=line.amount;
            });
            this.moveLinesTotal = move_lines_total;
            this.$el.find('#aml_total').text(self.moveLinesTotal);
        }
    });


    instance.web.account.poiBankUnreconciledStatementLines = instance.web.Widget.extend({
        init: function(parent, context){
            this._super(parent);
        },
        start: function(){
            this.render();
            this.set_callbacks();
        },
        render: function(){
            var self = this;
            var unreconciled_lines = self.getParent().unreconciled_lines;
            var st_lines = []
            for(var i = 0, len = unreconciled_lines.length; i < len; i++){
                st_lines.push(self.getParent().get_statement_by_id(unreconciled_lines[i]));
            }

            self.$el.prepend(QWeb.render("poi_bank_unreconciled_statement_lines", {
                lines: st_lines,
            }));
        },
        set_callbacks: function(){
            var self = this;
            $('.unreconciled_statement_line').change(function() {
                console.log("CHANGED!!!",this);
                if($(this).is(":checked")) {
                    console.log("CHECKED",$(this).attr("id"));
                    self.getParent().add_selected_statement($(this).attr("id"));
                };
                if(!$(this).is(":checked")) {
                    console.log("UNCHECKED",$(this).attr("id"));
                    self.getParent().remove_selected_statement($(this).attr("id"));
                };
            });
        }
    });


    instance.web.account.poiBankUnreconciledMoveLines = instance.web.Widget.extend({
        init: function(parent, context){
            this._super(parent);
        },
        start: function(){
            this.render();
            this.set_callbacks();
        },
        render: function(){
            var self = this;
            var unreconciled_move_lines = self.getParent().unreconciled_move_lines;
            var move_lines = []
            for(var i = 0, len = unreconciled_move_lines.length; i < len; i++){
                move_lines.push(self.getParent().get_move_line_by_id(unreconciled_move_lines[i]));
            }

            self.$el.prepend(QWeb.render("poi_bank_unreconciled_move_lines", {
                lines: move_lines,
            }));
        },
        set_callbacks: function(){
            var self = this;
            $('.unreconciled_move_line').change(function() {
                console.log("CHANGED!!!",this);
                if($(this).is(":checked")) {
                    console.log("MOVE CHECKED",$(this).attr("id"));
                    self.getParent().add_selected_move_line($(this).attr("id"));
                };
                if(!$(this).is(":checked")) {
                    console.log("MOVE UNCHECKED",$(this).attr("id"));
                    self.getParent().remove_selected_move_line($(this).attr("id"));
                };
            });
        }
    });











    //LAS LINEAS SIN CONCILIAR
    instance.web.account.poiBankUnreconciledStatementLine = instance.web.Widget.extend({
        classname: 'oe_unreconciled_bank_statement_line',
        init: function(parent, context){
            console.log('poiBankUnreconciledStatementLine init');
            this._super(parent);
            this.formatCurrency = this.getParent().formatCurrency;
            this.monetaryIsZero = this.getParent().monetaryIsZero;

            this.st_line = context.st_line;
            this.partner_id = context.st_line.partner_id;

            this.context = context;
            this.st_line_id = context.st_line_id;
            this.animation_speed = this.getParent().animation_speed;
            this.aestetic_animation_speed = this.getParent().aestetic_animation_speed;
            this.model_bank_statement_line = new instance.web.Model("account.bank.statement.line");
            this.model_res_users = new instance.web.Model("res.users");
            this.map_currency_id_rounding = this.getParent().map_currency_id_rounding;
            this.map_account_id_code = this.getParent().map_account_id_code;
            this.presets = this.getParent().presets;
            this.is_valid = true;
            this.is_consistent = true; // Used to prevent bad server requests
            this.filter = "";
        },
        start: function() {
            console.log('poiBankUnreconciledStatementLine start');
            var self = this;
            return self._super().then(function() {
                // no animation while loading
                self.animation_speed = 0;
                self.aestetic_animation_speed = 0;

                self.is_consistent = false;
                if (self.context.animate_entrance) {
                    self.$el.fadeOut(0);
                    self.$el.slideUp(0);
                }
                return $.when(self.render()).then(function(){
                    self.is_consistent = true;
                    self.loadActions();
                    // Make an entrance
                    self.animation_speed = self.getParent().animation_speed;
                    self.aestetic_animation_speed = self.getParent().aestetic_animation_speed;
                    if (self.context.animate_entrance) {
                        return self.$el.stop(true, true).fadeIn({ duration: self.aestetic_animation_speed, queue: false }).css('display', 'none').slideDown(self.aestetic_animation_speed);
                    }
                });
            });
        },
        render: function() {
            console.log('poiBankUnreconciledStatementLine render', this);
            var self = this;
            self.$el.replaceWith(QWeb.render("poi_bank_unreconciled_statement_line", {
                line: self.st_line,
            }));
        },
        loadActions: function(){
            console.log("ESTO", this.$el);
            this.$el.find('.cell_action :checkbox').click(function() {
                var $this = $(this);
                // $this will contain a reference to the checkbox
                if ($this.is(':checked')) {
                    // the checkbox was checked
                } else {
                    // the checkbox was unchecked
                }
                console.log('WIIIII');
            });
        },
        clickOnCheckbox: function() {
            console.log('WIIIII');
        },
    });


}