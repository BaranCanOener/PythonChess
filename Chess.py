# -*- coding: utf-8 -*-
"""
Created on Sun Jul 21 12:36:30 2019

@author: Baran
Command line based chess engine
- Includes alphabeta pruning, quiescence searches and iterative deepening
- The integers used to evaluate positional strength of each piece type come from
   https://www.chessprogramming.org/Simplified_Evaluation_Function
"""

import time, random, subprocess
     
class Engine:
    
    #Worst-case valuation for white resp. black (and conversely, best-case valuation for the opponent)
    __whiteMin = -99999
    __blackMax = 99999
    
    #Control variables for iterative deepening search
    timeLimit = 5
    __startTime = time.time()
    __iterativeDeepening = True
    __abortSearch = False
    
    #If true, pseudorandom variations between -rand_limit and rand_limit will be applied by the evaluation function
    randomness = True 
    rand_limit = 30
    
    #The maximum depth for quiescence searches after the normal (=all moves) depth is reached
    quiescenceLimit = 2
    
    #Counts the visited positions
    nodes = 0
    
    #turnSequence[0] stores the best found move, currentTurnSequence stores the entire turn sequence that the engine currently looks at
    turnSequence = []
    currentTurnSequence = []
            
    #Evaluate positional strength of a given square according to piece-wise given scoreboards
    def evaluatePositioning(self, board, x, y):
        if board.squares[x][y] != None:
            if board.squares[x][y].colour  == Colour.White:
                return(board.squares[x][y].scoreBoard[7-y][x])
            else:
                return(board.squares[x][y].scoreBoard[y][x])
        else:
            return 0
    
    #Simple heuristic evaluation function of the entire board
    #Incorporates the material balance as well as positional strength
    def evaluatePositionAlphaBeta(self, board):
        val = 0
        for x in range(8):
            for y in range(8):
                if board.squares[x][y] != None:
                    if board.squares[x][y].colour == Colour.White:
                        val = val + board.squares[x][y].value + self.evaluatePositioning(board, x, y)
                    else:
                        val = val - board.squares[x][y].value - self.evaluatePositioning(board, x, y)
        if self.randomness:
            val = val + random.randint(-self.rand_limit, self.rand_limit)
        return val
    
    #Depth-limited Quiescence-Search to limit the Horizon effect:
    #Traverse only moves that result in a piece being taken,
    #after the alphabeta search across all potential moves up to a given depth is finished
    def quietSearch(self, board, colour, depth, maxDepth, alpha, beta):     
        self.updateSearchProgress(alpha, beta)
        value = self.evaluatePositionAlphaBeta(board)
        if depth == maxDepth:   
            return value
        if colour == Colour.White: #white maximizes  
            for x in range(8):
                for y in range(8):
                    if (board.squares[x][y] != None) and (board.squares[x][y].colour) == colour and (board.squares[x][y].getCaptureMoveList(x,y,board)!= None):
                        potentialMoves = [mov for mov in board.squares[x][y].moves]
                        for mov in potentialMoves:   
                            if (board.squares[mov[0]][mov[1]] != None) and (board.squares[mov[0]][mov[1]].colour == (not colour)):
                                self.nodes = self.nodes + 1 
                                move = board.move(x, y, mov[0], mov[1]) 
                                if (move.validMove):
                                    self.currentTurnSequence[depth] = [x, y, mov[0], mov[1]]
                                    if isinstance(move.pieceTaken,King):
                                        board.revertMove(move) 
                                        return self.__blackMax     
                                    value = max([value,self.quietSearch(board,not colour, depth + 1, maxDepth, alpha,beta)])
                                    board.revertMove(move)
                                    self.currentTurnSequence[depth] = []
                                    if value > alpha:
                                        alpha = value
                                        self.turnSequence[depth] = [x, y, mov[0], mov[1]]
                                    if alpha >= beta:
                                        return value        
        else:
            for x in range(8):
                for y in range(8):
                    if (board.squares[x][y] != None) and (board.squares[x][y].colour == colour) and (board.squares[x][y].getCaptureMoveList(x,y,board)!= None):
                        potentialMoves = [mov for mov in board.squares[x][y].moves]
                        for mov in potentialMoves:
                            if board.squares[mov[0]][mov[1]] != None and (board.squares[mov[0]][mov[1]].colour == (not colour)):
                                self.nodes = self.nodes + 1              
                                move = board.move(x, y, mov[0], mov[1]) 
                                if (move.validMove):
                                    self.currentTurnSequence[depth] = [x, y, mov[0], mov[1]]
                                    if isinstance(move.pieceTaken,King):
                                        board.revertMove(move)
                                        return self.__whiteMin
                                    value = min([value,self.quietSearch(board,not colour, depth + 1, maxDepth, alpha, beta)])
                                    board.revertMove(move)
                                    self.currentTurnSequence[depth] = []
                                    if value < beta:
                                        beta = value
                                        self.turnSequence[depth] = [x, y, mov[0], mov[1]]
                                    if alpha >= beta:
                                        return value
        return value 
    
    def alphaBeta(self, board, colour, depth, maxDepth, alpha, beta):
        if (depth == maxDepth) or (self.__abortSearch): 
            return self.quietSearch(board, colour, depth, maxDepth + self.quiescenceLimit, alpha, beta)
        if colour == Colour.White: #white maximizes
            value = self.__whiteMin
            for x in range(8):
                for y in range(8):
                    if (board.squares[x][y] != None) and board.squares[x][y].colour == colour:
                        board.squares[x][y].getMoveList(x,y, board)
                        potentialMoves = [mov for mov in board.squares[x][y].moves]
                        for mov in potentialMoves:
                            self.nodes = self.nodes + 1 
                            move = board.move(x, y, mov[0], mov[1])                            
                            if (move.validMove):
                                self.currentTurnSequence[depth] = [x, y, mov[0], mov[1]]   
                                if isinstance(move.pieceTaken,King):
                                    board.revertMove(move) 
                                    return self.__blackMax                           
                                value = max([value,self.alphaBeta(board, not colour, depth + 1, maxDepth, alpha, beta)])
                                if value > alpha:
                                    self.turnSequence[depth] = [x, y, mov[0], mov[1]]
                                    alpha = value                         
                                board.revertMove(move) 
                                self.currentTurnSequence[depth] = []
                                if alpha >= beta:
                                    return value
        else:
            value = self.__blackMax
            for x in range(8):
                for y in range(8):
                    if (board.squares[x][y] != None) and board.squares[x][y].colour == colour:
                        board.squares[x][y].getMoveList(x,y, board)
                        potentialMoves = [mov for mov in board.squares[x][y].moves]
                        for mov in potentialMoves:
                            self.nodes = self.nodes + 1 
                            move = board.move(x, y, mov[0], mov[1])                           
                            if (move.validMove):    
                                if isinstance(move.pieceTaken,King):
                                    board.revertMove(move) 
                                    return self.__whiteMin   
                                self.currentTurnSequence[depth] = [x, y, mov[0], mov[1]]
                                value = min([value,self.alphaBeta(board, not colour, depth + 1, maxDepth, alpha, beta)])
                                if value < beta:
                                    self.turnSequence[depth] = [x, y, mov[0], mov[1]]
                                    beta = value
                                board.revertMove(move)  
                                self.currentTurnSequence[depth] = []
                                if alpha >= beta:
                                    return value
        return value
    
    #Depth 0-part of the game tree search is handled in this routine:
    #The difference to the above alphaBeta-Routine is that the preferred move 
    #(passed as firstMove) is executed first.
    #The purpose is to make use of previous (lower maxDepth) search results of
    #iterative deepening, which should typically result in a lot of pruned moves
    def alphaBeta_depth0(self, board, colour, depth, maxDepth, alpha, beta, firstMove):
        if firstMove == None:
            return self.alphaBeta(board, colour, depth, maxDepth, alpha, beta)
        else:
            if colour == Colour.White: #white maximizes
                value = self.__whiteMin
                move = board.move(firstMove[0], firstMove[1], firstMove[2], firstMove[3])
                if (move.validMove):
                    self.currentTurnSequence[depth] = [firstMove[0], firstMove[1], firstMove[2], firstMove[3]]                           
                    value = max([value,self.alphaBeta(board, not colour, depth + 1, maxDepth, alpha, beta)])  
                    if value > alpha:
                        self.turnSequence[depth] = [firstMove[0], firstMove[1], firstMove[2], firstMove[3]]      
                        alpha = value
                    board.revertMove(move) 
                    self.currentTurnSequence[depth] = []
                for x in range(8):
                    for y in range(8):
                        if (board.squares[x][y] != None) and board.squares[x][y].colour == colour:
                            board.squares[x][y].getMoveList(x,y, board)
                            potentialMoves = [mov for mov in board.squares[x][y].moves]
                            for mov in potentialMoves:
                                if (mov == firstMove):
                                    continue
                                self.nodes = self.nodes + 1 
                                move = board.move(x, y, mov[0], mov[1])                            
                                if (move.validMove):
                                    self.currentTurnSequence[depth] = [x, y, mov[0], mov[1]]                           
                                    valueNew = max([value,self.alphaBeta(board, not colour, depth + 1, maxDepth, alpha, beta)])
                                    board.revertMove(move) 
                                    if self.__abortSearch: #partial results are discarded if the corresponding tree is not searched fully
                                        return value
                                    else:
                                        value = valueNew
                                    if value > alpha:
                                        self.turnSequence[depth] = [x, y, mov[0], mov[1]]
                                        alpha = value 
                                    
                                    self.currentTurnSequence[depth] = []
                                    if alpha >= beta:
                                        return value
            else:
                value = self.__blackMax
                move = board.move(firstMove[0], firstMove[1], firstMove[2], firstMove[3])
                if (move.validMove):
                    self.currentTurnSequence[depth] = [firstMove[0], firstMove[1], firstMove[2], firstMove[3]]                           
                    value = min([value,self.alphaBeta(board, not colour, depth + 1, maxDepth, alpha, beta)])
                    if value < beta:
                        self.turnSequence[depth] = [firstMove[0], firstMove[1], firstMove[2], firstMove[3]]      
                        beta = value 
                    board.revertMove(move) 
                    self.currentTurnSequence[depth] = []
                for x in range(8):
                    for y in range(8):
                        if (board.squares[x][y] != None) and board.squares[x][y].colour == colour:
                            board.squares[x][y].getMoveList(x,y, board)
                            potentialMoves = [mov for mov in board.squares[x][y].moves]
                            for mov in potentialMoves:
                                if (mov == firstMove):
                                    continue
                                self.nodes = self.nodes + 1 
                                move = board.move(x, y, mov[0], mov[1])                           
                                if (move.validMove):                       
                                    self.currentTurnSequence[depth] = [x, y, mov[0], mov[1]]
                                    valueNew = min([value,self.alphaBeta(board, not colour, depth + 1, maxDepth, alpha, beta)])
                                    board.revertMove(move) 
                                    if self.__abortSearch:
                                        return value
                                    else:
                                        value = valueNew
                                    if value < beta:
                                        self.turnSequence[depth] = [x, y, mov[0], mov[1]]
                                        beta = value   
                                    self.currentTurnSequence[depth] = []
                                    if alpha >= beta:
                                        return value
            return value

    def calculateMove_IterativeDeepening(self, board, colour, timeLimit):
        maxDepth = 0
        startingMove = None
        self.timeLimit = timeLimit
        self.__abortSearch = False
        self.__iterativeDeepening = True
        self.__startTime = time.time()
        self.nodes = 0
        board.allowIllegalMoves = True
        while not self.__abortSearch: #Continually increase depth while the time limit is not exceeded            
            maxDepth = maxDepth + 1
            self.turnSequence = [[-1,-1,-1,-1]]*(maxDepth + self.quiescenceLimit)
            self.currentTurnSequence = [[]]*(maxDepth+self.quiescenceLimit)
            val = self.alphaBeta_depth0(board,colour,0,maxDepth,self.__whiteMin,self.__blackMax, startingMove)         
            startingMove = self.turnSequence[0]
        board.allowIllegalMoves = False
        print("\n"+" -Best Valuation @Depth "+str(maxDepth)+" : "+ str(val))
        if startingMove == [-1,-1,-1,-1]: 
            print(" -Checkmate within "+str(maxDepth)+" turns.")
            startingMove = board.generateMoveList(colour)[0]
        return startingMove
    
    def calculateMove_FixedDepth(self, board, colour, maxDepth):
        self.__abortSearch = False
        self.__iterativeDeepening = False
        self.nodes = 0
        self.turnSequence = [[-1,-1,-1,-1]]*(maxDepth + self.quiescenceLimit)
        self.currentTurnSequence = [[]]*(maxDepth+self.quiescenceLimit)
        board.allowIllegalMoves = True
        val = self.alphaBeta(board,colour,0,maxDepth,self.__whiteMin,self.__blackMax)
        board.allowIllegalMoves = False
        print("\n"+" -Best Valuation @Depth "+str(maxDepth)+" : "+ str(val))
        if self.turnSequence[0] == [-1,-1,-1,-1]: 
            print(" -Checkmate within "+str(maxDepth)+" turns.")
            self.turnSequence[0] = self.currentTurnSequence[0]
        return self.turnSequence[0]
    
    #Method used to print the current search progress,
    #and to abort the search if the prescribed time limit is exceeded
    def updateSearchProgress(self, alpha, beta):
        if self.nodes % 100 == 0:
            s = ''
            i = 0
            for move in self.currentTurnSequence:
                if (move != []) and (move != [-1,-1,-1,-1]):
                    s = s + ChessGame.numToLetter(self, move[0])+str(move[1] + 1)+ChessGame.numToLetter(self, move[2])+str(move[3] + 1)
                    if (len(self.currentTurnSequence) - i <= self.quiescenceLimit + 1):
                        s = s + "="
                    else:
                        s = s + "-"
                else:
                    s = s + "none=" 
                i = i + 1
            if (self.__iterativeDeepening):
                time_diff = time.time() - self.__startTime
                if (time_diff > self.timeLimit):
                    time_diff = self.timeLimit
                    self.__abortSearch = True    
                print("\r"+" -CALC.. t-" + "%.1f"%round(self.timeLimit - time_diff,1)+
                      "sec, d="+str(len(self.currentTurnSequence)-self.quiescenceLimit)+"+"+
                      str(self.quiescenceLimit)+", n="+str(self.nodes)+", seq=["+s[:-1]+"]",end='')
            else:
                print('\r'+' -CALC.. n='+str(self.nodes) + ", seq=["+s[:-1]+"]",end='')
    
