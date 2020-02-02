#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import webapp2
import jinja2
import os
import sys
from google.appengine.ext import db


jinja_environment = jinja2.Environment(autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))


class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)
	def render_str(self, template, **params):
		t = jinja_environment.get_template(template)
		return t.render(params)
	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))


###DB
class Emaile(db.Model):
	email = db.EmailProperty(required=True) #StringProperty
	created = db.DateTimeProperty(auto_now_add=True)


###PAGES
class MainPage(Handler):
	def render_front(self, error=""):
		self.render("index.html")
	def get(self):
		self.render_front()

##### Żartem
class DlugieImiePage(Handler):
    def get(self):
		self.render("zartem/o-zbyt-dlugim-imieniu.html")
class GospodarstwoPage(Handler):
    def get(self):
		self.render("zartem/moje-male-gospodarstwo.html")
class IgnacyPage(Handler):
    def get(self):
		self.render("zartem/samotny-ignacy.html")
class JedenDzienPage(Handler):
    def get(self):
		self.render("zartem/jeden-dzien-z-zycia-polskiej-firmy.html")
class KochajmyPage(Handler):
    def get(self):
		self.render("zartem/kochajmy_sie.html")
class KotPage(Handler):
    def get(self):
		self.render("zartem/kot.html")
class MedrzecPage(Handler):
	def get(self):
		self.render("zartem/medrzec-pemienia-chiquxiawan.html")
class NiesmiertelnyPage(Handler):
	def get(self):
		self.render("zartem/niesmiertelny.html")
class PatriotaPage(Handler):
	def get(self):
		self.render("zartem/jak_byc_patriota.html")
class StatystykaPage(Handler):
	def get(self):
		self.render("zartem/statystyka-bogini-racjonalistow.html")
class ZabkiPage(Handler):
    def get(self):
		self.render("zartem/prawda_o_zabkach.html")
class RufaPage(Handler):
    def get(self):
		self.render("zartem/rufa-hornety.html")
class WystepPage(Handler):
    def get(self):
		self.render("zartem/wystep-zycia.html")
class ZaPieknemPage(Handler):
    def get(self):
		self.render("zartem/pogon_za_pieknem.html")


##### Serio
class BiochemiaPage(Handler):
	def get(self):
		self.render("serio/biochemia.html")
class FantomPage(Handler):
	def get(self):
		self.render("serio/fantom.html")
class LustroPage(Handler):
    def get(self):
		self.render("serio/lustro.html")
class Marsjanie1Page(Handler):
    def get(self):
		self.render("serio/marsjanie-cz1.html")
class NiebieskiePage(Handler):
    def get(self):
		self.render("serio/panstwo-niebieskie.html")
class PoStudiachPage(Handler):
    def get(self):
		self.render("serio/co-robic-po-studiach.html")
class SOSPage(Handler):
	def get(self):
		self.render("serio/sos.html")
class WKosmosiePage(Handler):
    def get(self):
		self.render("serio/sami-w-kosmosie.html")


##### Zakalec
class BuddyzmPage(Handler):
	def get(self):
		self.render("zakalec/filozofia-buddyzmu.html")
class DyplomacjaPage(Handler):
	def get(self):
		self.render("zakalec/recenzja-dyplomacji-kissingera.html")
class FilozofiaPage(Handler):
	def get(self):
		self.render("zakalec/wnioski-dotyczace-filozofii.html")
class JakobiLeidentalPage(Handler):
	def get(self):
		self.render("zakalec/recenzja-sztuki-jakobi-i-leidental.html")
class OEtruskachPage(Handler):
	def get(self):
		self.render("zakalec/o-etruskach.html")
class OJaponiiPage(Handler):
	def get(self):
		self.render("zakalec/o-japonii.html")
class StarozytniPage(Handler):
	def get(self):
		self.render("zakalec/obraz-swiata-wedlug-starozytnych.html")
class TerraformacjaPage(Handler):
	def get(self):
		self.render("zakalec/na-temat-terraformacji-marsa.html")


##### Okruchy
class Okruchy3Page(Handler):
	def get(self):
		self.render("okruchy/2016-2018.html")
class Okruchy2Page(Handler):
	def get(self):
		self.render("okruchy/2014-2015.html")
class Okruchy1Page(Handler):
	def get(self):
		self.render("okruchy/1994-2013.html")



class Error404Page(Handler):
	def render_front(self, error=""):
		self.render("error404.html")
	def get(self):
		self.render_front()

class OAutorze(Handler):
	def get(self):
		self.render("o-autorze.html")

### Newsletter
class NewsletterPage(Handler):
	def render_front(self, email="", error=""):
		self.render("newsletter.html", email=email, error=error)
	def get(self):
		self.render_front()
	def post(self):
		email = self.request.get('email')

		#a = db.GqlQuery("select * FROM Emaile where email='sulfid@o2.pl'")
		#b = a[0]
		#b.delete()

		if (email):
			e = Emaile(email=email)
			e.put()
			self.redirect("/newsletter/wyslany")

		else:
			error = "Wpisz Email"
			self.render_front(email, error)

