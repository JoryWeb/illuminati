odoo.define('account_reports.tour', function (require) {
'use strict';

var Tour = require('web_tour.tour');

Tour.register('account_reports_widgets', {
    test: true,
    url: '/web#action=account_reports.action_account_report_pnl',
    },
     [
        {
            content:    "wait web client",
            trigger:    ".o_account_reports_body",
            extra_trigger: ".breadcrumb",
            run: function() {}
        },
        {
            content: "unfold line",
            trigger: '.js_account_report_foldable:first',
            run: 'click',
        },
        {
            content: "check that line has been unfolded",
            trigger: '[data-parent-id]',
        },
        {
            content: 'Open dropdown menu of one of the unfolded line',
            trigger: '[data-parent-id] .o_account_report_line a:first', 
            run: 'click',
        },
        {
            content: 'click on the annotate action',
            trigger: '[data-parent-id] .o_account_report_line .o_account_reports_domain_dropdown:first .js_account_reports_add_footnote',
            run: 'click',
        },
        {
            content: 'insert footnote text',
            trigger: '.js_account_reports_footnote_note',
            run: 'text My awesome footnote!'
        },
        {
            content: 'save footnote',
            trigger: '.modal-footer .btn-primary',
            run: 'click'
        },
        {
            content: 'wait for footnote to be saved',
            trigger: '.footnote#footnote1 .text:contains(1. My awesome footnote!)',
            extra_trigger: '.o_account_reports_footnote_sup a[href="#footnote1"]',
        },
        {
            content:      "change date filter",
            trigger:    ".o_account_reports_filter_date > a",
        },
        {
            content:      "change date filter",
            trigger:    ".js_account_report_date_filter[data-filter='last_year'] > a",
            run: 'click'
        },
        {
            content:      "wait refresh",
            trigger:    ".o_account_reports_level2.total:last() .o_account_report_column_value:contains(0.00)"
        },
        {
            content:      "change comparison filter",
            trigger:    ".o_account_reports_filter_date_cmp > a"
        },
        {
            content:      "change comparison filter",
            trigger:    ".js_foldable_trigger[data-filter='previous_period_filter'] > a"
        },
        {
            content:      "change comparison filter",
            trigger:    ".js_account_report_date_cmp_filter[data-filter='previous_period']",
            run: 'click',
        },
        {
            content:      "wait refresh, report should have 4 columns",
            trigger:    "th + th + th + th"
        },
        {
            content:      "click summary",
            trigger: '.o_account_reports_summary',
            run: 'click'
        },
        {
            content:      "edit summary",
            trigger:    'textarea[name="summary"]',
            run: 'text v9 accounting reports are fabulous !'
        },
        {
            content:      "save summary",
            trigger:    '.js_account_report_save_summary',
            run: 'click'
        },
        {
            content:      "wait refresh and check that summary has been saved",
            trigger:    ".o_account_reports_summary:visible:contains(v9 accounting reports are fabulous !)",
            run: function(){}
        },
        {
            content:      "change boolean filter",
            trigger:    ".o_account_reports_filter_bool > a",
        },
        {
            content:      "change cash basis filter",
            trigger:    ".js_account_report_bool_filter[data-filter='cash_basis'] > a",
            run: 'click'
        },
        {
            title:      "export xlsx",
            trigger:    'button[action="print_xlsx"]',
            run: 'click'
        },
    ]
);

Tour.register('account_followup_reports_widgets', {
    test: true,
    url: '/web#action=account_reports.action_account_followup_all',
    },
     [
        {
            content: 'wait for web client',
            trigger: "#trustDropdown",
            extra_trigger: ".breadcrumb",
            run: function() {}
        },
        {
            content: 'click trust ball',
            trigger: '#trustDropdown',
            run: 'click'
        },
        {
            content: 'change trust',
            trigger: '.changeTrust[data-new-trust="good"]',
            run: 'click'
        },
        {
            content: 'exclude one line',
            trigger: '.o_account_reports_table tr:not(:has(td.color-red)) input[type="checkbox"]:first',
            run: 'click'
        },
        {
            content: 'ensure that line has been excluded',
            trigger: '.o_account_reports_table .o_account_followup_blocked',
            run: function() {}
        },
        {
            content: 'send by mail',
            trigger: '.followup-email',
            run: 'click'
        },
        {
            content: 'check that message telling that mail has been sent is shown',
            trigger: '.alert:contains(The followup report was successfully emailed !)',
            run: function() {}
        },
        {
            content: 'dismiss alert',
            trigger: '.alert .close',
            run: 'click'
        },
        {
            content:      "change filter",
            trigger:    ".o_account_reports_followup-filter > a",
        },
        {
            content:      "change filter",
            trigger:    ".js_account_reports_one_choice_filter[data-id='all'] > a",
            run: 'click'
        },
        {
            content: "open history button",
            trigger: '#history:visible .dropdown > a',
            run: 'click'
        },
        // TODO /!\ fix this fragile selector, since other modules can insert other overdue invoices for Agrolait
        //          and then block the tour
        {
            content: "Check that sent mail has only 2 invoices",
            trigger: '.o_account_reports_history li table:first tbody:not(:has(tr:has(td:contains(INV))+tr:has(td:contains(INV))+tr:has(td:contains(INV))+tr:has(td:contains(Total))))',
            extra_trigger: '.o_account_reports_history li table:first tbody:has(tr:has(td:contains(INV))+tr:has(td:contains(INV))+tr:has(td:contains(Total)))',
            run: function() {}
        },
        {
            content:      "change filter",
            trigger:    ".o_account_reports_followup-filter > a",
        },
        {
            content:      "change filter",
            trigger:    ".js_account_reports_one_choice_filter[data-id='action'] > a",
            run: 'click'
        },
        {
            content: 'Click the Do it later button',
            trigger: '.o_account_reports_followup_skip',
            run: 'click'
        },
        {
            content: 'Check that we have nothing to display',
            trigger: '.alert-info:contains(No followup to send ! You have skipped 1 partners)'
        },

     ]
);

});