class ChessBoard:
    
    squares = None #an 8x8 list containing Piece-instances (resp. inherited class instances)
    kingWhiteLocation = [4,0] #Keep Track of the King's location for more efficient checks
    kingBlackLocation = [4,7]
    enPassantPawn = [-1,-1] #stores the coordinate of a pawn allowing for an en passant capture
    allowIllegalMoves = False #The engine is allowed to
    
    def resetBoard(self):
        self.squares = []
        for x in range(8):
            self.squares.append([])
            for y in range(8):
                self.squares[x].append([])
                if y == 1:
                    self.squares[x][y] = Pawn(Colour.White)
                elif y == 6:
                    self.squares[x][y] = Pawn(Colour.Black)
                elif (y > 1) and (y < 6):
                    self.squares[x][y] = None
                elif (y == 0) or (y == 7):
                    if y == 0:
                        colour = Colour.White
                    else:
                        colour = Colour.Black
                    if x == 0:
                       self.squares[x][y] = Rook(colour)
                    elif x == 1:
                       self.squares[x][y] = Knight(colour)
                    elif x == 2:
                       self.squares[x][y] = Bishop(colour)
                    elif x == 3:
                       self.squares[x][y] = Queen(colour)
                    elif x == 4:
                       self.squares[x][y] = King(colour)
                    elif x == 5:
                       self.squares[x][y] = Bishop(colour)
                    elif x == 6:
                       self.squares[x][y] = Knight(colour)
                    elif x == 7:
                       self.squares[x][y] = Rook(colour)
        self.kingWhiteLocation = [4,0] #Keep Track of the King's location for efficient Check-Checks
        self.kingBlackLocation = [4,7]
        self.whiteKingMoved = False
        self.blackKingMoved = False
        self.whiteLRookMoved = False
        self.blackLRookMoved = False
        self.whiteRRookMoved = False
        self.blackRRookMoved = False
                       
    def _resetToDebugBoard(self):
        self.resetBoard()
        for x in range(8):
            for y in range(8):
                self.squares[x][y] = None
        self.squares[0][0] = Rook(Colour.Black)
        self.squares[1][1] = Pawn(Colour.Black)
        self.squares[3][1] = Rook(Colour.White)
        self.squares[3][5] = Pawn(Colour.Black)
        self.squares[4][4] = Bishop(Colour.Black)
        self.squares[4][4] = Bishop(Colour.Black)
        self.squares[5][1] = Pawn(Colour.White)
        self.squares[6][1] = King(Colour.White)
        self.squares[6][7] = King(Colour.Black)
        
        self.kingWhiteLocation = [6,1]
        self.kingBlackLocation = [6,7]
        
    def printBoard_NoColour(self, moveset, move):
        moveAdj = ' '
        print(" ________________________________")
        print("|                               |")
        print("|    a  b  c  d  e  f  g  h     |")
        for y in range(7,-1,-1):
            print("| "+str(y + 1)+"  ",end="")
            for x in range(8):
                if moveset != None:
                    if [x,y] in moveset:
                        moveAdj = "*"
                    else:
                        moveAdj = " "
                else:
                    if (move != None) and (move.dest[0] == x and move.dest[1] == y):
                        moveAdj = "<" #highlight destination of moved piece
                    else:
                        moveAdj = " "
                if (self.squares[x][y] == None):
                    if (move != None) and (move.orig[0] == x and move.orig[1] == y): #print "shadow" of the last moved piece
                        print(move.pieceMoved.symbol+"> ",end="")
                    else:
                        print(moveAdj+"  "+"",end="")
                else:
                    if self.squares[x][y].colour == Colour.White:
                        print(self.squares[x][y].symbol+"w"+moveAdj,end="")
                    else:
                        print(self.squares[x][y].symbol+"b"+moveAdj,end="")
            print(" "+str(y + 1)+" |")
        print("|    a  b  c  d  e  f  g  h     |")
        print("|_______________________________|")
        
    def printBoard(self, moveset, move):
        moveAdj = ' '
        colWhite = "\x1b[0;37;40m"
        colBlack = "\x1b[0;33;40m"
        subprocess.call("", shell = True)
        print("\x1b[5;30;47m    a b c d e f g h    "+"\x1b[0m")
        for y in range(7,-1,-1):
            print("\x1b[5;30;47m"+" "+str(y + 1)+" \x1b[0;36;40m"+" ",end="")
            for x in range(8):
                moveAdj = " "
                if moveset != None:
                    if [x,y] in moveset:
                        moveAdj = "\x1b[0;37;40m"+"*"
                            
                if (self.squares[x][y] == None):
                    if (move != None) and (move.orig[0] == x and move.orig[1] == y): #print "shadow" of the last moved piece
                        if move.pieceMoved.colour == Colour.White:
                            print(colWhite+"_<"+"\x1b[0m",end="")
                        else:
                            print(colBlack+"_<"+"\x1b[0m",end="")
                    else:
                        print("\x1b[0;36;40m"+moveAdj+" "+"\x1b[0m",end="")
                else:
                    if self.squares[x][y].colour == Colour.White:
                        col = colWhite
                    else:
                        col = colBlack
                    if (move != None):
                        if (move.dest[0] == x and move.dest[1] == y):
                            moveAdj = "<" #highlight destination of moved piece
                            col = "\x1b[0;36;40m"
                        else:
                            moveAdj = " "
                    print(col+self.squares[x][y].symbol+moveAdj+"\x1b[0m",end="")
            print("\x1b[5;30;47m "+str(y + 1)+" \x1b[0m")
        print("\x1b[5;30;47m"+"    a b c d e f g h    \x1b[0m")
        
    #Returns True if colour is in check
    def isColourCheck(self, colour):

        for x in range(8):
            for y in range(8):
                if self.squares[x][y] != None:
                    if (self.squares[x][y].colour != colour) and (self.squares[x][y].getCaptureMoveList(x,y, self) != None):
                        for mov in self.squares[x][y].moves:
                            if (self.kingBlackLocation == mov) and (colour == Colour.Black):
                                return True
                           
                            if self.kingWhiteLocation == mov and (colour == Colour.White):
                                return True
                          
        return False
    
    #Get all moves of colour
    def generateMoveList(self, colour):
        moves = []
        for x in range(8):
            for y in range(8):
                if self.squares[x][y] != None:
                    if (self.squares[x][y].colour == colour):
                        self.squares[x][y].getMoveList(x, y, self)
                        for mov in self.squares[x][y].moves:
                            mov_ =self.move(x,y, mov[0], mov[1])
                            if mov_.validMove == True:
                                moves.append([x,y, mov[0], mov[1]])
                                self.revertMove(mov_)
        return moves
    
    #Undo the given move, assuming that the current board state resulted from the passed argument move
    def revertMove(self, move):        
        if move.isWhiteLRookCastling:
            self.squares[3][0].timesMoved = 0
            self.squares[2][0].timesMoved = 0
            self.squares[4][0] = self.squares[2][0]
            self.kingWhiteLocation = [4, 0]
            self.squares[0][0] = self.squares[3][0]
            self.squares[3][0] = None
            self.squares[2][0] = None
        elif move.isWhiteRRookCastling:
            self.squares[6][0].timesMoved = 0
            self.squares[5][0].timesMoved = 0
            self.squares[4][0] = self.squares[6][0]
            self.kingWhiteLocation = [4, 0]
            self.squares[7][0] = self.squares[5][0]
            self.squares[6][0] = None
            self.squares[5][0] = None
        elif move.isBlackLRookCastling:
            self.squares[2][7].timesMoved = 0
            self.squares[3][7].timesMoved = 0
            self.squares[4][7] = self.squares[2][7]
            self.kingBlackLocation = [4, 7]
            self.squares[0][7] = self.squares[3][7]
            self.squares[3][7] = None
            self.squares[2][7] = None   
        elif move.isBlackRRookCastling:
            self.squares[6][7].timesMoved = 0
            self.squares[5][7].timesMoved = 0
            self.squares[4][7] = self.squares[6][7]
            self.kingBlackLocation = [4, 7]
            self.squares[7][7] = self.squares[5][7]
            self.squares[6][7] = None
            self.squares[5][7] = None
        elif move.isEnPassant:
            if (move.orig[0] - move.dest[0] == 1):
                self.squares[move.orig[0] - 1][move.orig[1]] = move.pieceTaken
                self.squares[move.orig[0]][move.orig[1]] = move.pieceMoved
                self.squares[move.orig[0] - 1][move.dest[1]] = None
            if (move.dest[0] - move.orig[0] == 1):
                self.squares[move.orig[0] + 1][move.orig[1]] = move.pieceTaken
                self.squares[move.orig[0]][move.orig[1]] = move.pieceMoved
                self.squares[move.orig[0] + 1][move.dest[1]] = None
            move.pieceMoved.timesMoved = move.pieceMoved.timesMoved - 1
        else: #routine holds for ordinary moves and pawn promotions
            self.squares[move.orig[0]][move.orig[1]] = move.pieceMoved
            self.squares[move.dest[0]][move.dest[1]] = move.pieceTaken
            #update king location, if king is moved
            if move.pieceMoved.colour == Colour.White and isinstance(move.pieceMoved, King):
                self.kingWhiteLocation = [move.orig[0], move.orig[1]]
            if move.pieceMoved.colour == Colour.Black and isinstance(move.pieceMoved, King):
                self.kingBlackLocation = [move.orig[0], move.orig[1]]
            move.pieceMoved.timesMoved = move.pieceMoved.timesMoved - 1
        self.enPassantPawn = move.prevEnPassantPawn
    
    
    #returns true if x,y is attacked by any piece of the specified colour
    def isAttackedBy(self, xOrig, yOrig, colour):
        for x in range(8):
            for y in range(8):
                if self.squares[x][y] != None:
                    if (self.squares[x][y].colour == colour):
                        self.squares[x][y].getCaptureMoveList(x, y, self)
                        for mov in self.squares[x][y].moves:
                            if [mov[0],mov[1]] == [xOrig,yOrig]:
                                return True
        return False
    
    #Returns the move-class and performs the move if it is legal (and execute=True)
    def move(self, xOrig, yOrig, xDest, yDest):
        move = MoveData()
        move.orig = [xOrig, yOrig]
        move.dest = [xDest, yDest]
        move.pieceMoved = self.squares[xOrig][yOrig]
        move.pieceTaken = self.squares[xDest][yDest]
        
        if move.pieceMoved == None:
            return move
        if (not self.allowIllegalMoves):
            if not [xDest, yDest] in move.pieceMoved.getMoveList(xOrig, yOrig, self):
                return move 
        #Castling logic
        if isinstance(move.pieceMoved, King):
            if ([xOrig,yOrig] == [4, 0]) and ([xDest,yDest] == [2,0]): #Attempted white queenside castling
                if ((isinstance(self.squares[0][0], Rook) and (self.squares[0][0].colour == Colour.White) and (self.squares[0][0].timesMoved == 0) and 
                    (not self.isAttackedBy(3,0, Colour.Black)) and (not self.isAttackedBy(2,0,Colour.Black))) and (move.pieceMoved.timesMoved == 0) and 
                    not self.isColourCheck(Colour.White)): #check if legal castling          
                    self.squares[3][0] = self.squares[0][0] 
                    self.squares[2][0] = self.squares[4][0]
                    self.squares[4][0] = None
                    self.kingWhiteLocation = [2, 0]
                    self.squares[0][0] = None
                    self.squares[3][0].timesMoved = self.squares[3][0].timesMoved + 1
                    self.squares[2][0].timesMoved = self.squares[2][0].timesMoved + 1
                    move.isWhiteLRookCastling = True  
                    move.validMove = True
                return move
            if ([xOrig,yOrig] == [4, 0]) and ([xDest,yDest] == [6,0]): #attemted white kingside castling
                if ((isinstance(self.squares[7][0], Rook) and (self.squares[7][0].colour == Colour.White) and (self.squares[7][0].timesMoved == 0) and 
                    (not self.isAttackedBy(5,0, Colour.Black)) and (not self.isAttackedBy(6,0,Colour.Black))) and (move.pieceMoved.timesMoved == 0) and 
                    not self.isColourCheck(Colour.White)): #check if legal castling                                       
                    self.squares[5][0] = self.squares[7][0] 
                    self.squares[6][0] = self.squares[4][0]
                    self.squares[4][0] = None
                    self.kingWhiteLocation = [6, 0]
                    self.squares[7][0] = None
                    self.squares[5][0].timesMoved = self.squares[5][0].timesMoved + 1
                    self.squares[6][0].timesMoved = self.squares[6][0].timesMoved + 1
                    move.isWhiteRRookCastling = True  
                    move.validMove = True
                return move
            if ([xOrig,yOrig] == [4, 7]) and ([xDest,yDest] == [2,7]): #attempted black queenside castling
                if ((isinstance(self.squares[0][7], Rook) and (self.squares[0][7].colour == Colour.Black) and (self.squares[0][7].timesMoved == 0) and 
                    (not self.isAttackedBy(3,7, Colour.White)) and (not self.isAttackedBy(2,7,Colour.White))) and (move.pieceMoved.timesMoved == 0) and 
                    not self.isColourCheck(Colour.Black)): #check if legal castling                                                     
                    self.squares[3][7] = self.squares[0][7] 
                    self.squares[2][7] = self.squares[4][7]
                    self.squares[4][7] = None
                    self.kingBlackLocation = [2, 7]
                    self.squares[0][7] = None
                    self.squares[2][7].timesMoved = self.squares[2][7].timesMoved + 1
                    self.squares[3][7].timesMoved = self.squares[3][7].timesMoved + 1
                    move.isBlackLRookCastling = True  
                    move.validMove = True
                return move
            if ([xOrig,yOrig] == [4, 7]) and ([xDest,yDest] == [6,7]): #attempted black kingside castling
                if ((isinstance(self.squares[7][7], Rook) and (self.squares[7][7].colour == Colour.Black) and (self.squares[7][7].timesMoved == 0) and 
                    (not self.isAttackedBy(5,7, Colour.White)) and (not self.isAttackedBy(6,7,Colour.White))) and (move.pieceMoved.timesMoved == 0) and 
                    not self.isColourCheck(Colour.Black)): #check if legal castling                                       
                    self.squares[5][7] = self.squares[7][7] 
                    self.squares[6][7] = self.squares[4][7]
                    self.squares[4][7] = None
                    self.kingBlackLocation = [6, 7]
                    self.squares[7][7] = None
                    self.squares[6][7].timesMoved = self.squares[6][7].timesMoved + 1
                    self.squares[5][7].timesMoved = self.squares[5][7].timesMoved + 1
                    move.isBlackRRookCastling = True  
                    move.validMove = True   
                return move
            
        #update king location, if king is moved
        if [xOrig, yOrig] == self.kingWhiteLocation:
            self.kingWhiteLocation = [xDest, yDest]
        if ([xOrig, yOrig] == self.kingBlackLocation):
            self.kingBlackLocation = [xDest, yDest]
        
        #update board
        self.squares[xDest][yDest] = move.pieceMoved
        self.squares[xOrig][yOrig] = None
        
        #check whether player checks himself (i.e. invalid move)
        if (not self.allowIllegalMoves):
            if (self.isColourCheck(move.pieceMoved.colour) == True):
                if [xDest, yDest] == self.kingWhiteLocation: #Revert King location
                    self.kingWhiteLocation = [xOrig, yOrig]
                if [xDest, yDest] == self.kingBlackLocation:
                    self.kingBlackLocation = [xOrig, yOrig]
                self.squares[xDest][yDest] = move.pieceTaken #Revert move
                self.squares[xOrig][yOrig] = move.pieceMoved #Revert move
                move.validMove = False
                return move
        
        move.prevEnPassantPawn = self.enPassantPawn#preserve en passant of current board state, before move execution
        if isinstance(move.pieceMoved, Pawn):
            if (yDest == 7) and (move.pieceMoved.colour == Colour.White): #Pawn Promotion
                self.squares[xDest][yDest] = Queen(Colour.White)
                self.enPassantPawn = [-1,-1]
            if (yDest == 0) and (move.pieceMoved.colour == Colour.Black): #Pawn Promotion
                self.squares[xDest][yDest] = Queen(Colour.Black)
                self.enPassantPawn = [-1,-1]
            if (xOrig - xDest == 1) and (self.enPassantPawn == [xOrig-1,yOrig]) and (move.pieceMoved.colour == Colour.White):
                    move.isEnPassant = True #Move is an en passant capture
                    move.pieceTaken = self.squares[xDest][yDest - 1]
                    self.squares[xDest][yDest - 1] = None
                    self.enPassantPawn = [-1,-1]
            elif (xDest - xOrig == 1) and (self.enPassantPawn == [xOrig+1,yOrig]) and (move.pieceMoved.colour == Colour.White):
                    move.isEnPassant = True
                    move.pieceTaken = self.squares[xDest][yDest - 1]
                    self.squares[xDest][yDest - 1] = None
                    self.enPassantPawn = [-1,-1]
            elif (xOrig - xDest == 1) and (self.enPassantPawn == [xOrig-1,yOrig]) and (move.pieceMoved.colour == Colour.Black): #black left en passant executed
                    move.isEnPassant = True
                    move.pieceTaken = self.squares[xDest][yDest + 1]
                    self.squares[xDest][yDest + 1] = None
                    self.enPassantPawn = [-1,-1]
            elif (xDest - xOrig == 1) and (self.enPassantPawn == [xOrig+1,yOrig]) and (move.pieceMoved.colour == Colour.Black): #black right en passant executed
                    move.isEnPassant = True
                    move.pieceTaken = self.squares[xDest][yDest + 1]
                    self.squares[xDest][yDest + 1] = None
                    self.enPassantPawn = [-1,-1]
            elif (abs(yDest-yOrig) == 2): #Allow for en passant capture in the next turn
                self.enPassantPawn = [xDest,yDest]
            else:
                self.enPassantPawn = [-1,-1] #no en passant possible
        else:
            self.enPassantPawn = [-1,-1]
            
        #Keep track of times moved
        move.pieceMoved.timesMoved = move.pieceMoved.timesMoved + 1

        move.validMove = True
        return move        
        
    def __init__(self):
        self.resetBoard()