class NewsletterWyslanyPage(Handler):
	def get(self):
		self.render("newsletter_wyslany.html")

class BryEmailePage(Handler):
	def get(self):
		emaile = db.GqlQuery("SELECT * FROM Emaile ORDER BY created DESC")
		self.render("bry_emaile.html", emaile=emaile)



"""
class SomePage(Handler):
	def render_front(self, error="", kolor="", robic="", marzenie=""):
		self.render("1.html", error=error, kolor=kolor, robic=robic, marzenie=marzenie)
	def get(self):
		self.render_front()
	def post(self):
		kolor = self.request.get('kolor')
		robic = self.request.get('robic')
		marzenie = self.request.get('marzenie')

		if not (kolor and robic and marzenie):
			error = "Wypelnij porzadnie!"
			self.render_front(error, kolor, robic, marzenie)

		else:
			error = ""
			self.redirect("/thanks")

class ThanksHandler(Handler):
	def get(self):
		self.render("2.html")

class AddComHandler(Handler):
	def render_front(self, nick="", comment="", error=""):
		self.render("3.html", nick=nick, comment=comment, error=error)
	def get(self):
		self.render_front()
	def post(self):
		nick = self.request.get('nick')
		comment = self.request.get('comment')

		#a = db.GqlQuery("select * FROM Komentarz where nick='mniam'")
		#b = a[0]
		#b.delete()

		if (nick and comment):
			com = Komentarz(nick=nick, comment=comment)
			com.put()
			self.redirect("/comments")

		else:
			error = "Wpisz Nick i Komentarz"
			self.render_front(nick, comment, error)

class CommentsHandler(Handler):
	def get(self):
		comments = db.GqlQuery("SELECT * FROM Komentarz ORDER BY created DESC")
		self.render('4.html', comments=comments)
"""

zartem_urls = [('/zartem/jak-byc-patriota', PatriotaPage),
                ('/zartem/kochajmy-sie', KochajmyPage),
                ('/zartem/pogon-za-pieknem', ZaPieknemPage),
                ('/zartem/jeden-dzien-z-zycia-polskiej-firmy', JedenDzienPage),
                ('/zartem/kot', KotPage),
                ('/zartem/wystep-zycia', WystepPage),
                ('/zartem/rufa-hornety', RufaPage),
                ('/zartem/prawda-o-zabkach', ZabkiPage),
                ('/zartem/samotny-ignacy', IgnacyPage),
                ('/zartem/o-zbyt-dlugim-imieniu', DlugieImiePage),
                ('/zartem/moje-male-gospodarstwo', GospodarstwoPage),
                ('/zartem/medrzec-plemienia-chiquxiawan', MedrzecPage),
                ('/zartem/niesmiertelny', NiesmiertelnyPage),
                ('/zartem/statystyka-bogini-racjonalistow', StatystykaPage)
                ]

serio_urls = [('/serio/co-robic-po-studiach', PoStudiachPage),
               ('/serio/biochemia', BiochemiaPage),
               ('/serio/lustro', LustroPage),
               ('/serio/marsjanie-cz1', Marsjanie1Page),
    		   ('/serio/panstwo-niebieskie', NiebieskiePage),
    		   ('/serio/sami-w-kosmosie', WKosmosiePage),
               ('/serio/fantom', FantomPage),
               ('/serio/sos', SOSPage),
                ]

zakalec_urls = [('/zakalec/o-etruskach', OEtruskachPage),
                ('/zakalec/obraz-swiata-wedlug-starozytnych', StarozytniPage),
                ('/zakalec/o-japonii', OJaponiiPage),
                ('/zakalec/na-temat-terraformacji-marsa', TerraformacjaPage),
                ('/zakalec/wnioski-dotyczace-filozofii', FilozofiaPage),
                ('/zakalec/recenzja-sztuki-jakobi-i-leidental', JakobiLeidentalPage),
                ('/zakalec/na-czym-polega-filozofia-buddyzmu', BuddyzmPage),
                ('/zakalec/recenzja-dyplomacji-kissingera', DyplomacjaPage),
                ]

okruchy_urls = [('/okruchy/2016-2018', Okruchy3Page),
                ('/okruchy/2014-2015', Okruchy2Page),
                ('/okruchy/1994-2013', Okruchy1Page),
                ]

other_urls = [('/', MainPage),
               ('/newsletter/zapisz', NewsletterPage),
               ('/newsletter/wyslany', NewsletterWyslanyPage),
               ('/bry/emaile', BryEmailePage),
               ('/error404', Error404Page),
               ('/o-autorze', OAutorze),
               ] #, ('/comments', CommentsHandler)], debug=True)



all_urls = zartem_urls + serio_urls + zakalec_urls + okruchy_urls + other_urls

app = webapp2.WSGIApplication(all_urls, debug=True)
