odoo.define('rating.rating', function (require) {
    "use strict";

    var ajax = require('web.ajax');
    var Widget = require('web.Widget');
    var translation = require('web.translation');
    var _t = translation._t;

    var labels = {
        '0' : "",
        '1' : _t("I hated it"),
        '2' : _t("I don't like it"),
        '3' : _t("It's okay"),
        '4' : _t("I like it"),
        '5' : _t("I love it"),
    };
    var page_widgets = {};

    $(document).ready(function(){

        // Rating Card
        $('[data-toggle="rating-popover"]').popover({
            html : true,
            trigger: 'hover',
            title: function() {
                return $($(this).data('popover-selector')).find('.popover-title').html();
            },
            content: function() {
              return $($(this).data('popover-selector')).find('.popover-content').html();
            }
        });

        // Star Widget
        var RatingStarWidget = Widget.extend({
            events: {
                "mousemove .stars" : "moveOnStars",
                "mouseleave .stars" : "moveOut",
                "click .stars" : "clickOnStar",
            },
            _setup: function(){
                this.$input = this.$('input');
                this.star_list = this.$('.stars').find('i');

                this.half_star_enabled = this.$input.data('half_star_enabled');
                this.is_editable = !this.$input.data('is_disabled');
                this.fixed = false; // user has click or not
                // set the default value and bind event
                this.set("star_index", this.$input.data('default') || -1);
                this.on("change:star_index", this, this.changeStars);
            },
            setElement: function($el){
                this._super.apply(this, arguments);
                this._setup();
            },
            changeStars: function(){
                var index = Math.floor(this.get("star_index"));
                var nbr_star = index;
                // reset the stars
                this.star_list.removeClass('fa-star fa-star-half-o').addClass('fa-star-o');
                if(index >= 0){
                    // fill the star before the current pointed star
                    this.$('.stars').find("i:lt("+index+")").removeClass('fa-star-o fa-star-half-o').addClass('fa-star');
                    // add half star if decimal <= 0.5, a complete star otherwise for the current pointed star
                    var star_class = 'fa-star';
                    if(this.half_star_enabled){
                        var decimal = this.get("star_index") - index;
                        if(decimal <= 0.5 && false){
                            star_class = 'fa-star-half-o';
                            nbr_star += 0.5;
                        }else{
                            star_class = 'fa-star';
                            nbr_star += 1;
                        }
                    }
                    this.$('.stars').find("i:eq("+(index)+")").removeClass('fa-star-o fa-star fa-star-half-o').addClass(star_class);
                }else{
                    nbr_star = 0.0;
                }

                this.$input.val(nbr_star);
                this.$('.rate_text .label').text(labels[index+1]);
            },
            moveOut: function(){
                if(!this.fixed && this.is_editable){
                    this.set("star_index", -1);
                }
                this.fixed = false;
            },
            moveOnStars: function(e){
                if(this.is_editable){
                    var elem = this.$('.stars');
                    var x = e.pageX - $(elem).offset().left;
                    var w = this.$('.stars').width();
                    var percentage = (x/w)*100;
                    var res = (percentage/100)*this.star_list.length;
                    this.set("star_index", res);
                }
            },
            clickOnStar: function(e){
                if(this.is_editable){
                    this.fixed = true;
                }
            },
        });

        $('.o_rating_star_card').each(function(index, elem){
            page_widgets[index] = new RatingStarWidget().setElement(elem);
        })

    });

    return {
        rating_star_widgets : page_widgets
    };

});