class MoveData:
    
    orig = [-1,-1]
    dest = [-1,-1]
    pieceMoved = None
    pieceTaken = None
    isWhiteLRookCastling = False
    isWhiteRRookCastling = False
    isBlackLRookCastling = False
    isBlackRRookCastling = False
    validMove = False
    prevEnPassantPawn = [-1,-1]#to remember whether an en passant was possible
    isEnPassant = False
    
class Colour:
    
    White = 0
    Black = 1   

class Piece:
    
    colour = None
    moves = None
    timesMoved = 0
    
    def __init__(self, colour):
        self.colour = colour
    
    #Returns a list of possible moves assuming the piece is at he (x,y) Position on the board
    #The board is passed in child classes to only generate moves within range of the piece (i.e. to avoid skipping for sliding pieces)
    #Legality of moves is handled by the board class itself
    def getMoveList(self, x, y, board):
        pass
    
    #Returns only captures and pawn steps (because of the potential of a pawn promotion)
    def getCaptureMoveList(self, x, y, board):
        pass
    
class Pawn(Piece):
    
    symbol = 'p'
    value = 100
    scoreBoard = [[ 0,  0,  0,  0,  0,  0,  0,  0],
                  [50, 50, 50, 50, 50, 50, 50, 50],
                  [10, 10, 20, 30, 30, 20, 10, 10],
                  [5,  5, 10, 25, 25, 10,  5,  5],
                  [0,  0,  0, 20, 20,  0,  0,  0],
                  [5, -5,-10,  0,  0,-10, -5,  5],
                  [5, 10, 10,-20,-20, 10, 10,  5],
                  [0,  0,  0,  0,  0,  0,  0,  0]]
    
    def getMoveList(self, x, y, board):
        self.moves = []
        if self.colour == Colour.White:
            if (y < 7):
                if (board.squares[x][y+1] == None):
                    self.moves.append([x,y+1])
            if y == 1:
                if (board.squares[x][y+2] == None) and (board.squares[x][y+1] == None):
                    self.moves.append([x,y+2])
            if (y < 7):
                if x > 0:
                    if (board.squares[x-1][y+1] != None):
                        if self.colour != board.squares[x-1][y+1].colour:
                            self.moves.append([x-1,y+1])
            if (y < 7):
                if x < 7:
                    if (board.squares[x+1][y+1] != None):
                        if self.colour != board.squares[x+1][y+1].colour:
                            self.moves.append([x+1,y+1])
                if (y == 4): #check if en passant is possible
                    if (x > 0) and (board.enPassantPawn == [x-1,y]) and (board.squares[x-1][y] != None) and (self.colour != board.squares[x-1][y].colour):
                        self.moves.append([x-1,y+1]) #white left en passant
                    if (x < 7) and (board.enPassantPawn == [x+1,y]) and (board.squares[x+1][y] != None) and (self.colour != board.squares[x+1][y].colour):
                        self.moves.append([x+1,y+1]) #white right en passant                      
        if self.colour == Colour.Black:
            if (y > 0):
                if (board.squares[x][y-1] == None):
                    self.moves.append([x,y-1])
            if y == 6:
                if (board.squares[x][y-2] == None) and (board.squares[x][y-1] == None):
                    self.moves.append([x, y-2])
            if (y > 0):
                if x > 0:
                    if (board.squares[x-1][y-1] != None):
                        if self.colour != board.squares[x-1][y-1].colour:
                            self.moves.append([x-1,y-1])
            if (y > 0):
                if x < 7:
                    if (board.squares[x+1][y-1] != None):
                        if self.colour != board.squares[x+1][y-1].colour:
                            self.moves.append([x+1,y-1])
                if (y == 3): #check if en passant is possible
                    if (x > 0) and (board.enPassantPawn == [x-1,y]) and (board.squares[x-1][y] != None) and (self.colour != board.squares[x-1][y].colour):
                        self.moves.append([x-1,y-1]) #black left en passant
                    if (x < 7) and (board.enPassantPawn == [x+1,y]) and (board.squares[x+1][y] != None) and (self.colour != board.squares[x+1][y].colour):
                        self.moves.append([x+1,y-1]) #black right en passant      
        return self.moves
        
        def getCaptureMoveList(self, x, y, board):
            self.moves = []
            if self.colour == Colour.White:
                if (y < 7):
                    if x > 0:
                        if (board.squares[x-1][y+1] != None):
                            if self.colour != board.squares[x-1][y+1].colour:
                                self.moves.append([x-1,y+1])
                if (y < 7):
                    if x < 7:
                        if (board.squares[x+1][y+1] != None):
                            if self.colour != board.squares[x+1][y+1].colour:
                                self.moves.append([x+1,y+1])
                    if (y == 4): #check if en passant is possible
                        if (x > 0) and (board.enPassantPawn == [x-1,y]) and (board.squares[x-1][y] != None) and (self.colour != board.squares[x-1][y].colour):
                            self.moves.append([x-1,y+1]) #white left en passant
                        if (x < 7) and (board.enPassantPawn == [x+1,y]) and (board.squares[x+1][y] != None) and (self.colour != board.squares[x+1][y].colour):
                            self.moves.append([x+1,y+1]) #white right en passant                      
            if self.colour == Colour.Black:
                if (y > 0):
                    if x > 0:
                        if (board.squares[x-1][y-1] != None):
                            if self.colour != board.squares[x-1][y-1].colour:
                                self.moves.append([x-1,y-1])
                if (y > 0):
                    if x < 7:
                        if (board.squares[x+1][y-1] != None):
                            if self.colour != board.squares[x+1][y-1].colour:
                                self.moves.append([x+1,y-1])
                    if (y == 3): #check if en passant is possible
                        if (x > 0) and (board.enPassantPawn == [x-1,y]) and (board.squares[x-1][y] != None) and (self.colour != board.squares[x-1][y].colour):
                            self.moves.append([x-1,y-1]) #black left en passant
                        if (x < 7) and (board.enPassantPawn == [x+1,y]) and (board.squares[x+1][y] != None) and (self.colour != board.squares[x+1][y].colour):
                            self.moves.append([x+1,y-1]) #black right en passant      
            return self.moves

