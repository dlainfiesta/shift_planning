# shift_planning

Binary Integer Goal Programming Model applied to shift planning, with the following constraints:

- A worker can only work 1 shift per day or less.
- A worker must rest at least 3 shifts after working 1 shift
- There are several production lines, where no all production lines work every day or shift
- A workers was schooled in specific production lines, therefore cannot work in all production lines
- Workers might have a shift preference (https://link.springer.com/article/10.1007/s10479-018-2848-5?shared-article-renderer) and if the planner can approximate it, the acceptance of the shift plan might be greatly improved
- A worker can work between 4 and 5 shifts per week
- The assignment is always on the basis of full shifts, no half shits are assigned
- The planned shifts for each production line must be completed.

Opt statement: Max(workers shift preference)
Constraints: The passing above statements

Packages used: ortools.sat.python / cp_model, pandas and numpy

This code allows the user to schedule shifts for different production lines, where not all workers can operate all lines, lets you limit the amount of min/max shifts a worker can have during week and assures that workers will rest at least 3 shifts between active shifts and never work two shifts consecutively. 
