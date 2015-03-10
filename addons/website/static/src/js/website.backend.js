odoo.define('website.backend', ['web.core', 'web.form_common', 'web.form_widgets'], function (require) {
"use strict";

var core = require('web.core');
var form_common = require('web.form_common');
var form_widgets = require('web.form_widgets'); // required to guarantee that
    // the overrride of fieldtexthtml works

var WidgetWebsiteButton = form_common.AbstractField.extend({
    template: 'WidgetWebsiteButton',
    render_value: function() {
        this._super();
        this.$()
            .toggleClass("success", this.get_value())
            .toggleClass("danger", !this.get_value());
        if (this.node.attrs.class) {
            this.$el.addClass(this.node.attrs.class);
        }
    },
});

core.form_widget_registry.add('website_button', WidgetWebsiteButton);

var widget = form_common.AbstractField.extend(form_common.ReinitializeFieldMixin);


var FieldTextHtml = widget.extend({
    template: 'FieldTextHtml',
    start: function () {
        var self = this;

        this.callback = _.uniqueId('FieldTextHtml_');
        odoo[this.callback+"_editor"] = function (EditorBar) {
            self.on_editor_loaded(EditorBar);
        };
        odoo[this.callback+"_content"] = function () {
            self.on_content_loaded();
        };
        odoo[this.callback+"_updown"] = null;
        odoo[this.callback+"_downup"] = function (value) {
            self.dirty = true;
            self.internal_set_value(value);
            self.trigger('changed_value');
            self.resize();
        };

        // init jqery objects
        this.$iframe = this.$('iframe');
        this.document = null;
        this.$body = $();
        this.$content = $();

        // init resize
        this.resize = function resize() {
            if ($("body").hasClass("o_form_FieldTextHtml_fullscreen")) {
                self.$iframe.css('height', $("body").hasClass('o_form_FieldTextHtml_fullscreen') ? (document.body.clientHeight - self.$iframe.offset().top) + 'px' : '');
            } else if (self.get('effective_readonly')) {
                var height = 110;
                try {
                    height += self.$body.height();
                    height +=  parseInt(self.$content.parent().css("margin-top"));
                } catch (e) {}
                self.$iframe.css("height", height+"px");
            } else {
                self.$iframe.css("height", (self.$body.find("#oe_snippets").length ? 500 : 300) + "px");
            }
        };
        $(window).on('resize', self.resize);

        return this._super();
    },
    get_url: function () {
        var src = this.options.editor_url ? this.options.editor_url+"?" : "/website/field/html?";
        var datarecord = this.view.get_fields_values();

        var attr = {
            'model': this.view.model,
            'field': this.name,
            'res_id': datarecord.id || '',
            'callback': this.callback
        };
        if (this.options.snippets) {
            attr.snippets = this.options.snippets;
        }
        if (!this.get("effective_readonly")) {
            attr.enable_editor = 1;
        }
        if (core.debug) {
            attr.debug = 1;
        }

        for (var k in attr) {
            src += "&"+k+"="+attr[k];
        }

        delete datarecord[this.name];
        src += "&datarecord="+ encodeURIComponent(JSON.stringify(datarecord));

        return src;
    },
    initialize_content: function() {
        this.$iframe = this.$el.find('iframe');
        this.document = null;
        this.$body = $();
        this.$content = $();
        this.dirty = false;
        this.editor = false;
        odoo[this.callback+"_set_value"] = function () {};

        this.$iframe.attr("src", this.get_url());
    },
    on_content_loaded: function () {
        this.document = this.$iframe.contents()[0];
        this.$body = $("body", this.document);
        this.$content = this.$body.find("#wrapwrap .o_editable:first");
        setTimeout(this.resize,0);
    },
    on_editor_loaded: function (EditorBar) {
        var self = this;
        this.editor = EditorBar;

        $("body").on('click', function (event) {
            if ($("body").hasClass('o_form_FieldTextHtml_fullscreen')) {
                $("body").removeClass("o_form_FieldTextHtml_fullscreen");
                self.$iframe.css('height', '');
                event.preventDefault();
                event.stopPropagation();
            }
        });

        setTimeout(function () {
            var $fullscreen = $('<span class="btn btn-primary" style="margin: 5px;padding: 1px; position: fixed; top: 0; right: 0; z-index: 2000;"><span class="o_fullscreen fa fa-arrows-alt" style="color: white;margin: 3px 5px;"></span></span>');
            $("#website-top-navbar", self.document).append($fullscreen);
            $fullscreen.on('click', function () {
                $("body").toggleClass("o_form_FieldTextHtml_fullscreen");
                self.resize();
            });
            setTimeout(self.resize,0);
        }, 500);
    },
    render_value: function() {
        if (!this.$content) {
            return;
        }
        if(odoo[this.callback+"_set_value"]) {
            odoo[this.callback+"_set_value"](this.get('value') || '', this.view.get_fields_values());
            this.resize();
        }
    },
    is_false: function() {
        return this.get('value') === false || this.get('value') === "";
    },
    get_value: function(save_mode) {
        if (save_mode && this.editor && this.editor.snippets && this.dirty) {
            this.editor.snippets.clean_for_save();
            this.internal_set_value( this.$content.prop('innerHTML') );
        }
        return this.get('value');
    },
    destroy: function () {
        $(window).off('resize', this.resize);
        delete odoo[this.callback];
        delete odoo[this.callback+"_content"];
        delete odoo[this.callback+"_updown"];
    }
});

core.form_widget_registry.add('html', FieldTextHtml);
});
