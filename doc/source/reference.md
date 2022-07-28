# API Reference

That section is not didactic at all, just listing the documentation of every
bit of code for a complete reference.

## Models

Those Django models are the core of the system. They both store the data in
database and perform the various plumbing tasks, including actually sending
messages.

### Base Message

Since emails and SMSes are very similar concept, this base class will hold
common concepts between the two, letting them specialize only on some core
aspects.

```{eval-rst}
.. autoclass:: wailer.models.BaseMessage
   :members:
```

### Email

Specialization of the base message to be able to send emails.

```{eval-rst}
.. autoclass:: wailer.models.Email
   :members:
```

## Interfaces

Those interfaces help you implement your own custom behaviors.

### SMS/Email common class

```{eval-rst}
.. autoclass:: wailer.interfaces.BaseMessageType
   :members:
```

### Email types

```{eval-rst}
.. autoclass:: wailer.interfaces.EmailType
   :members:
```

## Type aliases

Those are type aliases that are used throughout the app for clarity.

### JSON Type

This one mimics the JSON spec to indicate that this value should be matching
concepts that exist in JSON.

```{eval-rst}
.. autodata:: wailer.interfaces.JsonType
   :annotation: Represents a JSON-serializable type
```
