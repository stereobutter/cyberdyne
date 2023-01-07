# cyberdyne - a friendly Python library for asynchronous decision making and AI


## Installation

```pip install cyberdyne```


## Blackboards

Blackboards are useful when programming state machines or behavior trees as a place
to share state and data with external processes in a program. 

Creating a blackboard is as simple as adding a `Field` or `DerivedField` as an 
attribute to a class. Use a `Field` to create a field from an initial value and
`DerivedField` for a field that depends on the value of one or more other fields 
(including other derived fields). 

```python
from cyberdyne.blackboards import Field, DependentField

class Blackboard:
    a = Field(1)
    b = Field(2)
    c = DerivedField(lambda a, b: a+b, depends_on=(a, b))
    d = DerivedField(lambda c: 2*c, depends_on=c)
```

A common use case for blackboards is coordinating multiple state machines 
or behavior trees interacting with each other such as multiple NPCs in a game. 
You can also effectively use blackboards to structure your program to separate 
decision making logic (your state machine and/or behavior tree) from I/O 
via *sensors* (processes that read data from the 
outside world and update the blackboard) and *actuators* (processes that read from
the blackboard and write data out to the outside world).


```python
class Blackboard:
    should_stop = Field(False)


async def some_state_or_action(blackboard):
    """Some state or action within your state machine or behavior tree."""
    ...
    # wait for the blackboard's `should_stop` attribute to become `True`
    await blackboard.should_stop.wait_value(True)
    ...

async def some_external_process(blackboard):
    """Some external component that interacts with your state machine
    or behavior tree via the blackboard."""
    ...
    # set a new value for the `.should_stop` field
    blackboard.should_stop = True
    ...
```
