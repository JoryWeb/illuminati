openerp.help_popup = function(instance, local) {

    var _t = instance.web._t;
    instance.web.ViewManager.include({

        do_create_view: function(view_type) {
            console.log("POPUP_do_create");
            var self = this;
            var res = self._super(view_type);
            self.$el.find('a.o_help_online_button').each(function () {
                console.log("POPUP_each");
                var $elem = $(this);
                if ($elem.data('click-init')) {
                    return true;
                }
                $elem.data('click-init', true);
                if (self.action.id == undefined || (self.action.advanced_help == '' && self.action.enduser_help == '')) {
                    self.$el.find('a.o_help_online_button').hide()
                }
                $elem.on('click', function(e) {
                    console.log("POPUP_click");
                    var params = 'height=650, width=800, location=no, ';
                    params += 'resizable=yes, menubar=yes';
                    path = self.action.id;
                    my_window = window.open('/report/html/help_popup.tpl_help/' + path, 'Help', params);
                    // allows to back to the window if opened previoulsy
                    setTimeout('my_window.focus()', 1);
                });

                return true;

            });
            return res;
        },
    });
}