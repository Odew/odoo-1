openerp.web_editor = function(instance) {
    'use strict';

    /**
     * FieldTextHtml Widget
     * Intended for FieldText widgets meant to display HTML content. This
     * widget will instantiate an iframe with the editor summernote improved by odoo
     */

    var widget = instance.web.form.AbstractField.extend(instance.web.form.ReinitializeFieldMixin);

    instance.web.form.FieldTextHtmlSimple = widget.extend({
        template: 'web_editor.FieldTextHtmlSimple',
        _config: function () {
            var self = this;
            return {
                'focus': false,
                'height': 180,
                'toolbar': [
                    ['style', ['style']],
                    ['font', ['bold', 'italic', 'underline', 'clear']],
                    ['fontsize', ['fontsize']],
                    ['color', ['color']],
                    ['para', ['ul', 'ol', 'paragraph']],
                    ['table', ['table']],
                    ['insert', ['link', 'picture']],
                    ['history', ['undo', 'redo']]
                ],
                'styleWithSpan': false,
                'inlinemedia': ['p'],
                'lang': "odoo",
                'onChange': function (value) {
                    self.internal_set_value(value);
                    self.trigger('changed_value');
                }
            };
        },
        initialize_content: function() {
            var self = this;
            this.$textarea = this.$("textarea").val(this.get('value') || "<p><br/></p>");

            if (!this.get("effective_readonly")) {
                this.$textarea.summernote(this._config());

                if (this.field.translate && this.view) {
                    $(openerp.qweb.render('web_editor.FieldTextHtml.button.translate', this))
                        .appendTo(this.$('.note-toolbar'))
                        .on('click', this.on_translate);
                }

                var reset = _.bind(this.reset_history, this);
                this.view.on('load_record', this, reset);
                setTimeout(reset, 0);
            } else {
                this.$textarea.removeAttr("readonly").after('<div class="note-editable"/>');
            }
            this.$content = this.$('.note-editable:first');

            $(".oe-view-manager-content").on("scroll", function () {
                $('.o_table_handler').remove();
            });
            this._super();
        },
        reset_history: function () {
            var history = this.$content.data('NoteHistory');
            if (history) {
                history.reset();
                self.$('.note-toolbar').find('button[data-event="undo"]').attr('disabled', true);
            }
        },
        text_to_html: function (text) {
            var value = text || "";
            if (value.match(/^\s*$/)) {
                value = '<p><br/></p>';
            } else {
                value = "<p>"+value.split(/<br\/?>/).join("</p><p>")+"</p>";
                value = value.replace('<p><p>', '<p>').replace('</p></p>', '</p>');
            }
            return value;
        },
        render_value: function() {
            var value = this.get('value');
            this.$textarea.val(value || '');
            this.$content.html(this.text_to_html(value));
            this.$content.focusInEnd();
            var history = this.$content.data('NoteHistory');
            if (history && history.recordUndo()) {
                this.$('.note-toolbar').find('button[data-event="undo"]').attr('disabled', false);
            }
        },
        is_false: function() {
            return !this.get('value') || this.get('value') === "<p><br/></p>" || !this.get('value').match(/\S/);
        },
        get_value: function(save_mode) {
            if (save_mode && this.options['style-inline']) {
                openerp.web_editor_.class_to_style(this.$content);
                openerp.web_editor_.font_to_img(this.$content);
                this.internal_set_value(this.$content.html());
            }
            return this.get('value');
        },
        destroy_content: function () {
            $(".oe-view-manager-content").off("scroll");
            this.$textarea.destroy();
            this._super();
        }
    });

    instance.web.form.FieldTextHtmlTranslate = instance.web.form.FieldTextHtmlSimple.extend({
        events: {
            'keyup [contentEditable=true]': 'set_content_change',
            'click a': function (event) {event.preventDefault();},
        },
        _config: function () {
            var config = this._super();
            config.height = false;
            config.toolbar = [['history', ['undo', 'redo']]];
            return config;
        },
        initialize_content: function() {
            var self = this;
            this._super();
            if (!this.get("effective_readonly")) {
                $(openerp.qweb.render('web_editor.FieldTextHtml.button.reset', this))
                    .appendTo(this.$('.note-toolbar'))
                    .on('click', function () {
                        self.$content.data('NoteHistory').recordUndo();
                        self.set_value(self.view.datarecord.source);
                    });

                this.$textarea.removeAttr("readonly").on('keyup', function () {
                    var value = $(this).val();
                    self.internal_set_value(value);
                    self.$content.html(value);
                    self.trigger('changed_value');
                });

                if (this.view.datarecord.field_type === 'html') {
                    console.log("fdf");
                    this.set_translatable();
                }
            }
            this.$el.addClass('oe_form_field_html_translate');
        },
        set_content_change: function (event) {
            if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) {
                event.preventDefault();
                event.stopPropagation();
            }
            var $html = this.$content.clone();
            $html.find("*").addBack().filter('[contentEditable=true]').removeAttr('contentEditable');
            this.internal_set_value($html.html());
            this.trigger('changed_value');
        },
        set_translatable: function () {
            console.log("ooo");
            this.$content.find("*").addBack().contents()
                .filter(function() {
                    return this.nodeType === 3 && !!_.str.trim(this.textContent).length;
                }).each(function () {
                    $(this.parentNode).attr("contentEditable", true);
                });
        },
        render_value: function() {
            if (this.view.datarecord.field_type !== 'html') {
                this.$content.parent().hide();
                this.$textarea.show();
                if (this.$textarea.val() === "<p><br/></p>") {
                    this.$textarea.val("");
                }
            } else {
                this.$content.parent().show();
                this.$textarea.hide();
                this.$content.attr("contentEditable", false).off('keyup');

                if (!this.get("effective_readonly")) {
                    this.set_translatable();
                }
            }
            this._super();
            if (!this.get("effective_readonly") && this.view.datarecord.field_type === 'html') {
                this.set_translatable();
            }
        },
        destroy_content: function () {
            this.$content.find("*").addBack().removeAttr("contentEditable");
            this._super();
        }
    });

    instance.web.form.FieldTextHtml = widget.extend({
        template: 'web_editor.FieldTextHtml',
        start: function () {
            var self = this;

            this.callback = _.uniqueId('FieldTextHtml_');
            window.openerp[this.callback+"_editor"] = function (EditorBar) {
                setTimeout(function () {
                    self.on_editor_loaded(EditorBar);
                },0);
            };
            window.openerp[this.callback+"_content"] = function (EditorBar) {
                self.on_content_loaded();
            };
            window.openerp[this.callback+"_updown"] = null;
            window.openerp[this.callback+"_downup"] = function (value) {
                self.dirty = true;
                self.internal_set_value(value);
                self.trigger('changed_value');
                self.resize();
            };

            // init jqery objects
            this.$iframe = this.$el.find('iframe');
            this.document = null;
            this.$body = $();
            this.$content = $();

            this.$iframe.css('min-height', 'calc(100vh - 360px)');

            // init resize
            this.resize = function resize() {
                if (self.get('effective_readonly')) { return; }
                if ($("body").hasClass("o_form_FieldTextHtml_fullscreen")) {
                    self.$iframe.css('height', $("body").hasClass('o_form_FieldTextHtml_fullscreen') ? (document.body.clientHeight - self.$iframe.offset().top) + 'px' : '');
                } else {
                    self.$iframe.css("height", (self.$body.find("#oe_snippets").length ? 500 : 300) + "px");
                }
            };
            $(window).on('resize', self.resize);

            return this._super();
        },
        get_url: function () {
            var src = this.options.editor_url ? this.options.editor_url+"?" : "/web_editor/field/html?";
            var datarecord = this.view.get_fields_values();

            var attr = {
                'model': this.view.model,
                'field': this.name,
                'res_id': datarecord.id || '',
                'callback': this.callback
            };

            if (this.options['style-inline']) {
                attr['inline_mode'] = 1;
            }
            if (this.options.snippets) {
                attr['snippets'] = this.options.snippets;
            }
            if (!this.get("effective_readonly")) {
                attr['enable_editor'] = 1;
            }
            if (this.field.translate) {
                attr['translatable'] = 1;
            }
            if (openerp.session.debug) {
                attr['debug'] = 1;
            }

            for (var k in attr) {
                src += "&"+k+"="+attr[k];
            }

            delete datarecord[this.name];
            src += "&datarecord="+ encodeURIComponent(JSON.stringify(datarecord));

            return src;
        },
        initialize_content: function() {
            this.$el.closest('.modal-body').css('max-height', 'none');
            this.$iframe = this.$el.find('iframe');
            this.document = null;
            this.$body = $();
            this.$content = $();
            this.dirty = false;
            this.editor_bar = false;
            window.openerp[this.callback+"_updown"] = null;
            this.$iframe.attr("src", this.get_url());
        },
        on_content_loaded: function () {
            var self = this;
            this.document = this.$iframe.contents()[0];
            this.$body = $("body", this.document);
            this.$content = this.$body.find("#wrapwrap .o_editable:first");
            self.render_value();
            setTimeout(this.resize,0);
        },
        on_editor_loaded: function (EditorBar) {
            var self = this;
            this.editor_bar = EditorBar;

            $("body").on('click', function (event) {
                if ($("body").hasClass('o_form_FieldTextHtml_fullscreen')) {
                    $("body").removeClass("o_form_FieldTextHtml_fullscreen");
                    self.$iframe.css('height', '');
                    event.preventDefault();
                    event.stopPropagation();
                }
            });

            if (this.get('value') && window.openerp[self.callback+"_updown"] && !(this.$content.html()||"").length) {
                self.render_value();
            }

            setTimeout(function () {
                self.add_button();
                setTimeout(self.resize,0);
            }, 0);
        },
        add_button: function () {
            var self = this;
            var $button = $(openerp.qweb.render('web_editor.FieldTextHtml.button', this)).appendTo($("#web_editor-top-edit", self.document));

            $button.on('click', '.oe_field_translate', function () {
                self.on_translate();
            });
            $button.on('click', '.o_fullscreen', function () {
                $("body").toggleClass("o_form_FieldTextHtml_fullscreen");
                self.resize();
            });
        },
        render_value: function() {
            var value = (this.get('value') || "").replace(/^<p[^>]*>(\s*|<br\/?>)<\/p>$/, '');
            if (!this.$content) {
                return;
            }
            if (!this.get("effective_readonly")) {
                if(window.openerp[this.callback+"_updown"]) {
                    window.openerp[this.callback+"_updown"](value, this.view.get_fields_values(), this.name);
                    this.resize();
                }
            } else {
                this.$content.html(value);
                this.$iframe.css("height", (this.$body.height()+20) + "px");
            }
        },
        is_false: function() {
            return this.get('value') === false || !this.$content.html().match(/\S/);
        },
        get_value: function(save_mode) {
            if (save_mode && this.editor_bar && this.editor_bar.snippets && this.dirty) {
                this.editor_bar.snippets.clean_for_save();
                this.internal_set_value( this.$content.html() );
            }
            return this.get('value');
        },
        destroy: function () {
            $(window).off('resize', self.resize);
            delete window.openerp[this.callback+"_editor"];
            delete window.openerp[this.callback+"_content"];
            delete window.openerp[this.callback+"_updown"];
            delete window.openerp[this.callback+"_downup"];
        }
    });

    instance.web.form.widgets = instance.web.form.widgets.extend({
        'html': 'instance.web.form.FieldTextHtmlSimple',
        'html_translate': 'instance.web.form.FieldTextHtmlTranslate',
        'html_frame': 'instance.web.form.FieldTextHtml',
    });
};
