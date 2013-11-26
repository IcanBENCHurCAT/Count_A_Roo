import praw
import time
import mechanize

#The pre-determined 'end of the list'
end_node = 'http://www.reddit.com/r/InternetAMA/comments/1opuiu/i_started_the_whole_switcharoo_thing_ama/'
#Name for the bot
agent = 'Count_A_Roo 1.0 by /u/icanbenchurcat'
#Open a connection to Reddit
	#Here is where you would add login credentials, if we needed to login
r = praw.Reddit(user_agent=agent)
#Keeps a list of 'possible' links, if the next node is not obvious
possibles = list()
#Fall-back method of opening reddit via a regular browser
br = mechanize.Browser()

#The list of keywords which the bot should prefer over 'plain-old-links'
keys = ["switch-a-roo", "switcharoo", "ah, the ol", "the old reddit", "switcheroo", "redditaroo"]
#Found a post that was confused for the 'next chain'. Avoid known 'bad-paths' with this list
ignoreList = ["reddit.com/r/cummingonfigurines"]

#output: url to the newest submission in /r/switcharoo
def getNewestSubmission():
	top = list(r.get_subreddit('switcharoo').get_new(limit=1))[0]
	return top.url

#input: url of the switcharoo comment
#output: url of the next switcharoo comment
def openLink(url):
	#Some people put garbage at the end of the link, strip it off
	index = url.find("#")
	if index != -1:
		url = url[:index]
	
	#find the postID, because I know the commentID is after it
	begin = url.find("/comments/")
	begin += len("/comments/")
	end = url.find("/",begin)
	
	nextID = url[begin:end]
	
	begin = url.find("/", end + 1)
	begin += 1
	end = url.find("?", begin)
	
	#there is no '?context=##' at the end of the link
		#use the entire link
	if(end < 0):
		end = len(url)
	
	#the ID of the comment is not needed, but can be gathered here
	#nextCommentID = url[begin:end]
	
	#trim the end of the link off, if needed (?context=##)
	url = url[:end]
	
	#open the next submission, see if the comment was directly linked to
	submission = r.get_submission(url)
	next_comment = submission.comments[0].body
	
	begin = next_comment.find("reddit.com/r/")
	end = next_comment.find(")", begin)
	retVal = next_comment[begin:end]
	
	#link could not be found, parse all of the comments until you can find the link
	if len(retVal) == 0:
		del possibles[0:len(possibles)]
		recurseComments(submission.comments[0].replies)
		
		removeBogusLinks()
		#if there is at least one, make a choice
		if len(possibles) > 0:
			retVal = listPossibles()
		#could not find any, try harder
		else:
			tryBrowser(url)
			retVal = listPossibles()
	
	#different links are formatted differently, make sure they all start the same
	if retVal.startswith("http://www.") == False:
		retVal = "http://www." + retVal
	return retVal

#input: a comment
#function: if we can find a link that looks good, add it to possibles
			#if we notice this comment has children, check the children
def recurseComments(parentNode):
	for reply in parentNode:
		if hasattr(reply, 'body') == False:
			continue
		index = reply.body.find("reddit.com/r/")
		if index != -1:
			end = reply.body.find(")", index)
			retVal = reply.body[index:end]
			possibles.append({"body":reply.body, "url":retVal})
		elif len(reply.replies) != 0:
			recurseComments(reply.replies)
	
#input: url of the next switcharoo
#function: opens a browser at url. examines all of the links to see
			#if any of the 'keys' are in the link text, add them to possibles
def tryBrowser(url):
	retVal = ""
	header = {'user-agent' : agent}
	req = mechanize.Request(headers=header, url=url)
	br.open(req)
	for link in br.links():
		if hasattr(link, "text"):
			for item in keys:
				index = str(link.text).lower().find(item)
				if(index != -1):
					url = link.url
					#different links are formatted differently, make sure they all start the same
					if url.startswith("http") == False:
						if url.startswith("www") == False:
							if url.startswith("reddit.com") == False:
								url = "http://www.reddit.com" + url
							else:
								url = "http://www." + url
						else:
							url = "http://" + url
					
					possibles.append({"body":link.text, "url":url})

#output: the selected node in possibles
#function: loops through possibles, selecting the first node that looks good
			#if we can't find any matches, list them all and ask the operator to make a choice.
			#this choice should be used to add to the 'keys' so we can make the same choice next time
def listPossibles():
	if len(possibles) == 1:
		return possibles[0]["url"]

	for item in possibles:
		for phrase in keys:
			if item["body"].lower().find(phrase) != -1:
				return item["url"]
	count = 0
	for item in possibles:
		print item["body"], " : ", count
		count += 1
		
	selection = input("Choose the correct roo... ")
	return possibles[selection]["url"]

#function: removes links from possibles that link to ignoreList items
def removeBogusLinks():
	count = 0
	for item in possibles:
		if ignoreList.count(item["url"]):
			del(possibles[count])
	count += 1

#main script. '-1' as input will run until it reaches the final node
good = False
while(good == False):
	count = input("How deep do you want to go? ")
	if type(count) == int:
		good = True
	else:
		print "Invalid Selection, try again."

#start a timer, grab the newest node and start digging
start = time.clock()
url = getNewestSubmission()
elapsed = time.clock() - start

if count == -1:
	count = 1
	while(url != end_node):
		print url, " Successfully linked! at node ", count, " running for ", elapsed
		url = openLink(url)
		count += 1
		elapsed = time.clock() - start
else:
	for i in range(0, count):
		print url, " Successfully linked!"
		url = openLink(url)
