import sys
from typing import overload

from crossword import *


class CrosswordCreator():
    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [[None for _ in range(self.crossword.width)]
                   for _ in range(self.crossword.height)]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new("RGBA", (self.crossword.width * cell_size,
                                 self.crossword.height * cell_size), "black")
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [(j * cell_size + cell_border,
                         i * cell_size + cell_border),
                        ((j + 1) * cell_size - cell_border,
                         (i + 1) * cell_size - cell_border)]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j],
                            fill="black",
                            font=font)

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for var in self.domains:
            var_len = var.length
            words = self.domains[var]
            copy = words.copy()

            # Delete words that lengths don't match
            for word in copy:
                if len(word) != var_len:
                    self.domains[var].remove(word)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revision = False

        # Check if x and y overlaps
        overlap = self.crossword.overlaps[x, y]
        if overlap is None:
            return revision

        i, j = overlap
        domain = self.domains[x]
        d_copy = domain.copy()

        for x_value in d_copy:
            # check if y has valid value in its domain
            check = False

            for y_value in self.domains[y]:
                # check if x_value and y_value are consistent
                if x_value[i] == y_value[j]:
                    check = True
                    break
            if not check:
                self.domains[x].remove(x_value)
        return revision

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if arcs is None:
            # create list of all arcs
            arcs = []
            for var in self.crossword.variables:
                var_neighbors = self.crossword.neighbors(var)

                for var_neighbor in var_neighbors:
                    arc_new = (var, var_neighbor)

                    if arc_new not in arcs:
                        arcs.append(arc_new)

        while len(arcs) != 0:
            x, y = arcs.pop()
            # Update x
            revised = self.revise(x, y)

            if not revised:
                continue

            # If arc consistency is not possible
            if len(self.domains[x]) == 0:
                return False

            for neighbor in self.crossword.neighbors(x):
                if neighbor == y:
                    continue
                # Add neighbors affected by updating x
                arcs.append((neighbor, x))
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        if len(self.crossword.variables) == len(assignment):
            return True

        return False

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # Check all words unique
        for word1 in assignment:
            for word2 in assignment:
                if word1 == word2:
                    continue
                if assignment[word1] == assignment[word2]:
                    return False

        # Check all variables and words same length
        for word in assignment:
            if word.length != len(assignment[word]):
                return False

        # Check consistency between overlapped variables
        for var in assignment:
            var_neighbors = self.crossword.neighbors(var)
            for var_neighbor in var_neighbors:
                if var_neighbor not in assignment:
                    continue
                i, j = self.crossword.overlaps[var, var_neighbor]
                if assignment[var][i] != assignment[var_neighbor][j]:
                    return False
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        #  Dict of domain values as keys and number of values ruled out as keys' value
        order_dict = {}

        domain_values = self.domains[var]
        var_neighbors = self.crossword.neighbors(var)

        for value in domain_values:
            n = 0
            for var_neighbor in var_neighbors:
                # Skip if neighbor value already exsit
                if var_neighbor in assignment:
                    continue

                var_neighbor_domain = self.domains[var_neighbor]
                for neighbor_value in var_neighbor_domain:
                    # Remove equal values
                    if value == neighbor_value:
                        n += 1
                        continue

                    overlap = self.crossword.overlaps[var, var_neighbor]
                    if overlap is None:
                        continue
                    i, j = overlap
                    # Remove non-consistent overlap values
                    if value[i] != neighbor_value[j]:
                        n += 1
            order_dict[value] = n
        # Sort dictionary by its values
        order_dict = {
            k: v
            for k, v in sorted(order_dict.items(), key=lambda item: item[1])
        }

        # Get key from sorted dict
        list_key = list()
        for key in order_dict.keys():
            list_key.append(key)
        return list_key

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        total = self.crossword.variables
        assigned = set(assignment.keys())
        unassigned = total - assigned
        # list of variables with minimum values in domain
        min_var = []
        min_var.append(next(iter(unassigned)))

        for var in unassigned:
            if len(self.domains[var]) < len(self.domains[min_var[0]]):
                min_var = []
                min_var.append(var)
            if len(self.domains[var]) == len(self.domains[min_var[0]]):
                min_var.append(var)

        # Keep track of variable in min_var with max degree
        max_degree = len(self.crossword.neighbors(min_var[0]))
        max_degree_var = min_var[0]
        for var in min_var:
            if len(self.crossword.neighbors(var)) > max_degree:
                max_degree = len(self.crossword.neighbors(var))
                max_degree_var = var
        return max_degree_var

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment):
            return assignment

        # Select unassigned variable
        var = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var, assignment):
            assi_copy = assignment.copy()
            assi_copy.update({var: value})
            consistency = self.consistent(assi_copy)
            if consistency:
                assignment.update({var: value})
                result = self.backtrack(assignment)
                if result is not None:
                    return result
                else:
                    assignment.pop(var)
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
