(function () {
    'use strict';

    if (!openerp.website.translatable) {
        // Temporary hack until the editor bar is moved to the web client
        return;
    }

    var website = openerp.website;
    var web_editor = openerp.web_editor;

    web_editor.add_template_file('/website/static/src/xml/website.translator.xml');
    var nodialog = 'website_translator_nodialog';


    website.Translate = web_editor.Translate.extend({
        events: {
            'click [data-action="save"]': 'save',
            'click [data-action="cancel"]': 'cancel',
        },
        template: 'website.translator',
        onTranslateReady: function () {
            if(this.gengo_translate){
                this.translation_gengo_display();
            }
            this._super();
        },
        destroy: function () {
            this.$el.remove();
            this._super();
        }
    });

    website.TranslatorDialog = openerp.Widget.extend({
        events: _.extend({}, website.TopBar.prototype.events, {
            'hidden.bs.modal': 'destroy',
            'click button[data-action=activate]': function (ev) {
                this.trigger('activate');
            },
        }),
        template: 'website.TranslatorDialog',
        start: function () {
            this.$el.modal();
        },
    });

    website.TopBar.include({
        events: _.extend({}, website.TopBar.prototype.events, {
            'click [data-action="edit_master"]': 'edit_master',
            'click [data-action="translate"]': 'translate',
        }),
        start: function () {
            this.$('button[data-action=translate]').prop('disabled', web_editor.no_editor);
            return this._super();
        },
        translate: function () {
            var self = this;

            if (!localStorage[nodialog]) {
                var dialog = new website.TranslatorDialog();
                dialog.appendTo($(document.body));
                dialog.on('activate', this, function () {
                    localStorage[nodialog] = dialog.$('input[name=do_not_show]').prop('checked') || '';
                    dialog.$el.modal('hide');

                    self.on_translate();
                });
            } else {
                this.on_translate();
            }
        },
        on_translate: function () {
            var $editables = $('#wrapwrap [data-oe-model="ir.ui.view"], [data-oe-translate="1"]')
                    .not('link, script')
                    .not('#oe_snippets, #oe_snippets *, .navbar-toggle');

            if (!this.translator) {
                this.translator = new website.Translate(this, $editables, 'ir.ui.view', $(document.documentElement).data('view-xmlid'), 'arch');
                this.translator.on('saved cancel', this, this.stop_translate);
                this.translator.prependTo(document.body);
            } else {
                this.translator.setTarget($editables);
                this.translator.$el.show();
            }

            this.translator.edit();

            this.$('button[data-action=edit]').prop('disabled', true);
            this.$el.hide();
        },
        stop_translate: function () {
            this.translator.$el.hide();
            this.$('button[data-action=edit]').prop('disabled', false);
            this.$el.show();
        },
        edit_master: function (ev) {
            ev.preventDefault();
            var link = $('.js_language_selector a[data-default-lang]')[0];
            if (link) {
                link.search += (link.search ? '&' : '?') + 'enable_editor=1';
                window.location = link.attributes.href.value;
            }
        },
    });

})();
