import webapp2
import controllers

app = webapp2.WSGIApplication([
    ('/blog/?(?:.json)?', controllers.FrontPage),
    ('/blog/newpost', controllers.NewPost),
    ('/blog/([0-9]+)(?:.json)?', controllers.PermaLink),
    ('/testpage', controllers.TestPage),
    ('/blog/signup', controllers.Register),
    ('/blog/welcome', controllers.WelcomePage),
    ('/blog/login', controllers.LoginPage),
    ('/blog/logout', controllers.LogoutPage)
], debug=True)