class Knight(Piece):
    
    symbol = 'N'
    value = 300
    scoreBoard = [[-50,-40,-30,-30,-30,-30,-40,-50],
                  [-40,-20,  0,  0,  0,  0,-20,-40],
                  [-30,  0, 10, 15, 15, 10,  0,-30],
                  [-30,  5, 15, 20, 20, 15,  5,-30],
                  [-30,  0, 15, 20, 20, 15,  0,-30],
                  [-30,  5, 10, 15, 15, 10,  5,-30],
                  [-40,-20,  0,  5,  5,  0,-20,-40],
                  [-50,-40,-30,-30,-30,-30,-40,-50]]
    
    def getMoveList(self, x, y, board):
        self.moves = []
        if (x - 1 >= 0) and (y + 2 <= 7):
            if (board.squares[x-1][y+2] == None) or (self.colour != board.squares[x-1][y+2].colour):
                self.moves.append([x-1,y+2])
        if (x - 1 >= 0) and (y - 2 >= 0):
            if (board.squares[x-1][y-2] == None) or (self.colour != board.squares[x-1][y-2].colour):
                self.moves.append([x-1,y-2])
        if (x + 1 <= 7) and (y + 2 <= 7):
            if (board.squares[x+1][y+2] == None) or (self.colour != board.squares[x+1][y+2].colour):
                self.moves.append([x+1,y+2])
        if (x + 1 <= 7) and (y - 2 >= 0):
            if (board.squares[x+1][y-2] == None) or (self.colour != board.squares[x+1][y-2].colour):
                self.moves.append([x+1,y-2])
        if (x - 2 >= 0) and (y + 1 <= 7):
            if (board.squares[x-2][y+1] == None) or (self.colour != board.squares[x-2][y+1].colour):
                self.moves.append([x-2,y+1])
        if (x - 2 >= 0) and (y - 1 >= 0):
            if (board.squares[x-2][y-1] == None) or (self.colour != board.squares[x-2][y-1].colour):
                self.moves.append([x-2,y-1])
        if (x + 2 <= 7) and (y + 1 <= 7):
            if (board.squares[x+2][y+1] == None) or (self.colour != board.squares[x+2][y+1].colour):
                self.moves.append([x+2,y+1])
        if (x + 2 <= 7) and (y - 1 >= 0):
            if (board.squares[x+2][y-1] == None) or (self.colour != board.squares[x+2][y-1].colour):
                self.moves.append([x+2,y-1])
        return self.moves
    
    def getCaptureMoveList(self, x, y, board):
        self.moves = []
        if (x - 1 >= 0) and (y + 2 <= 7):
            if (board.squares[x-1][y+2] != None) and (self.colour != board.squares[x-1][y+2].colour):
                self.moves.append([x-1,y+2])
        if (x - 1 >= 0) and (y - 2 >= 0):
            if (board.squares[x-1][y-2] != None) and (self.colour != board.squares[x-1][y-2].colour):
                self.moves.append([x-1,y-2])
        if (x + 1 <= 7) and (y + 2 <= 7):
            if (board.squares[x+1][y+2] != None) and (self.colour != board.squares[x+1][y+2].colour):
                self.moves.append([x+1,y+2])
        if (x + 1 <= 7) and (y - 2 >= 0):
            if (board.squares[x+1][y-2] != None) and (self.colour != board.squares[x+1][y-2].colour):
                self.moves.append([x+1,y-2])
        if (x - 2 >= 0) and (y + 1 <= 7):
            if (board.squares[x-2][y+1] != None) and (self.colour != board.squares[x-2][y+1].colour):
                self.moves.append([x-2,y+1])
        if (x - 2 >= 0) and (y - 1 >= 0):
            if (board.squares[x-2][y-1] != None) and (self.colour != board.squares[x-2][y-1].colour):
                self.moves.append([x-2,y-1])
        if (x + 2 <= 7) and (y + 1 <= 7):
            if (board.squares[x+2][y+1] != None) and (self.colour != board.squares[x+2][y+1].colour):
                self.moves.append([x+2,y+1])
        if (x + 2 <= 7) and (y - 1 >= 0):
            if (board.squares[x+2][y-1] != None) and (self.colour != board.squares[x+2][y-1].colour):
                self.moves.append([x+2,y-1])
        return self.moves
    
