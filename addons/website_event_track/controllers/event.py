# -*- coding: utf-8 -*-

import collections
import datetime
import pytz
import re

from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.tools import html_escape as escape, DEFAULT_SERVER_DATETIME_FORMAT as DTF

class website_event(http.Controller):
    @http.route(['''/event/<model("event.event"):event>/track/<model("event.track", "[('event_id','=',event[0])]"):track>'''], type='http', auth="public", website=True)
    def event_track_view(self, event, track, **post):
        track = track.sudo()
        values = { 'track': track, 'event': track.event_id, 'main_object': track }
        return request.website.render("website_event_track.track_view", values)

    def _prepare_calendar(self, event, event_track_ids):
        local_tz = pytz.timezone(event.date_tz or 'UTC')
        locations = {}                  # { location: [track, start_date, end_date, rowspan]}
        dates = []                      # [ (date, {}) ]
        for track in event_track_ids:
            locations.setdefault(track.location_id or False, [])

        forcetr = True
        for track in event_track_ids:
            start_date = (datetime.datetime.strptime(track.date, DTF)).replace(tzinfo=pytz.utc).astimezone(local_tz)
            end_date = start_date + datetime.timedelta(hours = (track.duration or 0.5))
            location = track.location_id or False
            locations.setdefault(location, [])

            # New TR, align all events
            if forcetr or (start_date>dates[-1][0]) or not location:
                dates.append((start_date, {}, bool(location)))
                for loc in locations.keys():
                    if locations[loc] and (locations[loc][-1][2] > start_date):
                        locations[loc][-1][3] += 1
                    elif not locations[loc] or locations[loc][-1][2] < start_date:
                        locations[loc].append([False, locations[loc] and locations[loc][-1][2] or dates[0][0], start_date, 1])
                        dates[-1][1][loc] = locations[loc][-1]
                forcetr = not bool(location)

            # Add event
            if locations[location] and locations[location][-1][1] > start_date:
                locations[location][-1][3] -= 1
            locations[location].append([track, start_date, end_date, 1])
            dates[-1][1][location] = locations[location][-1]
        return {
            'locations': locations,
            'dates': dates
        }

    # TODO: not implemented
    @http.route(['''/event/<model("event.event", "[('show_tracks','=',1)]"):event>/agenda'''], type='http', auth="public", website=True)
    def event_agenda(self, event, tag=None, **post):
        days_tracks = collections.defaultdict(lambda: [])
        for track in sorted(event.track_ids, key=lambda x: (x.date, bool(x.location_id))):
            if not track.date: continue
            days_tracks[track.date[:10]].append(track)

        days = {}
        days_tracks_count = {}
        for day, tracks in days_tracks.iteritems():
            days_tracks_count[day] = len(tracks)
            days[day] = self._prepare_calendar(event, tracks)

        speakers = {}
        for track in event.sudo().track_ids:
            speakers_name = u" – ".join(track.speaker_ids.mapped('name'))
            speakers[track.id] = speakers_name

        return request.website.render("website_event_track.agenda", {
            'event': event,
            'days': days,
            'days_nbr': days_tracks_count,
            'speakers': speakers,
            'tag': tag
        })

    @http.route([
        '''/event/<model("event.event", "[('show_tracks','=',1)]"):event>/track''',
        '''/event/<model("event.event", "[('show_tracks','=',1)]"):event>/track/tag/<model("event.track.tag"):tag>'''
        ], type='http', auth="public", website=True)
    def event_tracks(self, event, tag=None, **post):
        searches = {}
        if tag:
            searches.update(tag=tag.id)
            tracks = request.env['event.track'].search([("id", "in", event.track_ids.ids), ("tag_ids", "=", tag.id)])
        else:
            tracks = event.track_ids

        def html2text(html):
            return re.sub(r'<[^>]+>', "", html)

        values = {
            'event': event,
            'main_object': event,
            'tracks': tracks,
            'tags': event.tracks_tag_ids,
            'searches': searches,
            'html2text': html2text
        }
        return request.website.render("website_event_track.tracks", values)

    @http.route(['''/event/<model("event.event", "[('show_track_proposal','=',1)]"):event>/track_proposal'''], type='http', auth="public", website=True)
    def event_track_proposal(self, event, **post):
        values = { 'event': event }
        return request.website.render("website_event_track.event_track_proposal", values)

    @http.route(['/event/<model("event.event"):event>/track_proposal/post'], type='http', auth="public", methods=['POST'], website=True)
    def event_track_proposal_post(self, event, **post):

        tags = []
        for tag in event.allowed_track_tag_ids:
            if post.get('tag_'+str(tag.id)):
                tags.append(tag.id)

        track_description = '''<section>
    <div class="container">
        <div class="row">
            <div class="col-md-12 text-center">
                <h2>%s</h2>
            </div>
            <div class="col-md-12">
                <p>%s</p>
            </div>
            <div class="col-md-12">
                <h3>About The Author</h3>
                <p>%s</p>
            </div>
        </div>
    </div>
</section>''' % (escape(post['track_name']), 
            escape(post['description']), escape(post['biography']))

        track = request.env['event.track'].sudo().create({
            'name': post['track_name'],
            'event_id': event.id,
            'tag_ids': [(6, 0, tags)],
            'user_id': False,
            'description': track_description
        })

        track.message_post(body="""Proposed By: %s<br/>
          Mail: <a href="mailto:%s">%s</a><br/>
          Phone: %s""" % (escape(post['partner_name']), escape(post['email_from']), 
            escape(post['email_from']), escape(post['phone'])))

        values = {'track': track, 'event':event}
        return request.website.render("website_event_track.event_track_proposal_success", values)
