(function () {
    'use strict';

    var web_editor = openerp.web_editor;

    web_editor.snippet.BuildingBlock.include({
        _get_snippet_url: function () {
            return '/website/snippets';
        }
    });

    web_editor.snippet.options.background = web_editor.snippet.Option.extend({
        start: function ($change_target) {
            this.$bg = $change_target || this.$target;
            this._super();
            var src = this.$bg.css("background-image").replace(/url\(['"]*|['"]*\)|^none$/g, "");
            if (this.$bg.hasClass('oe_custom_bg')) {
                this.$el.find('li[data-choose_image]').data("background", src).attr("data-background", src);
            }
        },
        background: function(type, value, $li) {
            if (value && value.length) {
                this.$bg.css("background-image", 'url(' + value + ')');
                this.$bg.addClass("oe_img_bg");
            } else {
                this.$bg.css("background-image", "");
                this.$bg.removeClass("oe_img_bg").removeClass("oe_custom_bg");
            }
        },
        choose_image: function(type, value, $li) {
            if(type !== "click") return;

            var self = this;
            var $image = $('<img class="hidden"/>');
            $image.attr("src", value);
            $image.appendTo(self.$bg);

            var editor = new web_editor.widgets.MediaDialog(null, $image[0]);
            editor.appendTo(document.body);
            editor.$('[href="#editor-media-video"], [href="#editor-media-icon"]').addClass('hidden');

            editor.on('saved', self, function (o) {
                var value = $image.attr("src");
                $image.remove();
                self.$el.find('li[data-choose_image]').data("background", value).attr("data-background", value);
                self.background(type, value,$li);
                self.$bg.addClass('oe_custom_bg');
                self.$bg.trigger("snippet-option-change", [self]);
                self.set_active();
            });
            editor.on('cancel', self, function () {
                $image.remove();
            });
        },
        set_active: function () {
            var self = this;
            var src = this.$bg.css("background-image").replace(/url\(['"]*|['"]*\)|^none$/g, "");
            this._super();

            this.$el.find('li[data-background]:not([data-background=""])')
                .removeClass("active")
                .each(function () {
                    var background = $(this).data("background") || $(this).attr("data-background");
                    if ((src.length && background.length && src.indexOf(background) !== -1) || (!src.length && !background.length)) {
                        $(this).addClass("active");
                    }
                });

            if (!this.$el.find('li[data-background].active').size()) {
                this.$el.find('li[data-background=""]:not([data-choose_image])').addClass("active");
            } else {
                this.$el.find('li[data-background=""]:not([data-choose_image])').removeClass("active");
            }
        }
    });

    web_editor.snippet.options.slider = web_editor.snippet.Option.extend({
        unique_id: function () {
            var id = 0;
            $(".carousel").each(function () {
                var cid = 1 + parseInt($(this).attr("id").replace(/[^0123456789]/g, ''),10);
                if (id < cid) id = cid;
            });
            return "myCarousel" + id;
        },
        drop_and_build_snippet: function() {
            this.id = this.unique_id();
            this.$target.attr("id", this.id);
            this.$target.find("[data-slide]").attr("data-cke-saved-href", "#" + this.id);
            this.$target.find("[data-target]").attr("data-target", "#" + this.id);
            this.rebind_event();
        },
        on_clone: function ($clone) {
            var id = this.unique_id();
            $clone.attr("id", id);
            $clone.find("[data-slide]").attr("href", "#" + id);
            $clone.find("[data-slide-to]").attr("data-target", "#" + id);
        },
        // rebind event to active carousel on edit mode
        rebind_event: function () {
            var self = this;
            this.$target.find('.carousel-indicators [data-slide-to]').off('click').on('click', function () {
                self.$target.carousel(+$(this).data('slide-to')); });
        },
        clean_for_save: function () {
            this._super();
            this.$target.find(".item").removeClass("next prev left right active")
                .first().addClass("active");
            this.$target.find('.carousel-indicators').find('li').removeClass('active')
                .first().addClass("active");
        },
        start : function () {
            var self = this;
            this._super();
            this.$target.carousel({interval: false});
            this.id = this.$target.attr("id");
            this.$inner = this.$target.find('.carousel-inner');
            this.$indicators = this.$target.find('.carousel-indicators');
            this.$target.carousel('pause');
            this.rebind_event();
        },
        add_slide: function (type, value) {
            if(type !== "click") return;

            var self = this;
            var cycle = this.$inner.find('.item').length;
            var $active = this.$inner.find('.item.active, .item.prev, .item.next').first();
            var index = $active.index();
            this.$target.find('.carousel-control, .carousel-indicators').removeClass("hidden");
            this.$indicators.append('<li data-target="#' + this.id + '" data-slide-to="' + cycle + '"></li>');

            // clone the best candidate from template to use new features
            var $snippets = this.BuildingBlock.$snippets.find('.oe_snippet_body.carousel');
            var point = 0;
            var selection;
            var className = _.compact(this.$target.attr("class").split(" "));
            $snippets.each(function () {
                var len = _.intersection(_.compact(this.className.split(" ")), className).length;
                if (len > point) {
                    point = len;
                    selection = this;
                }
            });
            var $clone = $(selection).find('.item:first').clone();

            // insert
            $clone.removeClass('active').insertAfter($active);
            setTimeout(function() {
                self.$target.carousel().carousel(++index);
                self.rebind_event();
            },0);
            return $clone;
        },
        remove_slide: function (type, value) {
            if(type !== "click") return;

            if (this.remove_process) {
                return;
            }
            var self = this;
            var new_index = 0;
            var cycle = this.$inner.find('.item').length - 1;
            var index = this.$inner.find('.item.active').index();

            if (cycle > 0) {
                this.remove_process = true;
                var $el = this.$inner.find('.item.active');
                self.$target.on('slid.bs.carousel', function (event) {
                    $el.remove();
                    self.$indicators.find("li:last").remove();
                    self.$target.off('slid.bs.carousel');
                    self.rebind_event();
                    self.remove_process = false;
                    if (cycle == 1) {
                        self.on_remove_slide(event);
                    }
                });
                setTimeout(function () {
                    self.$target.carousel( index > 0 ? --index : cycle );
                }, 500);
            } else {
                this.$target.find('.carousel-control, .carousel-indicators').addClass("hidden");
            }
        },
        interval : function(type, value) {
            this.$target.attr("data-interval", value);
        },
        set_active: function () {
            this.$el.find('li[data-interval]').removeClass("active")
                .filter('li[data-interval='+this.$target.attr("data-interval")+']').addClass("active");
        },
    });

    web_editor.snippet.options.carousel = web_editor.snippet.options.slider.extend({
        getSize: function () {
            this.grid = this._super();
            this.grid.size = 8;
            return this.grid;
        },
        clean_for_save: function () {
            this._super();
            this.$target.removeClass('oe_img_bg ' + this._class).css("background-image", "");
        },
        load_style_options : function () {
            this._super();
            $(".snippet-option-size li[data-value='']").remove();
        },
        start : function () {
            var self = this;
            this._super();

            // set background and prepare to clean for save
            var add_class = function (c){
                if (c) self._class = (self._class || "").replace(new RegExp("[ ]+" + c.replace(" ", "|[ ]+")), '') + ' ' + c;
                return self._class || "";
            };
            this.$target.on('slid.bs.carousel', function () {
                if(self.editor && self.editor.styles.background) {
                    self.editor.styles.background.$bg = self.$target.find(".item.active");
                    self.editor.styles.background.set_active();
                }
                self.$target.carousel("pause");
            });
            this.$target.trigger('slid.bs.carousel');
        },
        add_slide: function (type, data) {
            if(type !== "click") return;

            var $clone = this._super(type, data);
            // choose an other background
            var bg = this.$target.data("snippet-option-ids").background;
            if (!bg) return $clone;

            var $styles = bg.$el.find("li[data-background]");
            var $select = $styles.filter(".active").removeClass("active").next("li[data-background]");
            if (!$select.length) {
                $select = $styles.first();
            }
            $select.addClass("active");
            $clone.css("background-image", $select.data("background") ? "url('"+ $select.data("background") +"')" : "");

            return $clone;
        },
        // rebind event to active carousel on edit mode
        rebind_event: function () {
            var self = this;
            this.$target.find('.carousel-control').off('click').on('click', function () {
                self.$target.carousel( $(this).data('slide')); });
            this._super();

            /* Fix: backward compatibility saas-3 */
            this.$target.find('.item.text_image, .item.image_text, .item.text_only').find('.container > .carousel-caption > div, .container > img.carousel-image').attr('contentEditable', 'true');
        },
    });

    web_editor.snippet.options.marginAndResize = web_editor.snippet.Option.extend({
        start: function () {
            var self = this;
            this._super();

            var resize_values = this.getSize();
            if (resize_values.n) this.$overlay.find(".oe_handle.n").removeClass("readonly");
            if (resize_values.s) this.$overlay.find(".oe_handle.s").removeClass("readonly");
            if (resize_values.e) this.$overlay.find(".oe_handle.e").removeClass("readonly");
            if (resize_values.w) this.$overlay.find(".oe_handle.w").removeClass("readonly");
            if (resize_values.size) this.$overlay.find(".oe_handle.size").removeClass("readonly");

            this.$overlay.find(".oe_handle:not(.size), .oe_handle.size .size").on('mousedown', function (event){
                event.preventDefault();

                var $handle = $(this);

                var resize_values = self.getSize();
                var compass = false;
                var XY = false;
                if ($handle.hasClass('n')) {
                    compass = 'n';
                    XY = 'Y';
                }
                else if ($handle.hasClass('s')) {
                    compass = 's';
                    XY = 'Y';
                }
                else if ($handle.hasClass('e')) {
                    compass = 'e';
                    XY = 'X';
                }
                else if ($handle.hasClass('w')) {
                    compass = 'w';
                    XY = 'X';
                }
                else if ($handle.hasClass('size')) {
                    compass = 'size';
                    XY = 'Y';
                }

                var resize = resize_values[compass];
                if (!resize) return;


                if (compass === 'size') {
                    var offset = self.$target.offset().top;
                    if (self.$target.css("background").match(/rgba\(0, 0, 0, 0\)/)) {
                        self.$target.addClass("resize_editor_busy");
                    }
                } else {
                    var xy = event['page'+XY];
                    var current = resize[2] || 0;
                    _.each(resize[0], function (val, key) {
                        if (self.$target.hasClass(val)) {
                            current = key;
                        }
                    });
                    var begin = current;
                    var beginClass = self.$target.attr("class");
                    var regClass = new RegExp("\\s*" + resize[0][begin].replace(/[-]*[0-9]+/, '[-]*[0-9]+'), 'g');
                }

                self.BuildingBlock.editor_busy = true;

                var cursor = $handle.css("cursor")+'-important';
                var $body = $(document.body);
                $body.addClass(cursor);

                var body_mousemove = function (event){
                    event.preventDefault();
                    if (compass === 'size') {
                        var dy = event.pageY-offset;
                        dy = dy - dy%resize;
                        if (dy <= 0) dy = resize;
                        self.$target.css("height", dy+"px");
                        self.$target.css("overflow", "hidden");
                        self.on_resize(compass, null, dy);
                        self.BuildingBlock.cover_target(self.$overlay, self.$target);
                        return;
                    }
                    var dd = event['page'+XY] - xy + resize[1][begin];
                    var next = current+1 === resize[1].length ? current : (current+1);
                    var prev = current ? (current-1) : 0;

                    var change = false;
                    if (dd > (2*resize[1][next] + resize[1][current])/3) {
                        self.$target.attr("class", (self.$target.attr("class")||'').replace(regClass, ''));
                        self.$target.addClass(resize[0][next]);
                        current = next;
                        change = true;
                    }
                    if (prev != current && dd < (2*resize[1][prev] + resize[1][current])/3) {
                        self.$target.attr("class", (self.$target.attr("class")||'').replace(regClass, ''));
                        self.$target.addClass(resize[0][prev]);
                        current = prev;
                        change = true;
                    }

                    if (change) {
                        self.on_resize(compass, beginClass, current);
                        self.BuildingBlock.cover_target(self.$overlay, self.$target);
                    }
                };

                var body_mouseup = function(){
                    $body.unbind('mousemove', body_mousemove);
                    $body.unbind('mouseup', body_mouseup);
                    $body.removeClass(cursor);
                    setTimeout(function () {
                        self.BuildingBlock.editor_busy = false;
                    },0);
                    self.$target.removeClass("resize_editor_busy");
                };
                $body.mousemove(body_mousemove);
                $body.mouseup(body_mouseup);
            });
            this.$overlay.find(".oe_handle.size .auto_size").on('click', function (event){
                self.$target.css("height", "");
                self.$target.css("overflow", "");
                self.BuildingBlock.cover_target(self.$overlay, self.$target);
                return false;
            });
        },
        getSize: function () {
            this.grid = {};
            return this.grid;
        },

        on_focus : function () {
            this._super();
            this.change_cursor();
        },

        change_cursor : function () {
            var _class = this.$target.attr("class") || "";

            var col = _class.match(/col-md-([0-9-]+)/i);
            col = col ? +col[1] : 0;

            var offset = _class.match(/col-md-offset-([0-9-]+)/i);
            offset = offset ? +offset[1] : 0;

            var overlay_class = this.$overlay.attr("class").replace(/(^|\s+)block-[^\s]*/gi, '');
            if (col+offset >= 12) overlay_class+= " block-e-right";
            if (col === 1) overlay_class+= " block-w-right block-e-left";
            if (offset === 0) overlay_class+= " block-w-left";

            var mb = _class.match(/mb([0-9-]+)/i);
            mb = mb ? +mb[1] : 0;
            if (mb >= 128) overlay_class+= " block-s-bottom";
            else if (!mb) overlay_class+= " block-s-top";

            var mt = _class.match(/mt([0-9-]+)/i);
            mt = mt ? +mt[1] : 0;
            if (mt >= 128) overlay_class+= " block-n-top";
            else if (!mt) overlay_class+= " block-n-bottom";

            this.$overlay.attr("class", overlay_class);
        },
        
        /* on_resize
        *  called when the box is resizing and the class change, before the cover_target
        *  @compass: resize direction : 'n', 's', 'e', 'w'
        *  @beginClass: attributes class at the begin
        *  @current: curent increment in this.grid
        */
        on_resize: function (compass, beginClass, current) {
            this.change_cursor();
        }
    });

    web_editor.snippet.options["margin-y"] = web_editor.snippet.options.marginAndResize.extend({
        getSize: function () {
            this.grid = this._super();
            var grid = [0,4,8,16,32,48,64,92,128];
            this.grid = {
                // list of class (Array), grid (Array), default value (INT)
                n: [_.map(grid, function (v) {return 'mt'+v;}), grid],
                s: [_.map(grid, function (v) {return 'mb'+v;}), grid],
                // INT if the user can resize the snippet (resizing per INT px)
                size: null
            };
            return this.grid;
        },
    });

    web_editor.snippet.options["margin-x"] = web_editor.snippet.options.marginAndResize.extend({
        getSize: function () {
            this.grid = this._super();
            var width = this.$target.parents(".row:first").first().outerWidth();

            var grid = [1,2,3,4,5,6,7,8,9,10,11,12];
            this.grid.e = [_.map(grid, function (v) {return 'col-md-'+v;}), _.map(grid, function (v) {return width/12*v;})];

            var grid = [-12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,0,1,2,3,4,5,6,7,8,9,10,11];
            this.grid.w = [_.map(grid, function (v) {return 'col-md-offset-'+v;}), _.map(grid, function (v) {return width/12*v;}), 12];

            return this.grid;
        },
        _drag_and_drop_after_insert_dropzone: function(){
            var self = this;
            var $zones = $(".row:has(> .oe_drop_zone)").each(function () {
                var $row = $(this);
                var width = $row.innerWidth();
                var pos = 0;
                while (width > pos + self.size.width) {
                    var $last = $row.find("> .oe_drop_zone:last");
                    $last.each(function () {
                        pos = $(this).position().left;
                    });
                    if (width > pos + self.size.width) {
                        $row.append("<div class='col-md-1 oe_drop_to_remove'/>");
                        var $add_drop = $last.clone();
                        $row.append($add_drop);
                        self._drag_and_drop_active_drop_zone($add_drop);
                    }
                }
            });
        },
        _drag_and_drop_start: function () {
            this._super();
            this.$target.attr("class",this.$target.attr("class").replace(/\s*(col-lg-offset-|col-md-offset-)([0-9-]+)/g, ''));
        },
        _drag_and_drop_stop: function () {
            this.$target.addClass("col-md-offset-" + this.$target.prevAll(".oe_drop_to_remove").length);
            this._super();
        },
        hide_remove_button: function() {
            this.$overlay.find('.oe_snippet_remove').toggleClass("hidden", !this.$target.siblings().length);
        },
        on_focus : function () {
            this._super();
            this.hide_remove_button();
        },
        on_clone: function ($clone) {
            var _class = $clone.attr("class").replace(/\s*(col-lg-offset-|col-md-offset-)([0-9-]+)/g, '');
            $clone.attr("class", _class);
            this.hide_remove_button();
            return false;
        },
        on_remove: function () {
            this._super();
            this.hide_remove_button();
        },
        on_resize: function (compass, beginClass, current) {
            if (compass === 'w') {
                // don't change the right border position when we change the offset (replace col size)
                var beginCol = Number(beginClass.match(/col-md-([0-9]+)|$/)[1] || 0);
                var beginOffset = Number(beginClass.match(/col-md-offset-([0-9-]+)|$/)[1] || beginClass.match(/col-lg-offset-([0-9-]+)|$/)[1] || 0);
                var offset = Number(this.grid.w[0][current].match(/col-md-offset-([0-9-]+)|$/)[1] || 0);
                if (offset < 0) {
                    offset = 0;
                }
                var colSize = beginCol - (offset - beginOffset);
                if (colSize <= 0) {
                    colSize = 1;
                    offset = beginOffset + beginCol - 1;
                }
                this.$target.attr("class",this.$target.attr("class").replace(/\s*(col-lg-offset-|col-md-offset-|col-md-)([0-9-]+)/g, ''));

                this.$target.addClass('col-md-' + (colSize > 12 ? 12 : colSize));
                if (offset > 0) {
                    this.$target.addClass('col-md-offset-' + offset);
                }
            }
            this._super(compass, beginClass, current);
        },
    });

    web_editor.snippet.options.resize = web_editor.snippet.options.marginAndResize.extend({
        getSize: function () {
            this.grid = this._super();
            this.grid.size = 8;
            return this.grid;
        },
    });

    web_editor.snippet.options.parallax = web_editor.snippet.Option.extend({
        getSize: function () {
            this.grid = this._super();
            this.grid.size = 8;
            return this.grid;
        },
        on_resize: function (compass, beginClass, current) {
            this.$target.data("snippet-view").set_values();
        },
        start : function () {
            var self = this;
            this._super();
            if (!self.$target.data("snippet-view")) {
                this.$target.data("snippet-view", new web_editor.snippet.animationRegistry.parallax(this.$target));
            }
            this.scroll();
            this.$target.on('snippet-option-change snippet-option-preview', function () {
                self.$target.data("snippet-view").set_values();
            });
            this.$target.attr('contentEditable', 'false');

            this.$target.find('> div > .oe_structure').attr('contentEditable', 'true'); // saas-3 retro-compatibility

            this.$target.find('> div > div:not(.oe_structure) > .oe_structure').attr('contentEditable', 'true');
        },
        scroll: function (type, value) {
            this.$target.attr('data-scroll-background-ratio', value);
            this.$target.data("snippet-view").set_values();
        },
        set_active: function () {
            var value = this.$target.attr('data-scroll-background-ratio') || 0;
            this.$el.find('[data-scroll]').removeClass("active")
                .filter('[data-scroll="' + (this.$target.attr('data-scroll-background-ratio') || 0) + '"]').addClass("active");
        },
        clean_for_save: function () {
            this._super();
            this.$target.find(".parallax")
                .css("background-position", '')
                .removeAttr("data-scroll-background-offset");
        }
    });

    web_editor.snippet.options.transform = web_editor.snippet.Option.extend({
        start: function () {
            var self = this;
            this._super();
            this.$overlay.find('.oe_snippet_clone, .oe_handles').addClass('hidden');
            this.$overlay.find('[data-toggle="dropdown"]')
                .on("mousedown", function () {
                    self.$target.transfo("hide");
                });
            this.$target.on('attributes_change', function () {
                self.resetTransfo();
            });

            // don't unactive transform if rotation and mouseup on an other container
            var cursor_mousedown = false;
            $(document).on('mousedown', function (event) {
                if (self.$overlay.hasClass('oe_active') && $(event.target).closest(".transfo-controls").length) {
                    cursor_mousedown = event;
                }
            });
            $(document).on('mouseup', function (event) {
                if (cursor_mousedown) {
                    event.preventDefault();

                    var dx = event.clientX-cursor_mousedown.clientX;
                    var dy = event.clientY-cursor_mousedown.clientY;
                    setTimeout(function () {
                        self.$target.focusIn().activateBlock();
                        if (10 < Math.pow(dx, 2)+Math.pow(dy, 2)) {
                            setTimeout(function () {
                                self.$target.transfo({ 'hide': false });
                            },0);
                        }
                    },0);
                    cursor_mousedown = false;
                }
            });
        },
        style: function (type, value) {
            if (type !== 'click') return;
            var settings = this.$target.data("transfo").settings;
            this.$target.transfo({ 'hide': (settings.hide = !settings.hide) });
        },
        clear_style: function (type, value) {
            if (type !== 'click') return;
            this.$target.removeClass("fa-spin").attr("style", "");
            this.resetTransfo();
        },
        move_summernote_select: function () {
            var self = this;
            var transfo = this.$target.data("transfo");
            $('body > .note-handle')
                .attr('style', transfo.$markup.attr('style'))
                .css({
                    'z-index': 0,
                    'pointer-events': 'none'
                })
                .off('mousedown mouseup')
                .on('mousedown mouseup', function (event) {
                    self.$target.trigger( jQuery.Event( event.type, event ) );
                })
                .find('.note-control-selection').attr('style', transfo.$markup.find('.transfo-controls').attr('style'))
                    .css({
                        'display': 'block',
                        'cursor': 'auto'
                    });
        },
        resetTransfo: function () {
            var self = this;
            this.$overlay.css('width', '');
            this.$overlay.data('not-cover_target', true);
            this.$target.transfo("destroy");
            this.$target.transfo({
                hide: true,
                callback: function () {
                    var pos = $(this).data("transfo").$center.offset();
                    self.$overlay.css({
                        'top': pos.top | 0,
                        'left': pos.left | 0,
                        'position': 'absolute',
                    });
                    self.$overlay.find(".oe_overlay_options").attr("style", "width:0; left:0!important; top:0;");
                    self.$overlay.find(".oe_overlay_options > .btn-group").attr("style", "width:160px; left:-80px;");

                    self.move_summernote_select();
                }});
            this.$target.data('transfo').$markup
                .on("mouseover", function () {
                    self.$target.trigger("mouseover");
                })
                .mouseover();
        },
        on_focus : function () {
            var self = this;
            setTimeout(function () {
                self.$target.css({"-webkit-animation": "none", "animation": "none"});
                self.resetTransfo();
            },0);
        },
        on_blur : function () {
            this.$target.transfo("hide");
            $('.note-handle').hide(); // hide selection of summernote
            this.$target.css({"-webkit-animation-play-state": "", "animation-play-state": "", "-webkit-transition": "", "transition": "", "-webkit-animation": "", "animation": ""});
        },
        clean_for_save: function () {
            this.on_blur();
            this._super();
        }
    });

    web_editor.snippet.options.ul = web_editor.snippet.Option.extend({
        start: function () {
            this._super();
            this.$target.data("snippet-view", new web_editor.snippet.animationRegistry.ul(this.$target, true));
        },
        reset_ul: function () {
            this.$target.find('.o_ul_toggle_self, .o_ul_toggle_next').remove();

            this.$target.find('li:has(>ul,>ol)').map(function () {
                    // get if the li contain a text label
                    var texts = _.filter(_.toArray(this.childNodes), function (a) { return a.nodeType == 3;});
                    if (!texts.length || !texts.reduce(function (a,b) { return a.textContent + b.textContent;}).match(/\S/)) {
                        return;
                    }
                    $(this).children('ul,ol').addClass('o_close');
                    return $(this).children(':not(ul,ol)')[0] || this;
                })
                .prepend('<a href="#" class="o_ul_toggle_self fa" />');

            var $li = this.$target.find('li:has(+li:not(>.o_ul_toggle_self)>ul, +li:not(>.o_ul_toggle_self)>ol)');
            $li.map(function () { return $(this).children()[0] || this; })
                .prepend('<a href="#" class="o_ul_toggle_next fa" />');
            $li.removeClass('o_open').next().addClass('o_close');

            this.$target.find("li").removeClass('o_open').css('list-style', '');
            this.$target.find("li:has(.o_ul_toggle_self, .o_ul_toggle_next), li:has(>ul,>ol):not(:has(>li))").css('list-style', 'none');
        },
        clean_for_save: function () {
            this._super();
            if (!this.$target.hasClass('o_ul_folded')) {
                this.$target.find(".o_close").removeClass("o_close");
            }
            this.$target.find("li:not(:has(>ul))").css('list-style', '');
        },
        toggle_class: function (type, value, $li) {
            this._super(type, value, $li);
            this.$target.data("snippet-view").stop();
            this.reset_ul();
            this.$target.find("li:not(:has(>ul))").css('list-style', '');
            this.$target.data("snippet-view", new web_editor.snippet.animationRegistry.ul(this.$target, true));
        }
    });

})();
