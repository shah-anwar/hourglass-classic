class Queue(): #altered queue data structure, 'hybrid' - can be set as either a priority or non-priority queue on intialisation using priorityState flag
    def __init__(self, size, priorityState = False):
        self.main = [None] * int(size) #sets up empty array with size specified
        self.front = 0 #front pointer
        self.back = 0 #back pointer
        self.limit = size - 1 #limit of array index
        self.priorityState = priorityState #whether or not the queue is a priority queue
        if self.priorityState == True:
            self.priority = [None] * int(size) #sets up parallel empty array

    def peek(self): #returns front value without removal
        return self.main[self.front]

    def dequeue(self): #returns front value, removing it from the queue
        if self.isEmpty() == False:
            result = self.main[self.front]
            self.main[self.front] = None
            if self.priorityState == True: #removes from priority array if it is a priority queue
                self.priority[self.front] = None
            if self.front == self.back: #position of the pointers do not change if they are the same
                pass
            else:
                self.front += 1 #increments the pointer by one
            return result
        else:
            print("ERROR: Queue is empty")
            return None

    def enqueue(self, item, priorityVal = None):
        if self.isFull() == True: #shows error if the queue is already full
            print("ERROR: Queue is full")
        else:
            if self.priorityState == False: #code executed if it is a non-priority queue    
                self.main[self.back] = item
                self.back += 1
            else:
                if priorityVal == None:
                    print("ERROR: Priority unspecified")
                else:
                    if self.isEmpty() == True:
                        self.main[self.back] = item
                        self.priority[self.back] = priorityVal
                        self.back += 1
                    else:
                        last = False
                        for x in range(len(self.priority)): #iterates until the item reaches the end of the queue, or an item which has a priority less than it
                            if x == self.limit:
                                index = x
                                last = True
                                break
                            elif self.priority[x] == None:
                                pass
                            elif self.priority[x] > priorityVal:
                                index = x
                                break

                        if last == True: #as it is the last one, it is not required to change the positions of the values behind it
                            self.main[self.back] = item
                            self.priority[self.back] = priorityVal
                            self.back += 1
                        else:
                            currentItem = item
                            currentPriority = priorityVal
                            for y in range(index, self.limit + 1): #shifts all items of lesser priority down the queue
                                if currentItem == None:
                                    break
                                tempItem = self.main[y]
                                tempPriority = self.priority[y]
                                self.main[y] = currentItem
                                self.priority[y] = currentPriority
                                currentItem = tempItem
                                currentPriority = tempPriority
                            self.back += 1
    def getSize(self): #returns size of queue
        size = self.limit + 1
        for x in range(len(self.main)):
            if self.main[x] == None:
                size = size - 1
        return size

    def isEmpty(self): #returns whether or not a queue is empty
        if self.getSize() == 0:
            return True
        else:
            return False

    def isFull(self): #returns whether or not a queue is full
        if self.back == (self.limit + 1):
            return True
        else:
            return False

class LimitlessQueue(): #altered version of the classic queue, it doesn't have a limit and all items in the queue move foreward when dequeued (therefore not relying on a back or front pointer)
    def __init__(self, priorityState = None):
        self.main = []
        self.priorityState = None
        if self.priorityState == True:
            self.priority = []
    
    def peek(self): #returns front value without removal
        return self.main[0]

    def enqueue(self, item):
        self.main.append(item)
    
    def dequeue(self): #returns front value, removing it from the queue
        if self.isEmpty() == False: #nothing to pop is queue is empty
            print("ERROR: Queue is empty")
            return None
        else:
            result = self.main[0]
            self.main.pop(0)
            return result

    def getSize(self): #returns size of the queue
        return len(self.main)

    def isEmpty(self): #checks if the queue is empty or not (no need to check if full as it is limitless) {queue is limited to the python array limit; so not 'truly' limitless, but doesn't have a 'set' limit}
        if len(self.getsize()) == 0:
            return True
        else:
            return False

if __name__ == '__main__':
    print("This module must be run from within the file 'client.py'.")