class Rook(Piece):
    
    symbol = 'R'
    value = 500
    scoreBoard = [[ 0, 0, 0, 0, 0, 0, 0, 0],
                  [ 5,10,10,10,10,10,10, 5],
                  [-5, 0, 0, 0, 0, 0, 0,-5],
                  [-5, 0, 0, 0, 0, 0, 0,-5],
                  [-5, 0, 0, 0, 0, 0, 0,-5],
                  [-5, 0, 0, 0, 0, 0, 0,-5],
                  [-5, 0, 0, 0, 0, 0, 0,-5],
                  [ 0, 0, 0, 5, 5, 0, 0, 0]]
                  
    def getMoveList(self, x, y, board):
        self.moves = []
        i = 1
        while (x-i >= 0) and board.squares[x-i][y] == None:
            self.moves.append([x-i,y])
            i = i + 1
        if (x-i >= 0) and (board.squares[x-i][y].colour != self.colour):
            self.moves.append([x-i,y])          
        i = 1
        while (x+i <= 7) and board.squares[x+i][y] == None:
            self.moves.append([x+i,y])
            i = i + 1
        if (x+i <= 7) and (board.squares[x+i][y].colour != self.colour):
            self.moves.append([x+i,y])          
        i = 1
        while (y+i <= 7) and board.squares[x][y+i] == None:
            self.moves.append([x,y+i])
            i = i + 1
        if (y+i <= 7) and (board.squares[x][y+i].colour != self.colour):
            self.moves.append([x,y+i]) 
        i = 1
        while (y-i >= 0) and board.squares[x][y-i] == None:
            self.moves.append([x,y-i])
            i = i + 1
        if (y-i >= 0) and (board.squares[x][y-i].colour != self.colour):
            self.moves.append([x,y-i])           
        return self.moves
    
    def getCaptureMoveList(self, x, y, board):
        self.moves = []
        i = 1
        while (x-i >= 0) and board.squares[x-i][y] == None:
            i = i + 1
        if (x-i >= 0) and (board.squares[x-i][y].colour != self.colour):
            self.moves.append([x-i,y])          
        i = 1
        while (x+i <= 7) and board.squares[x+i][y] == None:
            i = i + 1
        if (x+i <= 7) and (board.squares[x+i][y].colour != self.colour):
            self.moves.append([x+i,y])          
        i = 1
        while (y+i <= 7) and board.squares[x][y+i] == None:
            i = i + 1
        if (y+i <= 7) and (board.squares[x][y+i].colour != self.colour):
            self.moves.append([x,y+i]) 
        i = 1
        while (y-i >= 0) and board.squares[x][y-i] == None:
            i = i + 1
        if (y-i >= 0) and (board.squares[x][y-i].colour != self.colour):
            self.moves.append([x,y-i])           
        return self.moves

