Initial idea: to make a screenshare platform for youtube;
that is to say, that we wanted to make a website that accomplished two goals: share youtube videos, and chat

design for chatroom process:
1. utilize a chatroom that was hosted on a separate server (that was public), have two users on our website login and just use the public chatroom
2. utilize a private chatroom that is shared with the user you invite
3. incorporating the cli into a webpage
4. ended up choosing to host on a webpage and use a public chatroom (deadsimplechat)
5. tried to host on heroku, didn't work because it didn't support flask/sqlite
6. looked around, and settled on pythonanywhere, because it supported flask but was more support for mysql than sqlite, so ported to mysql

work:
1. tried implement a website from scratch - perhaps show some of that code?
2. tried to figure out how to use the chatroom, whether or not this would come out the way we wanted, whether or not we wanted to use certain things
3. hosting on heroku, then migrated to pythonanywhere
4.

Future iterations:
1. Make it so emails don't have to be sent to use this; can just invite through our website
2. control buffering
3. make the website more dynamic, with options such as drawing and chat room connected to microphone
4. 1 to 1 chatrooms, private chatrooms