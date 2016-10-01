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

class PatriotaPage(Handler):
	def render_front(self, error=""):
		self.render("jak_byc_patriota.html")
	def get(self):
		self.render_front()

class KochajmyPage(Handler):
	def render_front(self, error=""):
		self.render("kochajmy_sie.html")
	def get(self):
		self.render_front()

class ZaPieknemPage(Handler):
	def render_front(self, error=""):
		self.render("pogon_za_pieknem.html")
	def get(self):
		self.render_front()

class JedenDzienPage(Handler):
	def render_front(self, error=""):
		self.render("jeden-dzien-z-zycia-polskiej-firmy.html")
	def get(self):
		self.render_front()
        
class PoStudiachPage(Handler):
	def render_front(self, error=""):
		self.render("co-robic-po-studiach.html")
	def get(self):
		self.render_front()
		
class KotPage(Handler):
	def render_front(self, error=""):
		self.render("kot.html")
	def get(self):
		self.render_front()
        
class BiochemiaPage(Handler):
	def render_front(self, error=""):
		self.render("biochemia.html")
	def get(self):
		self.render_front()

class LustroPage(Handler):
	def render_front(self, error=""):
		self.render("lustro.html")
	def get(self):
		self.render_front()
		
class NiebieskiePage(Handler):
	def render_front(self, error=""):
		self.render("panstwo-niebieskie.html")
	def get(self):
		self.render_front()

class OkruchyPage(Handler):
	def render_front(self, error=""):
		self.render("okruchy.html")
	def get(self):
		self.render_front()
		
class Error404Page(Handler):
	def render_front(self, error=""):
		self.render("error404.html")
	def get(self):
		self.render_front()


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
        		
app = webapp2.WSGIApplication([('/', MainPage),
                               ('/jak-byc-patriota', PatriotaPage),
                               ('/kochajmy-sie', KochajmyPage),
                               ('/pogon-za-pieknem', ZaPieknemPage),
                               ('/jeden-dzien-z-zycia-polskiej-firmy', JedenDzienPage),
                               ('/co-robic-po-studiach', PoStudiachPage),
							   ('/kot', KotPage),
                               ('/biochemia', BiochemiaPage),
                               ('/lustro', LustroPage),
							   ('/panstwo-niebieskie', NiebieskiePage),
							   ('/okruchy', OkruchyPage),
                               ('/newsletter', NewsletterPage),
                               ('/newsletter/wyslany', NewsletterWyslanyPage),
                               ('/bry/emaile', BryEmailePage),
                               ('/error404', Error404Page),
                               ], debug=True) #, ('/comments', CommentsHandler)], debug=True)
