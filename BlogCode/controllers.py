import webapp2
import jinja2
import random
import string
import hashlib
import os
import re
import hmac
import json
import logging


from models import User_DB, Blog_DB
from google.appengine.ext import db 

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>MAIN BLOGHANDLER<<<<<<<<<<<<<<<<<<<<<<<<<<
class BlogHandler(webapp2.RequestHandler):
  def write(self, *a, **kw):
      self.response.out.write(*a, **kw)
###Defines function 'Write' which is a shortcut for self.response
      
  def render_str(self, template, **params):
      t = jinja_env.get_template(template)
      return t.render(params)
#     Function that takes a template name and returns a string of that rendered template
    
  def render(self, template, **kw):
      self.write(self.render_str(template, **kw))

  def set_secure_cookie(self, name, val):
      cookie_val = str(User_DB.make_secure_val(val))
      self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/' % (name, cookie_val))
      
  def logout(self):
      self.response.headers.add_header('Set-Cookie', "user_cookie_id=; Path=/")
      
  def login(self, user):
      self.set_secure_cookie('user_cookie_id', str(user.key().id()))
  
  def login_skip(self, template, redirect):
    if self.request.cookies.get('user_cookie_id'):
        if User_DB.check_secure_val(self.request.cookies.get('user_cookie_id')):
            self.redirect(redirect)
        else:
            self.render(template)
    else:
        self.render(template)

  def render_json(self, d):
    json_txt = json.dumps(d)
    self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
    self.write(json_txt)
        



#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> REGULAR EXPRESSIONS <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return USER_RE.match(username)

PASS_RE = re.compile("^.{3,20}$")
def valid_password(password):
    return PASS_RE.match(password)


EMAIL_RE = re.compile("^[\S]+@[\S]+\.[\S]+$")
def valid_email(email):
    return EMAIL_RE.match(email)

COOKIE_RE = re.compile(r'.+=;\s*Path=/')
def valid_cookie(cookie):
    return cookie and COOKIE_RE.match(cookie)


#>>>>>>>>>>>>>>>>>>>>>>>>>>  PAGES    <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
#>>>>>>>>>>>>>>>>>>>>>>>>>>FRONT PAGE<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
class FrontPage(BlogHandler):
  def render_front(self, blog_title="", blog_entry="", created="", login_name = "", logout="", submit_error=""):
      entries = db.GqlQuery("SELECT * FROM Blog_DB " 
                            "ORDER BY created DESC "
                            "LIMIT 10")

      
      if self.request.cookies.get('user_cookie_id'):
          if User_DB.check_secure_val(self.request.cookies.get('user_cookie_id')):
              self.render('boot-frontpage.html', entries = entries, 
                                                   login_name = 'Hello, ' + 
                                                   str(User_DB.by_id(int(User_DB.check_secure_val(self.request.cookies.get('user_cookie_id')))).db_user_name),
                                                   logout = '| logout?')
          else:
              self.render('boot-frontpage.html', entries = entries,
                                                   login_name = "",
                                                   logout = "")
              
      else:
        self.render('boot-frontpage.html', entries = entries, login_name = "", logout = "")


  def get(self, format='html'):     
      Blog_api_info = Blog_DB.all().order('-created')
      if self.request.url.endswith('.json'):
        format = 'json'
      else:
        format == 'html'
      if format =='html':
        self.render_front()
      else:
        return self.render_json([e.as_dict() for e in Blog_api_info])


#>>>>>>>>>>>>>>>>>>>>>>>>>> NEW POST PAGE <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
class NewPost(BlogHandler):
  def render_front(self, blog_title = "", blog_entry = "", error = "", login_name="", logout=""):
###blog_entry etc. are blank to start with but will change as the user submits posts.
      
      
      self.render('boot-newpost.html',
                  login_name = 'You are currently submitting as ' + str(User_DB.by_id(int(User_DB.check_secure_val(self.request.cookies.get('user_cookie_id')))).db_user_name),
                  logout = '| logout?')
      
      
  def get(self):
      if not self.request.cookies.get('user_cookie_id'):
          self.render('boot-login.html', submit_error="Please log in to submit content")
      else:
          self.render_front()