class Bishop(Piece):
    
    symbol = 'B'
    value = 300
    scoreBoard = [[-20,-10,-10,-10,-10,-10,-10,-20],
                  [-10,  0,  0,  0,  0,  0,  0,-10],
                  [-10,  0,  5, 10, 10,  5,  0,-10],
                  [-10,  5,  5, 10, 10,  5,  5,-10],
                  [-10,  0, 10, 10, 10, 10,  0,-10],
                  [-10, 10, 10, 10, 10, 10, 10,-10],
                  [-10,  5,  0,  0,  0,  0,  5,-10],
                  [-20,-10,-10,-10,-10,-10,-10,-20]]
    
    def getMoveList(self, x, y, board):
        self.moves = []
        i = 1
        while (x-i >= 0) and (y+i <= 7) and board.squares[x-i][y+i] == None:
            self.moves.append([x-i, y+i])
            i = i + 1
        if ((x-i >= 0) and (y+i <= 7)) and board.squares[x-i][y+i].colour != self.colour:
            self.moves.append([x-i,y+i])          
        i = 1
        while (x-i >= 0) and (y-i >= 0) and board.squares[x-i][y-i] == None:
            self.moves.append([x-i,y-i])
            i = i + 1
        if ((x-i >= 0) and (y-i >= 0)) and board.squares[x-i][y-i].colour != self.colour:
            self.moves.append([x-i,y-i])         
        i = 1
        while (x+i <= 7) and (y-i >= 0) and board.squares[x+i][y-i] == None:
            self.moves.append([x+i,y-i])
            i = i + 1    
        if ((x+i <= 7) and (y-i >= 0)) and board.squares[x+i][y-i].colour != self.colour:
            self.moves.append([x+i,y-i])          
        i = 1
        while (x+i <= 7) and (y+i <= 7) and board.squares[x+i][y+i] == None:
            self.moves.append([x+i,y+i])
            i = i + 1     
        if ((x+i <= 7) and (y+i <= 7)) and board.squares[x+i][y+i].colour != self.colour:
            self.moves.append([x+i,y+i])
        return self.moves
    
    def getCaptureMoveList(self, x, y, board):
        self.moves = []
        i = 1
        while (x-i >= 0) and (y+i <= 7) and board.squares[x-i][y+i] == None:
            i = i + 1
        if ((x-i >= 0) and (y+i <= 7)) and board.squares[x-i][y+i].colour != self.colour:
            self.moves.append([x-i,y+i])          
        i = 1
        while (x-i >= 0) and (y-i >= 0) and board.squares[x-i][y-i] == None:
            i = i + 1
        if ((x-i >= 0) and (y-i >= 0)) and board.squares[x-i][y-i].colour != self.colour:
            self.moves.append([x-i,y-i])         
        i = 1
        while (x+i <= 7) and (y-i >= 0) and board.squares[x+i][y-i] == None:
            i = i + 1    
        if ((x+i <= 7) and (y-i >= 0)) and board.squares[x+i][y-i].colour != self.colour:
            self.moves.append([x+i,y-i])          
        i = 1
        while (x+i <= 7) and (y+i <= 7) and board.squares[x+i][y+i] == None:
            i = i + 1     
        if ((x+i <= 7) and (y+i <= 7)) and board.squares[x+i][y+i].colour != self.colour:
            self.moves.append([x+i,y+i])
        return self.moves
    
class Queen(Piece):
    
    symbol = 'Q'
    value = 900
    scoreBoard = [[-20,-10,-10, -5, -5,-10,-10,-20],
                  [-10,  0,  0,  0,  0,  0,  0,-10],
                  [-10,  0,  5,  5,  5,  5,  0,-10],
                  [-5,  0,  5,  5,  5,  5,  0, -5],
                  [0,  0,  5,  5,  5,  5,  0, -5],
                  [-10,  5,  5,  5,  5,  5,  0,-10],
                  [-10,  0,  5,  0,  0,  0,  0,-10],
                  [-20,-10,-10, -5, -5,-10,-10,-20]]
    
    def getMoveList(self, x, y, board):
        self.moves = []     
        i = 1
        while (x-i >= 0) and (y+i <= 7) and board.squares[x-i][y+i] == None:
            self.moves.append([x-i, y+i])
            i = i + 1
        if ((x-i >= 0) and (y+i <= 7)) and board.squares[x-i][y+i].colour != self.colour:
            self.moves.append([x-i,y+i])        
        i = 1
        while (x-i >= 0) and (y-i >= 0) and board.squares[x-i][y-i] == None:
            self.moves.append([x-i,y-i])
            i = i + 1
        if ((x-i >= 0) and (y-i >= 0)) and board.squares[x-i][y-i].colour != self.colour:
            self.moves.append([x-i,y-i])
        i = 1
        while (x+i <= 7) and (y-i >= 0) and board.squares[x+i][y-i] == None:
            self.moves.append([x+i,y-i])
            i = i + 1    
        if ((x+i <= 7) and (y-i >= 0)) and board.squares[x+i][y-i].colour != self.colour:
            self.moves.append([x+i,y-i])
        i = 1
        while (x+i <= 7) and (y+i <= 7) and board.squares[x+i][y+i] == None:
            self.moves.append([x+i,y+i])
            i = i + 1     
        if ((x+i <= 7) and (y+i <= 7)) and board.squares[x+i][y+i].colour != self.colour:
            self.moves.append([x+i,y+i])          
        i = 1
        while (x-i >= 0) and board.squares[x-i][y] == None:
            self.moves.append([x-i,y])
            i = i + 1
        if (x-i >= 0) and (board.squares[x-i][y].colour != self.colour):
            self.moves.append([x-i,y])         
        i = 1
        while (x+i <= 7) and board.squares[x+i][y] == None:
            self.moves.append([x+i,y])
            i = i + 1
        if (x+i <= 7) and (board.squares[x+i][y].colour != self.colour):
            self.moves.append([x+i,y])    
        i = 1
        while (y+i <= 7) and board.squares[x][y+i] == None:
            self.moves.append([x,y+i])
            i = i + 1
        if (y+i <= 7) and (board.squares[x][y+i].colour != self.colour):
            self.moves.append([x,y+i])
        i = 1
        while (y-i >= 0) and board.squares[x][y-i] == None:
            self.moves.append([x,y-i])
            i = i + 1
        if (y-i >= 0) and (board.squares[x][y-i].colour != self.colour):
            self.moves.append([x,y-i])    
        return self.moves    
    
    def getCaptureMoveList(self, x, y, board):
        self.moves = []     
        i = 1
        while (x-i >= 0) and (y+i <= 7) and board.squares[x-i][y+i] == None:
            i = i + 1
        if ((x-i >= 0) and (y+i <= 7)) and board.squares[x-i][y+i].colour != self.colour:
            self.moves.append([x-i,y+i])        
        i = 1
        while (x-i >= 0) and (y-i >= 0) and board.squares[x-i][y-i] == None:
            i = i + 1
        if ((x-i >= 0) and (y-i >= 0)) and board.squares[x-i][y-i].colour != self.colour:
            self.moves.append([x-i,y-i])
        i = 1
        while (x+i <= 7) and (y-i >= 0) and board.squares[x+i][y-i] == None:
            i = i + 1    
        if ((x+i <= 7) and (y-i >= 0)) and board.squares[x+i][y-i].colour != self.colour:
            self.moves.append([x+i,y-i])
        i = 1
        while (x+i <= 7) and (y+i <= 7) and board.squares[x+i][y+i] == None:
            i = i + 1     
        if ((x+i <= 7) and (y+i <= 7)) and board.squares[x+i][y+i].colour != self.colour:
            self.moves.append([x+i,y+i])          
        i = 1
        while (x-i >= 0) and board.squares[x-i][y] == None:
            i = i + 1
        if (x-i >= 0) and (board.squares[x-i][y].colour != self.colour):
            self.moves.append([x-i,y])         
        i = 1
        while (x+i <= 7) and board.squares[x+i][y] == None:
            i = i + 1
        if (x+i <= 7) and (board.squares[x+i][y].colour != self.colour):
            self.moves.append([x+i,y])    
        i = 1
        while (y+i <= 7) and board.squares[x][y+i] == None:
            i = i + 1
        if (y+i <= 7) and (board.squares[x][y+i].colour != self.colour):
            self.moves.append([x,y+i])
        i = 1
        while (y-i >= 0) and board.squares[x][y-i] == None:
            i = i + 1
        if (y-i >= 0) and (board.squares[x][y-i].colour != self.colour):
            self.moves.append([x,y-i])    
        return self.moves    
              
