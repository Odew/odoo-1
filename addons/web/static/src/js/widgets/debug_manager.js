odoo.define('web.DebugManager', function (require) {
"use strict";

var core = require('web.core');
var Dialog = require('web.Dialog');
var formats = require('web.formats');
var framework = require('web.framework');
var session = require('web.session');
var SystrayMenu = require('web.SystrayMenu');
var utils = require('web.utils');
var ViewManager = require('web.ViewManager');
var Widget = require('web.Widget');

var QWeb = core.qweb;
var _t = core._t;

var DebugManager = Widget.extend({
    template: "WebClient.DebugManager",
    events: {
        "click .o-debug-button": "render_dropdown",
        "click .o-debug-dropdown li": "on_debug_click",
        "click .o-debug-leave": "leave_debug",
        "update": "update",
    },
    start: function() {
        this._super();
        this.$dropdown = this.$(".o-debug-dropdown");
    },
    /**
     * Updates the DebugManager status and hide it if the current widget isn't a ViewManager
     * @param {web.Widget} [widget] the current widget
     */
    update: function(widget) {
        this.available = false;
        if (widget instanceof ViewManager) {
            this.available = true;
            this.view_manager = widget;
            this.dataset = this.view_manager.dataset;
            this.active_view = this.view_manager.active_view;
            this.view = this.active_view.controller;
        }
        this.$el.toggle(this.available);
    },
    /**
     * Renders the DebugManager dropdown
     */
    render_dropdown: function() {
        var self = this;

        // Empty the previously rendered dropdown
        this.$dropdown.empty();

        // Render the dropdown and append it
        var dropdown_content = QWeb.render('WebClient.DebugDropdown', {
            widget: self,
            active_view: self.active_view,
            view: self.view,
            action: self.view_manager.action,
            searchview: self.view_manager.searchview,
            uid: session.uid,
        });
        $(dropdown_content).appendTo(self.$dropdown);
    },
    /**
     * Calls the appropriate callback when clicking on a Debug option
     */
    on_debug_click: function (evt) {
        evt.preventDefault();

        var params = $(evt.target).data();
        var callback = params.action;

        if (callback && this[callback]) {
            // Perform the callback corresponding to the option
            this[callback](params, evt);
        } else {
            console.warn("No debug handler for ", callback);
        }
    },
    get_metadata: function() {
        var self = this;
        var ids = this.view.get_selected_ids();
        if (ids.length === 1) {
            self.dataset.call('get_metadata', [ids]).done(function(result) {
                new Dialog(this, {
                    title: _.str.sprintf(_t("Metadata (%s)"), self.dataset.model),
                    size: 'medium',
                    buttons: {
                        Ok: function() { this.parents('.modal').modal('hide');}
                    },
                }, QWeb.render('WebClient.DebugViewLog', {
                    perm : result[0],
                    format : formats.format_value
                })).open();
            });
        }
    },
    toggle_layout_outline: function() {
        this.view.rendering_engine.toggle_layout_debugging();
    },
    set_defaults: function() {
        this.view.open_defaults_dialog();
    },
    perform_js_tests: function() {
        this.do_action({
            name: _t("JS Tests"),
            target: 'new',
            type : 'ir.actions.act_url',
            url: '/web/tests?mod=*'
        });
    },
    get_view_fields: function() {
        var self = this;
        self.dataset.call('fields_get', [false, {}]).done(function (fields) {
            var $root = $('<dl>');
            _(fields).each(function (attributes, name) {
                $root.append($('<dt>').append($('<h4>').text(name)));
                var $attrs = $('<dl>').appendTo($('<dd>').appendTo($root));
                _(attributes).each(function (def, name) {
                    if (def instanceof Object) {
                        def = JSON.stringify(def);
                    }
                    $attrs
                        .append($('<dt>').text(name))
                        .append($('<dd style="white-space: pre-wrap;">').text(def));
                });
            });
            new Dialog(self, {
                title: _.str.sprintf(_t("Model %s fields"),
                                     self.dataset.model),
                buttons: {
                    Ok: function() { this.parents('.modal').modal('hide');}
                },
            }, $root).open();
        });
    },
    fvg: function() {
        var dialog = new Dialog(this, { title: _t("Fields View Get") }).open();
        $('<pre>').text(utils.json_node_to_xml(this.view.fields_view.arch, true)).appendTo(dialog.$el);
    },
    manage_filters: function() {
        this.do_action({
            res_model: 'ir.filters',
            name: _t('Manage Filters'),
            views: [[false, 'list'], [false, 'form']],
            type: 'ir.actions.act_window',
            context: {
                search_default_my_filters: true,
                search_default_model_id: this.dataset.model
            }
        });
    },
    translate: function() {
        this.do_action({
            name: _t("Technical Translation"),
            res_model : 'ir.translation',
            domain : [['type', '!=', 'object'], '|', ['name', '=', this.dataset.model], ['name', 'ilike', this.dataset.model + ',']],
            views: [[false, 'list'], [false, 'form']],
            type : 'ir.actions.act_window',
            view_type : "list",
            view_mode : "list"
        });
    },
    edit: function(params, evt) {
        this.do_action({
            res_model : params.model,
            res_id : params.id,
            name: evt.target.text,
            type : 'ir.actions.act_window',
            view_type : 'form',
            view_mode : 'form',
            views : [[false, 'form']],
            target : 'new',
            flags : {
                action_buttons : true,
                headless: true,
            }
        });
    },
    edit_workflow: function() {
        return this.do_action({
            res_model : 'workflow',
            name: _t('Edit Workflow'),
            domain : [['osv', '=', this.dataset.model]],
            views: [[false, 'list'], [false, 'form'], [false, 'diagram']],
            type : 'ir.actions.act_window',
            view_type : 'list',
            view_mode : 'list'
        });
    },
    print_workflow: function() {
        if (this.view.get_selected_ids && this.view.get_selected_ids().length == 1) {
            framework.blockUI();
            var action = {
                context: { active_ids: this.view.get_selected_ids() },
                report_name: "workflow.instance.graph",
                datas: {
                    model: this.dataset.model,
                    id: this.view.get_selected_ids()[0],
                    nested: true,
                }
            };
            this.session.get_file({
                url: '/web/report',
                data: {action: JSON.stringify(action)},
                complete: framework.unblockUI
            });
        } else {
            this.do_warn("Warning", "No record selected.");
        }
    },
    leave_debug: function() {
        window.location.search="?";
    },
});

return DebugManager;

});
