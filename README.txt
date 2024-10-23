				INSTRUCTIONS:

1) Run server.py from the 'Server' folder and select a network device (loopback or LAN)
	Note: LAN connections will not work on systems with strict firewall protocols

2) Run two (or more) instances of client.py from the 'Client' folder, ensuring that each instance
has a unique IP address assigned to it

3) If this is your first time running the program, select option 'n' from the client login screen
to create a new account, else login to any existing account
	Note: Due to the nuances of using SQL and Threading simultaneously, in the event 
	the program hangs for an excess of a minute (the program timeout limit), force close
	the program (if not closed automatically) and retry
	
	Note ii: The above-mentioned error is often due to Python's limitations in computing
	the equations neccessary for encryption
	
	Note iii: Do not log into the same account on two instances. In the event this does occur, the 
	first instance will most probably become disconnected from the network (although Nodes that
	accessed the account's EndIP's will still be connected, until refresh via 'getinfo') 

4) On the client console, run 'getinfo {NodeID}' for each intance you would like to connect to (and save
the public keys for)

5) Once the above-mentioned command is run, you may run 'chat {NodeID}' or 'messenger {NodeID}' for 
each NodeID accessed using getinfo

6) For the Hourglass Messenger to run, both sides of the chat must complete the steps above.
	Note: After consultation with stakeholders, many prefer that the messenger should automatically
	open the application for the recipient after opening it on one side. However, this is a security flaw 
	as it releases needless metadata to the central server - something this project was designed to
	avoid.