class King(Piece):
    
    symbol = 'K'
    value = 30000 #not representative in Endgame
    scoreBoard = [[-30,-40,-40,-50,-50,-40,-40,-30],
                  [-30,-40,-40,-50,-50,-40,-40,-30],
                  [-30,-40,-40,-50,-50,-40,-40,-30],
                  [-30,-40,-40,-50,-50,-40,-40,-30],
                  [-20,-30,-30,-40,-40,-30,-30,-20],
                  [-10,-20,-20,-20,-20,-20,-20,-10],
                  [20, 20,  0,  0,  0,  0, 20, 20],
                  [20, 30, 10,  0,  0, 10, 30, 20]]
    
    def getMoveList(self, x, y, board):
        self.moves = []
        if (x-1 >= 0) and (y+1 <= 7):
            if (board.squares[x-1][y+1] == None) or (self.colour != board.squares[x-1][y+1].colour):
                self.moves.append([x-1, y+1])
        if (x-1 >= 0) and (y-1 >= 0):
            if (board.squares[x-1][y-1] == None) or (self.colour != board.squares[x-1][y-1].colour):
                self.moves.append([x-1,y-1])
        if (x+1 <= 7) and (y-1 >= 0):
            if (board.squares[x+1][y-1] == None) or (self.colour != board.squares[x+1][y-1].colour):
                self.moves.append([x+1,y-1])
        if (x+1 <= 7) and (y+1 <= 7):
            if (board.squares[x+1][y+1] == None) or (self.colour != board.squares[x+1][y+1].colour):
                self.moves.append([x+1,y+1])
        if (x+1 <= 7):
            if (board.squares[x+1][y] == None) or (self.colour != board.squares[x+1][y].colour):
                self.moves.append([x+1,y])   
        if (x-1 >= 0) :
            if (board.squares[x-1][y] == None) or (self.colour != board.squares[x-1][y].colour):
                self.moves.append([x-1, y])
        if (y+1 <= 7):
            if (board.squares[x][y+1] == None) or (self.colour != board.squares[x][y+1].colour):
                self.moves.append([x, y+1])
        if (y-1 >= 0):
            if (board.squares[x][y-1] == None) or (self.colour != board.squares[x][y-1].colour):
                self.moves.append([x,y-1])
        if (x == 4) and (y == 0) and (board.squares[3][y] == None) and (board.squares[2][y] == None) and (board.squares[1][y] == None):
                self.moves.append([x-2,y])
        if (x == 4) and (y == 0) and (board.squares[5][y] == None) and (board.squares[6][y] == None):
                self.moves.append([x+2,y])
        if (x == 4) and (y == 7) and (board.squares[5][y] == None) and (board.squares[6][y] == None):
                self.moves.append([x+2,y])
        if (x == 4) and (y == 7) and (board.squares[3][y] == None) and (board.squares[2][y] == None) and (board.squares[1][y] == None):
                self.moves.append([x-2,y])
        return self.moves   
    
    def getCaptureMoveList(self, x, y, board):
        self.moves = []
        if (x-1 >= 0) and (y+1 <= 7):
            if (board.squares[x-1][y+1] != None) and (self.colour != board.squares[x-1][y+1].colour):
                self.moves.append([x-1, y+1])
        if (x-1 >= 0) and (y-1 >= 0):
            if (board.squares[x-1][y-1] != None) and (self.colour != board.squares[x-1][y-1].colour):
                self.moves.append([x-1,y-1])
        if (x+1 <= 7) and (y-1 >= 0):
            if (board.squares[x+1][y-1] != None) and (self.colour != board.squares[x+1][y-1].colour):
                self.moves.append([x+1,y-1])
        if (x+1 <= 7) and (y+1 <= 7):
            if (board.squares[x+1][y+1] != None) and (self.colour != board.squares[x+1][y+1].colour):
                self.moves.append([x+1,y+1])
        if (x+1 <= 7):
            if (board.squares[x+1][y] != None) and (self.colour != board.squares[x+1][y].colour):
                self.moves.append([x+1,y])   
        if (x-1 >= 0) :
            if (board.squares[x-1][y] != None) and (self.colour != board.squares[x-1][y].colour):
                self.moves.append([x-1, y])
        if (y+1 <= 7):
            if (board.squares[x][y+1] != None) and (self.colour != board.squares[x][y+1].colour):
                self.moves.append([x, y+1])
        if (y-1 >= 0):
            if (board.squares[x][y-1] != None) and (self.colour != board.squares[x][y-1].colour):
                self.moves.append([x,y-1])
        return self.moves   
          
    
