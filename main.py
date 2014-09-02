#!/usr/bin/env python
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
import webapp2, jinja2
from sets import Set
import os, cgi, string, random
from operator import itemgetter
from google.appengine.ext import db
from google.appengine.api import users, memcache
from datetime import datetime, timedelta

jinja_environment = jinja2.Environment(
		loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
        extensions=['jinja2.ext.autoescape'])

class Review(db.Model):
    username = db.StringProperty()
    date = db.DateProperty()
    movie = db.StringProperty()
    review = db.StringProperty()

class FollowedPerson(db.Model):
    username = db.StringProperty()
    followedPerson = db.StringProperty()

class SignedUp(db.Model):
    username = db.StringProperty()

class Favorite(db.Model):
    username = db.StringProperty()
    movie = db.StringProperty()
    genre = db.StringProperty()

class MainHandler(webapp2.RequestHandler):

    def getDate(self):
        TZoffset = timedelta(hours = -4)
        return datetime.now().date() + TZoffset #use eastern standard time

    def getUsername(self):
    	  return users.get_current_user()

    def getLogout(self):
    	  return users.create_logout_url('/')

    #called by post(), if the user is signing up to allow people to see their reviews
    def signUpUser(self, username):

        d = SignedUp(username = username)
        d.put() #add the user's name to the database
        cached_signup_set = memcache.get("signedUp")
        if cached_signup_set is not None:#if the cached signup set exists
             cached_signup_set.add(username)
             memcache.set("signedUp", cached_signup_set)
             self.response.write("<h1>You are now signed up for people to see your reviews. <a href='/'>Return to What to Watch</a></h1>")
        else: #creating cached_signup_set for first time
             cached_signup_set = set()
             cached_signup_set.add(username)
             memcache.add("signedUp", cached_signup_set)
             self.response.write("<h1>You are now signed up for people to see your reviews. <a href='/'>Return to What to Watch</a></h1>")

    #called by post(), if the user submitted the username of someone they'd like to follow
    def followPerson(self, username, personToFollow):

        e = FollowedPerson(username = username, followedPerson = personToFollow)
        e.put() #add the username/personToFollow to the database
        cached_followed_dict = memcache.get("followed") #get the dictionary of all users and the people they follow
        if cached_followed_dict is not None: #if this dictionary exists
            if username in cached_followed_dict: #if this user is already in the dictionary
              followedPeopleList = cached_followed_dict[username]
              followedPeopleList.append(personToFollow)
              cached_followed_dict[username] = followedPeopleList #add the key/value pair to the dictionary
            else: #if this is the first person the user is following
              cached_followed_dict[username] = [personToFollow]
            memcache.set("followed", cached_followed_dict)
            self.response.write("<h1>You are now signed up to see reviews from " + personToFollow + ". <a href='/'>Return to What to Watch</a></h1>")
        else: #creating cached_followed_dict for first time
          cached_followed_dict = {}
          cached_followed_dict[username] = [personToFollow]
          memcache.add("followed", cached_followed_dict)
          self.response.write("<h1>You are now signed up to see reviews from " + personToFollow + ". <a href='/'>Return to What to Watch</a></h1>")
    
    #called by post(), if the user submitted a review
    def saveReview(self, username, date, review, movie):

        f = Review(username = username, date = date, review = review, movie = movie)
        f.put() #add the username/date/review/movie to the database
        randomNumber = random.randint(1,100000)
        cached_reviews_key = username + "_" + str(randomNumber) #create a key for the review
        cached_reviews_value = [username, date, review, movie]
        cached_allReviews_dict = memcache.get("allReviews")
        if cached_allReviews_dict is not None: #if this dictionary exists
          cached_reviews_dict = cached_allReviews_dict.get(username) #get the cached dictionary of this user's reviews
          if cached_reviews_dict is not None: #if this dictionary exists
               cached_reviews_dict[cached_reviews_key] = cached_reviews_value #add the key/value pair to the dictionary
               cached_allReviews_dict[username] = cached_reviews_dict
               memcache.set("allReviews", cached_allReviews_dict)
               self.redirect("/")
          else: #if this is the user's first review
               cached_reviews_dict = {}
               cached_reviews_dict[cached_reviews_key] = cached_reviews_value
               cached_allReviews_dict[username] = cached_reviews_dict
               memcache.set("allReviews", cached_allReviews_dict)
               self.redirect("/")
        else: #creating cached_allReviews_dict for first time
          cached_reviews_dict = {}
          cached_reviews_dict[cached_reviews_key] = cached_reviews_value
          cached_allReviews_dict = {}
          cached_allReviews_dict[username] = cached_reviews_dict
          memcache.add("allReviews", cached_allReviews_dict)
          self.redirect("/")

    #called by post(), if the user submitted a favorite
    def saveFavorite(self, username, favoriteMovie, favoriteGenre):

        f = Favorite(username = username, movie = favoriteMovie, genre = favoriteGenre)
        f.put() #add the username/movie/genre to the database
        randomNumber = random.randint(1,100000)
        cached_favorite_key = username + "_" + str(randomNumber) #create a key for the favorite
        cached_favorite_value = [username, favoriteMovie, favoriteGenre]
        cached_allFavorites_dict = memcache.get("allFavorites")
        if cached_allFavorites_dict is not None: #if this dictionary exists
          cached_favorites_dict = cached_allFavorites_dict.get(username) #get the cached dictionary of this user's favorites
          if cached_favorites_dict is not None: #if this dictionary exists
               cached_favorites_dict[cached_favorite_key] = cached_favorite_value #add the key/value pair to the dictionary
               cached_allFavorites_dict[username] = cached_favorites_dict
               memcache.set("allFavorites", cached_allFavorites_dict)
               self.redirect("/")
          else: #if this is the user's first favorite
               cached_favorites_dict = {}
               cached_favorites_dict[cached_favorite_key] = cached_favorite_value
               cached_allFavorites_dict[username] = cached_favorites_dict
               memcache.set("allFavorites", cached_allFavorites_dict)
               self.redirect("/")
        else: #creating cached_allFavorites_dict for first time
          cached_favorites_dict = {}
          cached_favorites_dict[cached_favorite_key] = cached_favorite_value
          cached_allFavorites_dict = {}
          cached_allFavorites_dict[username] = cached_favorites_dict
          memcache.add("allFavorites", cached_allFavorites_dict)
          self.redirect("/")

    #called by mainMethod(), to refill part of cache
    def refillSignedUp(self):
      
        s = db.GqlQuery("SELECT * FROM SignedUp")
        cached_signup_set = set()
        for c in s:
          cached_signup_set.add(c.username) #add to the set of signed-up people
        memcache.set("signedUp",cached_signup_set) 

    #called by mainMethod(), to refill part of cache
    def refillFollowedPerson(self):

        f = db.GqlQuery("SELECT * FROM FollowedPerson")
        cached_followed_dict = {} #key-values will be username:list of people that user follows

        for b in f: #go through every entry. Each entry has a username and a followedPerson name
          if b.username in cached_followed_dict: #if the username for this entry has already been added to the dictionary that will be cached
            followedPeopleList = cached_followed_dict[b.username] #retrieve the to-be-cached list of people they follow
            followedPeopleList.append(b.followedPerson) #add another person to the to-be-cached list of people they follow
            cached_followed_dict[b.username] = followedPeopleList
          else: #if the username for this entry hasn't been added to the to-be-cached dictionary, start creating a list of the people that they follow
            cached_followed_dict[b.username] = [b.followedPerson]
        memcache.set("followed", cached_followed_dict)

    #called by mainMethod(), to refill part of cache
    def refillReview(self):

        t = db.GqlQuery("SELECT * FROM Review")
        cached_allReviews_dict = {}  #key-values will be username:all their reviews

        for a in t:
            randomNumber = random.randint(1,100000)
            cached_reviews_key = a.username + "_" + str(randomNumber) #create a key for storing the review in the cache
            cached_reviews_value = [a.username, a.date, a.review, a.movie]
            cached_reviews_dict = cached_allReviews_dict.get(a.username) #for the username associated with this review, retrieve the dictionary of
  #all their reviews (if this dictionary has been created already)
            if cached_reviews_dict is not None: #if the dictionary has been created, add a new key/value pair
                cached_reviews_dict[cached_reviews_key] = cached_reviews_value
                cached_allReviews_dict[a.username] = cached_reviews_dict
            else: #creating cached_reviews_dict for this particular user for first time
                cached_reviews_dict = {}
                cached_reviews_dict[cached_reviews_key] = cached_reviews_value
                cached_allReviews_dict[a.username] = cached_reviews_dict
        memcache.add("allReviews", cached_allReviews_dict)

    #called by mainMethod(), to refill part of cache
    def refillFavorite(self):

        t = db.GqlQuery("SELECT * FROM Favorite")
        cached_allFavorites_dict = {}  # key-values will be username:all their favorites

        for a in t: #go through each favorite
             randomNumber = random.randint(1,100000)
             cached_favorite_key = a.username + "_" + str(randomNumber) #create a key for storing the favorite in the cache
             cached_favorite_value = [a.username, a.movie, a.genre]
             cached_favorites_dict = cached_allFavorites_dict.get(a.username) #for the username associated with this review, retrieve the dictionary of
  #all their favorites (if this dictionary has been created already)
             if cached_favorites_dict is not None: #if the dictionary has been created, add a new key/value pair
                 cached_favorites_dict[cached_favorite_key] = cached_favorite_value
                 cached_allFavorites_dict[a.username] = cached_favorites_dict
             else: #creating cached_favorites_dict for this particular user for first time
                 cached_favorites_dict = {}
                 cached_favorites_dict[cached_favorite_key] = cached_favorite_value
                 cached_allFavorites_dict[a.username] = cached_favorites_dict
        memcache.add("allFavorites", cached_allFavorites_dict)  

    #called by post() method, if the user submitted the username of someone they'd like to follow
    def isPersonSignedUp(self, personToFollow):
          
        cached_signup_set = memcache.get("signedUp")
        if cached_signup_set is not None: #if at least one person has signed up
          if personToFollow in cached_signup_set: #if the personToFollow has signed up to be followed
              return True
          else:
              return False
        else:
          self.response.write("<h1>Sorry, there's been a problem accessing the list of people who've signed up. Please try again later.<a href='/'>Return to What to Watch</a></h1>")

    #called by mainMethod()
    def hasUserSignedUp(self, username, cached_signedUp_set):

        if cached_signedUp_set is not None: #if at least one person has signed up
          if username in cached_signedUp_set: #if this user has signed up
            thisUserSignedUp = 1 #this variable determines whether or not the user sees the signup button 
          else:
            thisUserSignedUp = 0
        else: #if nobody has signed up
          thisUserSignedUp = 0
        return thisUserSignedUp

    #called by prepTemplate() and prepSelectedTemplate()
    def prepMyReviewsList(self, mycached_reviews_dict, myReviews_list):
           
        for key in mycached_reviews_dict: #go through each of this user's reviews, and add them to the list called myReviews
            yearmonthday = format(mycached_reviews_dict[key][1], '%Y%m%d')
            if int(yearmonthday) > 20130815:
                month = format(mycached_reviews_dict[key][1], '%m')
                if month[0] == "0":
                  month = month[1:]
                day = format(mycached_reviews_dict[key][1], '%d')
                try:
                  myReviews_list.append({"yearmonthday": yearmonthday, "month": month, "day": day, "text": mycached_reviews_dict[key][2], "movie": mycached_reviews_dict[key][3]})
                except TypeError:
                  pass

    #called by prepTemplate()
    def prepOthersReviewsList(self, followedPeopleList, othersReviews_list):
           
        cached_allReviews_dict = memcache.get("allReviews")
        for person in followedPeopleList:
            cached_reviews_dict = cached_allReviews_dict.get(person) #get the dictionary of reviews for each person this user is following
            if cached_reviews_dict is not None:
              for key in cached_reviews_dict:
                yearmonthday = format(cached_reviews_dict[key][1], '%Y%m%d')
                if int(yearmonthday) > 20130815:
                  month = format(cached_reviews_dict[key][1], '%m')
                  if month[0] == "0":
                    month = month[1:]
                  day = format(cached_reviews_dict[key][1], '%d')
                  try:
                      othersReviews_list.append({"reviewer":cached_reviews_dict[key][0], "text":cached_reviews_dict[key][2], "yearmonthday": yearmonthday, "month": month, "day": day,  "movie":cached_reviews_dict[key][3]})
                  except TypeError:
                      pass
    
    #called by prepTemplate() and prepSelectedTemplate()
    def prepMyFavoritesList(self, mycached_favorites_dict, myFavorites_list):
           
        for key in mycached_favorites_dict: #go through each of this user's favorites, and add them to myFavorites_list
            try:
              myFavorites_list.append({"movie": mycached_favorites_dict[key][1], "genre": mycached_favorites_dict[key][2]})
            except TypeError:
              pass

    #called by mainMethod(), when the user chooses to see a selected friend's reviews and favorites
    def prepSelectedTemplate(self, username, selectedUsername, selectedReviews_list, selectedFavorites_list, selected_cached_reviews, selected_cached_favorites, myReviews_list, myFavorites_list):
            
        #to prep selectedReviews_list:
        self.prepMyReviewsList(selected_cached_reviews, selectedReviews_list)
        #to prep selectedFavorites_list:
        if selected_cached_favorites is not None: #if this user has favorites                  
          self.prepMyFavoritesList(selected_cached_favorites, selectedFavorites_list)
               
    #called by mainMethod()
    def prepTemplate(self, username, cached_followed_dict, mycached_reviews_dict, mycached_favorites_dict, othersReviews_list, myReviews_list, myFavorites_list):

        if mycached_reviews_dict is not None: #if this user has saved reviews
          self.prepMyReviewsList(mycached_reviews_dict, myReviews_list)

        if username in cached_followed_dict: #if this user is following people
          followedPeopleList = cached_followed_dict[username]
          self.prepOthersReviewsList(followedPeopleList, othersReviews_list)

        if mycached_favorites_dict is not None: #if this user has favorites
          self.prepMyFavoritesList(mycached_favorites_dict, myFavorites_list)

    #mainMethod() is called by the get() method or post() method (if selectedUsername)
    def mainMethod(self, username, selectedUsername, logout):

        myReviews_list = []
        myFavorites_list = []
        cached_signedUp_set = memcache.get("signedUp") #get the list of people who've signed up
        cached_allReviews_dict = memcache.get("allReviews")
        cached_allFavorites_dict = memcache.get("allFavorites")

        if cached_signedUp_set is None: #if this part of the cache has been lost
            self.refillSignedUp()
            cached_signedUp_set = memcache.get("signedUp")
        thisUserSignedUp = self.hasUserSignedUp(username, cached_signedUp_set)
        
        if cached_allReviews_dict is None: #if this part of the cache has been lost
            self.refillReview()
            cached_allReviews_dict = memcache.get("allReviews")
        mycached_reviews_dict = cached_allReviews_dict.get(username) 
        
        if cached_allFavorites_dict is None: #if this part of the cache has been lost
            self.refillFavorite()
            cached_allFavorites_dict = memcache.get("allFavorites")
        mycached_favorites_dict = cached_allFavorites_dict.get(username)
        
        if selectedUsername is None: #the user hasn't chosen to see a selected friend's reviews and favorites
          othersReviews_list = []
          cached_followed_dict = memcache.get("followed") #get the dictionary containing users and the people they follow
         
          if cached_followed_dict is None: #if this part of the cache has been lost
            self.refillFollowedPerson()
            cached_followed_dict = memcache.get("followed")

          self.prepTemplate(username, cached_followed_dict, mycached_reviews_dict, mycached_favorites_dict, othersReviews_list, myReviews_list, myFavorites_list)

          othersReviews_list.sort(key = itemgetter("yearmonthday"), reverse = True)
          myReviews_list.sort(key = itemgetter("yearmonthday"), reverse = True)

          template_values = {"othersReviews" : othersReviews_list, "myReviews" : myReviews_list, "myFavorites" : myFavorites_list, "username":username, "logout":logout, "signedup":thisUserSignedUp}

        else: #requested a selectedUsername's reviews and favorites
          selectedReviews_list = []
          selectedFavorites_list = []
          selected_cached_reviews = cached_allReviews_dict.get(selectedUsername)
          selected_cached_favorites = cached_allFavorites_dict.get(selectedUsername)

          self.prepSelectedTemplate(username, selectedUsername, selectedReviews_list, selectedFavorites_list, selected_cached_reviews, selected_cached_favorites, myReviews_list, myFavorites_list)

          selectedReviews_list.sort(key = itemgetter("yearmonthday"), reverse = True)
          myReviews_list.sort(key = itemgetter("yearmonthday"), reverse = True)

          template_values = {"selectedReviews" : selectedReviews_list, "selectedFavorites" : selectedFavorites_list,"myReviews" : myReviews_list, "myFavorites" : myFavorites_list, "username":username, "selectedUsername" : selectedUsername, "logout":logout, "signedup":thisUserSignedUp}
        
        template = jinja_environment.get_template('index.html')
        self.response.write(template.render(template_values))

    def get(self):

      username = self.getUsername()
      logout = self.getLogout()

      if username:
        self.mainMethod(str(username), None, logout)

      else:
      	self.redirect(users.create_login_url(self.request.uri))

    def post(self):

      username = str(self.getUsername())
      logout = self.getLogout()
      date = self.getDate()

      signUp = self.request.get("signUp")
      personToFollowSubmit = self.request.get("personToFollowSubmit")
      personToFollow = cgi.escape(self.request.get("personToFollow"))
      movieSubmit = self.request.get("movieSubmit")
      movie = cgi.escape(self.request.get("movie"))
      review = cgi.escape(self.request.get("submittedReview"))
      favoriteSubmit = self.request.get("favoriteSubmit")
      favoriteMovie = cgi.escape(self.request.get("favoriteMovie"))
      favoriteGenre = cgi.escape(self.request.get("favoriteGenre"))
      selectedUsername = self.request.get("selectedUsername")

      if selectedUsername: #if the user wants to see a selected friend's reviews and favorites
        self.mainMethod(username, selectedUsername, logout)

      if signUp: #if the user is signing up to allow people to see their reviews
        self.signUpUser(username)

      if personToFollowSubmit: #if the user clicked the submit button for following someone
        if personToFollow: #if the user submitted the username of someone they'd like to follow
          if (self.isPersonSignedUp(personToFollow)):
            self.followPerson(username, personToFollow)
          else:
          	self.response.write("<h1>Sorry, that person is not signed up. <a href='/'>Return to What to Watch</a></h1>")
        else:
          self.response.write("<h1>Please enter a username for a person whose reviews you'd like to see. <a href='/'>Return to What to Watch</a></h1>")
      
      if movieSubmit: #if the user clicked the submit button for saving a review
        if movie and review: #if the user submits a review
          self.saveReview(username, date, review, movie)
        else:
          self.response.write("<h1>Please enter the name of the movie, and a review. <a href='/'>Return to What to Watch</a></h1>")

      if favoriteSubmit: #if the user clicked the submit button for saving a favorite
        if favoriteMovie and favoriteGenre: #if the user submits a favoriteMovie
          self.saveFavorite(username, favoriteMovie, favoriteGenre)
        else:
          self.response.write("<h1>Please enter the name of the movie and the genre. <a href='/'>Return to What to Watch</a></h1>")

app = webapp2.WSGIApplication([
    ('/', MainHandler)], debug=True)
