# PythonChess
*Description.* A chess game written in Python 3.7. Includes a simple engine supporting alpha-beta-pruning, iterative deepening and quiescence searches. 
ASCII-based output is handled on the Python terminal.

*Next steps.* The castling and en passant-routines could probably be shortened and/or made more efficient, along with other improvements to the codebase. As far as completely new features like transposition tables go, I will probably reserve them for a translation to C++.

Command List:
* 'PQ XY' moves the piece on PQ to XY (e.g. e2 e4)
* 'undo' undoes the last move
* 'getmoves XY' displays all potential moves at XY
* 'getallmoves' displays all potential moves
* 'lastmove' displays the last move
* 'reset_board' fully resets the board
* 'engine_depth d' calls engine move at max. depth d
* 'engine_time t' calls engine move at max. allocated time t (seconds)
* 'engine_loop w b n' pits engines of max. alloc. time w and b against each other for n games
* 'engine_quiescence x' sets quiescence limit to x (default: 2)
* 'switch' alternates between coloured/black and white output (use if colour is not supported)

Output option 1 (colored):

![Colored Output](https://github.com/BaranCanOener/PythonChess/blob/master/ColouredOutput.PNG)

Output option 2 (black and white):

![Black and White Output](https://github.com/BaranCanOener/PythonChess/blob/master/BlackAndWhiteOutput.PNG) 