class ChessGame:
    
    board = None
    
    def numToLetter(self, coord):
        if coord == 0:
            return "a"
        elif coord == 1:
            return "b"
        elif coord == 2:
            return "c"
        elif coord == 3:
            return "d"
        elif coord == 4:
            return "e"
        elif coord == 5:
            return "f"
        elif coord == 6:
            return "g"
        elif coord == 7:
            return "h"
    
    def letterToNum(self, coord):
        if coord == "a":
            return 0
        elif coord == "b":
            return 1
        elif coord == "c":
            return 2
        elif coord == "d":
            return 3
        elif coord == "e":
            return 4
        elif coord == "f":
            return 5
        elif coord == "g":
            return 6
        elif coord == "h":
            return 7
        
    def debug(self):
        self.board._resetToDebugBoard()
        self.board.printBoard(None,None)
        
    def printHelp(self):
        print("Command List:")
        print("  'PQ XY' to move the piece on PQ to XY (e.g. e2 e4)")
        print("  'undo' to undo the last move")
        print("  'getmoves XY' to get all potential moves at XY")
        print("  'getallmoves' to get all potential moves")
        print("  'lastmove' to display the last move")
        print("  'reset_board' to fully reset the board")
        print("  'engine_depth d' to call engine move at depth d")
        print("  'engine_time t' to call engine move at max. allocated time t (seconds)")
        print("  'engine_loop w b n' to pit engines of max. alloc. time w and b against each other for n games")
        print("  'engine_quiescence x' to set quiescence limit to x (default: 2)")
        print("  'switch' to switch between coloured/black and white output (use if colour is not supported)")
        
    def getAllMoves(self, colour):
        moves = []
        for x in range(8):
            for y in range(8):
                if self.board.squares[x][y] != None and self.board.squares[x][y].colour == colour:
                    for mov in self.board.squares[x][y].getMoveList(x,y,self.board):
                        moves.append(mov)
        return moves
    
    def printBoard(self, moveset, move, printInColour):
        if printInColour:
            self.board.printBoard(moveset, move)
        else:
            self.board.printBoard_NoColour(moveset, move)
        
    def startGameLoop(self):
        self.board = ChessBoard()
        command = ''
        colour = Colour.White  
        engine = Engine()
        moveList = []
        move = MoveData()
        moveCounter = 0
        gameCounter = 0
        maxEngineGames = 10
        whiteWinCounter = 0
        blackWinCounter = 0
        time_white = 5
        time_black = 5
        printInColour = True
        self.printBoard(None,None,printInColour)
        self.printHelp()
        
        while command != "exit":    
            #Handles the detection of a check/checkmate an               
            if colour == Colour.White: 
                print("("+str(moveCounter)+")"+" White's turn.")
                if self.board.generateMoveList(Colour.White) == []:
                    print("White is checkmate after "+str(moveCounter)+" turns! See all potential moves of black:")
                    self.printBoard(self.getAllMoves(Colour.Black),None,printInColour)
                    blackWinCounter = blackWinCounter + 1
                    gameCounter = gameCounter + 1
                    print("Wins of white: " + str(whiteWinCounter) + ", wins of black: " + str(blackWinCounter))
                    print("Resetting board.")
                    self.board.resetBoard()
                    moveCounter = 0
                    colour = Colour.White
                    if (command == "engine_loop ") and (gameCounter == maxEngineGames):
                        print("Game cap of 10 reached.")
                        gameCounter = 0
                        whiteWinCounter = 0
                        blackWinCounter = 0
                        command = ""
                    self.printBoard(None,None,printInColour)
                elif self.board.isColourCheck(Colour.White):
                    print("White is checked!")       
            else:
                print("("+str(moveCounter)+")"+" Black's turn.")
                if self.board.generateMoveList(Colour.Black) == []:
                    print("Black is checkmate after "+str(moveCounter)+" turns! See all potential moves of white:")
                    self.printBoard(self.getAllMoves(Colour.White),None,printInColour)
                    whiteWinCounter = whiteWinCounter + 1
                    gameCounter = gameCounter + 1
                    print("Wins of white: " + str(whiteWinCounter) + ", wins of black: " + str(blackWinCounter))
                    print("Resetting board.")
                    self.board.resetBoard()
                    moveCounter = 0
                    colour = Colour.White
                    if (command == "engine_loop ") and (gameCounter == maxEngineGames):
                        print("Game cap of " + str(maxEngineGames) + " reached.")
                        gameCounter = 0
                        whiteWinCounter = 0
                        blackWinCounter = 0
                        command = ""
                    self.printBoard(None,None,printInColour)
                elif self.board.isColourCheck(Colour.Black):
                    print("Black is checked!")
                
 
            rnd = engine.randomness
            engine.randomness = False
            print("Heuristic Valuation       : " + str(engine.evaluatePositionAlphaBeta(self.board)))
            engine.randomness = rnd
            
            if command != "engine_loop ":
                command = input("> ")  
                
            if command == "exit":
                continue        
            elif command[:13] == "engine_depth ":
                maxDepth = [int(s) for s in command.split() if s.isdigit()][0]
                start_time = time.time()
                mov_ = engine.calculateMove_FixedDepth(self.board, colour, maxDepth)
                print(" -Total Nodes Searched    : " + str(engine.nodes))
                print(" -Time: " + str(round(time.time() - start_time,2)) + "s, " + str(int(engine.nodes / (time.time() - start_time + 0.001))) + "N/s")
                if move != [-1,-1,-1,-1]:
                    print("=> Engine Move: " + self.numToLetter(mov_[0] ) + str(mov_[1] + 1) + ' ' + self.numToLetter(mov_[2]) + str(mov_[3] + 1))       
                else:
                    print("Engine is checkmate, can't move.")
                print("")
                self.printBoard(None,None,printInColour)
            elif command[:12] == "engine_time ":
                timeLimit = [int(s) for s in command.split() if s.isdigit()][0]
                start_time = time.time()
                mov_ = engine.calculateMove_IterativeDeepening(self.board, colour, timeLimit)
                print(" -Total Nodes Searched    : " + str(engine.nodes))
                print(" -Time & Nodes per Second : " + str(round(time.time() - start_time,2)) + "s, " + str(int(engine.nodes / (time.time() - start_time + 0.001))) + "N/s")
                if mov_ != [-1,-1,-1,-1]:
                    print("=> Engine Move: " + self.numToLetter(mov_[0] ) + str(mov_[1] + 1) + ' ' + self.numToLetter(mov_[2]) + str(mov_[3] + 1))       
                else:
                    print("Engine is checkmate, can't move.")
                print("")
                self.printBoard(None,None,printInColour)
            elif command[:12] == "engine_loop ": #Have white AI depth 2 and black AI depth 3 battle each other
                start_time = time.time()
                if len(command) > 12:
                    time_white = [int(s) for s in command.split() if s.isdigit()][0]
                    time_black = [int(s) for s in command.split() if s.isdigit()][1]
                    try:
                        maxEngineGames = [int(s) for s in command.split() if s.isdigit()][2]
                    except:
                        maxEngineGames = 1
                    command = 'engine_loop '
                if (moveCounter == 200):
                    print("Move cap of 200 reached. Resetting game ..")
                    self.board.resetBoard()
                    colour = Colour.White
                    moveCounter = 0
                    self.printBoard(None,None,printInColour)
                    continue
                if colour == Colour.White:
                    mov_ = engine.calculateMove_IterativeDeepening(self.board, colour, time_white) 
                if colour == Colour.Black:
                    mov_ = engine.calculateMove_IterativeDeepening(self.board, colour, time_black)             
                move = self.board.move(mov_[0], mov_[1], mov_[2], mov_[3])
                colour = not colour
                moveCounter = moveCounter + 1
                print(" -Total Nodes Searched    : " + str(engine.nodes))
                print(" -Time & Nodes per Second : " + str(round(time.time() - start_time,2)) + "s, " + str(int(engine.nodes / (time.time() - start_time + 0.001))) + "N/s")
                if move.validMove:
                    print("=> Engine Move: " + self.numToLetter(mov_[0]) + str(mov_[1] + 1) + ' ' + self.numToLetter(mov_[2]) + str(mov_[3] + 1))   
                else:
                    print("Error - Engine can't move.")
                self.printBoard(None,move,printInColour)
            elif command[:18] == "engine_quiescence ":
                engine.quiescenceLimit = [int(s) for s in command.split() if s.isdigit()][0]
            elif command[:11] == "AI_setdepth":
                maxDepth = [int(s) for s in command.split() if s.isdigit()][0]
                continue
            elif command == "reset_board":
                self.board.resetBoard()
                colour = Colour.White
                moveCounter = 0
                self.printBoard(None,None,printInColour)
                continue
            elif (command == "undo"):
                if moveCounter == 0:
                    print('No move made yet!')
                    continue
                else:
                    self.board.revertMove(moveList[-1])
                    moveList.pop()
                    if moveList == []:
                        move = None
                    else:
                        move = moveList[-1]
                    colour = not colour
                    moveCounter = moveCounter - 1
                    self.printBoard(None,None,printInColour)
            elif (command == "lastmove"):
                self.printBoard(None,move,printInColour)
            elif (command[:8] == "getmoves"):
                try:
                    xOrig = self.letterToNum(command[9])
                    yOrig = int(command[10])-1
                    self.board.printBoard(self.board.squares[xOrig][yOrig].getMoveList(xOrig, yOrig, self.board),move)
                except:
                    print("Invalid Piece Chosen")
            elif (command == "getallmoves"):
                self.printBoard(self.getAllMoves(colour),None,printInColour)
            elif (command == "debug"):
                self.debug()
                colour=Colour.White
                self.printBoard(None, None,printInColour)
            elif (command == "switch"):
                printInColour = not printInColour
                self.printBoard(None, None,printInColour)
            else:
                try:
                    yOrig = int(command[1]) - 1
                    xOrig = self.letterToNum(command[0])
                    yDest = int(command[4]) - 1
                    xDest = self.letterToNum(command[3])
                except:
                    print("Invalid command")
                    self.printBoard(None,None,printInColour)
                    self.printHelp()
                    continue
                if self.board.squares[xOrig][yOrig] == None or self.board.squares[xOrig][yOrig].colour != colour:
                    print("Invalid Piece Chosen")
                else:
                    move = self.board.move(xOrig, yOrig, xDest, yDest)
                    if not move.validMove:
                        print("Invalid Move")
                    else: #valid move
                        moveList.append(move)
                        colour = not colour
                        moveCounter = moveCounter + 1
                        self.printBoard(None,None,printInColour)
        
game = ChessGame()
game.startGameLoop()