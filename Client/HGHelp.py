def main(): #general help menu
    print("""
    Help Menu
    -=-=-=-=-

        Use any command, followed by "-h" or "--help" to bring up usage for the specified command

    Command             Purpose
    =======             =======
    chat/messenger      Start Messenger Application
    exit/quit           Exit the application
    getinfo             Add a user to your list of friends
    help                View the Help menu
    show                View stored data (i.e., Connected Users, Known Users), use 'show -h' for more details
    whoami              Return the name of the current user
    """)

def show(): #help menu for command: 'show'
    print("""
    Usage: show [option] {optional: target} 
    
    Option              Purpose
    ======              =======
    online              Show list of online users in known list
    known               Show list of known users
    """)

def messenger(): #help menu for comman: 'messenger'
    print("""
    Usage: messenger/chat [NodeID] 
    
    Option              Purpose
    ======              =======
    NodeID              Enter the NodeID of the user you wish to chat with
    """)

def getinfo():
    print("""
    Usage: getinfo [NodeID] 
    
    Option              Purpose
    ======              =======
    NodeID              Enter the NodeID of the user you wish to add
    """)

def messenger_main():
    print("""
    Help Menu
    -=-=-=-=-

        To use any command specified below, precede input with the '/' character

    Command             Purpose
    =======             =======
    exit/quit           Exit the messenger
    help                View the Help menu
    ping                Check whether or not the recipient is online
    whoami              Return the name of the current user
    """)

if __name__ == '__main__':
    print("This module must be run from within the file 'client.py'.")