#1st get request: asking us to render the NewPost page.

  def post(self):
      blog_title = self.request.get("subject")
      blog_entry = self.request.get("content")
      user_name = str(User_DB.by_id(int(User_DB.check_secure_val(self.request.cookies.get('user_cookie_id')))).db_user_name)
#Post request: when form is submitted, it will pull throught the title and the entry name from the {{variables}} in HTML.
      
    
      if blog_title and blog_entry:
          blog_post = Blog_DB(blog_title = blog_title, blog_entry = blog_entry, blog_user_name=user_name)
          blog_post.put()

          blog_id = str(blog_post.key().id())
          self.redirect("/blog/%s" % blog_id)
      else:        
        error = 'We-need-some-subject-and-some-content-please'
        self.render('boot-newpost.html', blog_title = blog_title, blog_entry = blog_entry, error = error)


#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>PERMA LINK PAGE<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
class PermaLink(BlogHandler):
  def get(self, perm_id, format='html'):
      p = Blog_DB.get_by_id(int(perm_id))
      if self.request.url.endswith('json'):
        format == 'json'
        self.render_json(p.as_dict())
      else:
        format=='html'
        if p:
          self.render('boot-permalink.html', p = p)
        else:
          self.error(404)
          return



#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SIGN UP PAGE HANDLER <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

class SignUpPage(BlogHandler): 
    def get(self): 
        self.login_skip('boot-signup.html', '/blog')



    def post(self):
        user_name = self.request.get('username')
        user_pass = self.request.get('password')
        user_verify = self.request.get('verify')
        user_email = self.request.get('email')
        
        hash_user_pass = User_DB.make_pw_hash(user_name, user_pass)     
        user_error, pass_error, verify_error, email_error  = "", "", "", ""
        
        
        if not valid_username(user_name):
            user_error = 'Invalid-Username'

        if  not valid_password(user_pass):
            pass_error = 'Invalid-Password'
        
        elif user_pass != user_verify:
            verify_error = "Passwords-Don't-Match"

            
        if user_email:
            if not valid_email(user_email):  
                email_error = 'Invalid-Email'
        else:
            email_error = ""
            
            
        
        if  user_error or pass_error or verify_error or email_error:
            self.render('boot-signup.html', user_error = user_error,
                                       pass_error = pass_error,
                                       verify_error = verify_error,
                                       email_error = email_error)
        else:
            self.done()

    def done(self, *a, **kw):
        raise NotImplementedError

            
class Register(SignUpPage):
    def done(self):
        #make sure the user doesn't already exist
        u = User_DB.by_name(self.request.get('username'))
        if u:
            msg = 'That-user-already-exists.'
            self.render('boot-signup.html', user_error = msg)
        else:
            u = User_DB.register(self.request.get('username'), self.request.get('password'), self.request.get('email'))
            u.put()

            self.login(u)
            self.redirect('/blog')
            

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>LOGIN HANDLER<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
class LoginPage(BlogHandler):
    def get(self):
        if self.request.cookies.get('user_cookie_id'):
            if User_DB.check_secure_val(self.request.cookies.get('user_cookie_id')):
              self.redirect('/blog')
            else:
              self.render('boot-login.html')
        else:
              self.render('boot-login.html')

    def post(self):
        user_name = self.request.get('username')
        user_pass = self.request.get('password')

        login_error = ""
        
        u = User_DB.login(user_name, user_pass)
        if u:
            self.login(u)
            self.redirect('/blog')
        else:
            login_error = 'Invalid-login'
            self.render('boot-login.html', login_error = login_error)


#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>LOG OUT<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
class LogoutPage(BlogHandler):
  def get(self):
      self.logout()
      self.redirect("/blog/signup")
      
  
  

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>WELCOME HANDLER<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
            
class WelcomePage(BlogHandler):
      def get(self):
          if not self.request.cookies.get('user_cookie_id'):
              self.redirect("/blog/signup")
          else:
              self.response.out.write('Welcome, ' + User_DB.check_secure_val(self.request.cookies.get('user_cookie_id')))
                
        


#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>QUERY PAGE>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class TestPage(FrontPage):
  def get(self):
      entries = db.GqlQuery("SELECT * FROM Blog_DB")
      
      self.render('testpage.html', entries = entries)