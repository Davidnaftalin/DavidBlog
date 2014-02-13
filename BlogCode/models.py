
import webapp2
import jinja2
import random
import string
import hashlib
import os
import re
import hmac

from google.appengine.ext import db

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> USER DATABASE <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
SECRET = 'secret'

class User_DB(db.Model):
      db_user_name = db.StringProperty(required=True) 
      db_user_pass = db.StringProperty(required = True)
      db_user_email = db.StringProperty(required = False)
      db_date_created=db.DateTimeProperty(auto_now_add = True) 
      
      @classmethod
      def by_name(cls, name):
          u = User_DB.all().filter('db_user_name =', name).get()
          return u
        
      @classmethod
      def register(cls, name, pw, email = None):
          pw_hash = User_DB.make_pw_hash(name, pw)
          return User_DB(parent = User_DB.users_key(),
                                  db_user_name = name,
                                  db_user_pass = pw_hash,
                                  db_user_email = email) 

        
      @classmethod
      def by_id(cls, uid):
          return User_DB.get_by_id(uid, parent = User_DB.users_key())
      
      @classmethod
      def login(cls, name, pw):
          u = cls.by_name(name)
          if u and User_DB.valid_pw(name, pw, u.db_user_pass):
            return u

#HASING PROC
      @classmethod    
      def hash_str(cls, s):
          return hmac.new(SECRET, s).hexdigest()

      @classmethod
      def make_secure_val(cls, s):
          return ("%s|%s" % (s, User_DB.hash_str(s)))

      @classmethod
      def check_secure_val(cls, h):
          val = h.split('|')[0]
          if h == User_DB.make_secure_val(val):
            return val

#PASWWORD ENCRYPTION          
      @classmethod
      def make_salt(cls):
          return ''.join(random.choice(string.letters) for x in xrange(5))

      @classmethod
      def make_pw_hash(cls, name, pw, salt = None):
          if not salt:
            salt = User_DB.make_salt()
          h = hashlib.sha256(name + pw + salt).hexdigest()
          return '%s,%s' % (h, salt)

      @classmethod
      def valid_pw(cls, name, pw, h):
          salt = h.split(',')[1]
          return h == User_DB.make_pw_hash(name, pw, salt)
  
      @classmethod
      def users_key(cls, group = 'default'):
          return db.Key.from_path('users', group)
      
#>>>>>>>>>>>>>>>>>>>>>>>>>CONTENT DATABASE<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

class Blog_DB(db.Model):
      blog_title = db.StringProperty(required=True) 
      blog_entry = db.TextProperty(required = True)
      blog_user_name = db.StringProperty(required=False)
      created=db.DateTimeProperty(auto_now_add = True) 

      def as_dict(self):
          time_fmt = '%c'
          d = {'title': self.blog_title,
               'entry': self.blog_entry,
               'created': self.created.strftime(time_fmt)}
          return d



