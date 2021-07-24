# AI---Crosswords

An implementation of a constraint satisfaction problem: given the structure of a crossword puzzle (i.e., which squares of the grid are meant to be filled in with a letter), and a list of words to use, the problem becomes one of choosing which words should go in each vertical or horizontal sequence of squares.

There are two Python files in this project: crossword.py and generate.py. The first was provided, the second was implemented by myslef and has some functions that the AI would need to run to generate puzzles.

## How It Works

The program has several parts.

1. First the AI checks for each position, which words could fit in (the number of blocks equal to the number of characters of words). This is called `Node Consistency` and it generates a domain (subsist of words) for each position.
2. Then the Arc Consistency is checked, using the `AC-3 Algorithm`. In pairs, the words that do not have the same letter in the block where they intercepts are deleted from each domain.
3. A Backtracking Search is implemented: within the remaining options,the AI choose one word and start to look for other words to fit in the different spaces. If there is an error, the algorithm goes back and start over using a different word.
4. The program uses two .txt files: one for the structure (it has # indicating masked blocks and _ indicating open spaces) and the other file is a list of words to use.

## Getting Started

Download the file and run `python generate.py data/structure1.txt data/words1.txt output.png` and see the crossword puzzle that AI generated for you.

Have Fun!
