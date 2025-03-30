## Grounding & Inspiration

This project uses Clean Architecture patterns. Hereafter "CA" will be used for "Clean Architecture".

- Background article by Bob Martin https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- Diagrams
    - [The CA Diagram (sphere) - by Uncle Bob](https://blog.cleancoder.com/uncle-bob/images/2012-08-13-the-clean-architecture/CleanArchitecture.jpg) -
      by Uncle Bob
    - [The CA Diagram (simplified) - by nikolovlazar](https://github.com/nikolovlazar/nextjs-clean-architecture/blob/main/assets/clean-architecture-diagram.jpg?raw=true)
- Inspiration from existing CA implementations
    - [CA with Python](https://medium.com/@shaliamekh/clean-architecture-with-python-d62712fd8d4f) - by R. Shaliamekh.
        - [clean-architecture-fastapi - by shaliamekh](https://github.com/shaliamekh/clean-architecture-fastapi/tree/main) -
          associated repo for blog post
    - [CA in Next.js](https://img.youtube.com/vi/jJVAla0dWJo/0.jpg)](https://www.youtube.com/watch?v=jJVAla0dWJo) -
      video describing CA
        - [nextjs-clean-architecture - by nikolovlazar](https://github.com/nikolovlazar/nextjs-clean-architecture/tree/main) -
          associated repo for video
- Other similar architectures to Clean Architecture
    - [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/) - (a.k.a. Ports and Adapters) by
      Alistair Cockburn
    - [Onion Architecture](https://jeffreypalermo.com/2008/07/the-onion-architecture-part-1/) - by Jeffrey Palermo
    - [Screaming Architecture](https://blog.cleancoder.com/uncle-bob/2011/09/30/Screaming-Architecture.html) - by Uncle
      Bob (the same guy behind Clean Architecture)

## CA in brief

Clean Architecture is a _set of rules_ that help us structure our applications
in such way that they're easier to maintain and test, and their codebases are
predictable. It's like a common language that developers understand, regardless
of their technical backgrounds and programming language preferences.

Clean Architecture, and similar/derived architectures, all have the same goal -
_separation of concerns_. They introduce **layers** that bundle similar code
together. The "layering" helps us achieve important aspects in our codebase:

- **Independent of UI** - the business logic is not coupled with the UI
  framework that's being used (in this case Next.js). The same system can be
  used in a CLI application, without having to change the business logic or
  rules.
- **Independent of Database** - the database implementation/operations are
  isolated in their own layer, so the rest of the app does not care about which
  database is being used, but communicates using _Models_.
- **Independent of Frameworks** - the business rules and logic simply don't know
  anything about the outside world. They receive data defined with plain
  objects/dictionaries, _Services_ and _Repositories_ to define
  their own logic and functionality. This allows us to use frameworks as tools,
  instead of having to "mold" our system into their implementations and
  limitations. If we use Route Handlers in our app's _Drivers_, and want to refactor some of
  them to use a different framework implementation all we need to do is just invoke the specific
  _controllers_ in the new framework's manner, but the _core_
  business logic remains unchanged.
- **Testable** - the business logic and rules can easily be tested because it
  does not depend on the UI framework, or the database, or the web server, or
  any other external element that builds up our system.

Clean Architecture achieves this through defining a _dependency hierarchy_ -
layers depend only on layers **below them**, but not above.

## Project structure (only the important parts)

- `app` - **Frameworks & Drivers Layer** - basically everything Next.js (pages,
  server actions, components, styles etc...) or whatever "consumes" the app's
  logic
- ~~`di` - Dependency Injection - a folder where we setup the DI container and the
  modules~~ # TODO: (future implementation)
- ~~`db` - Everything DB - initializing the DB client, defining schema, migrations~~ # TODO: (future implementation)
- `src` - The "root" of the system
    - `application` - **Application Layer** - holds use cases and interfaces for repositories and services
    - `entities` - **Entities Layer** - holds models, value objects and custom errors/exceptions
    - `infrastructure` - **Infrastructure Layer** - holds implementations of repositories and services,
      and pulls in the interfaces from `application`
    - `interface-adapters` - **Interface Adapters Layer** - holds controllers that serve as an entry point to the system
      (used in Frameworks & Drivers layer to interact with the system)
    - `drivers` - **Frameworks & Drivers layer** - holds implementation-specific details for a given framework (e.g.
      FastAPI routes)
- `tests` - Unit tests live here - the `unit` subfolder's structure matches `src`
- `pyproject.toml` - list of deps & configuration for python tools (linters, formatters, )
    - ~~Where the `pylint-module-boundaries` plugin is defined - _this stops you from breaking the dependency rule_~~ #
      TODO: (future implementation)
- `scripts` - manual scripts to run project-wide actions (e.g. run tests) from bash terminal
- `docs` - project documentation
- `.github/workflows` - project cicd files

### Project structure (Developer Tooling)

- `.pre-commit-config.yaml` - rules triggered to run via got hooks
- `cspell.config.yaml` - custom dictionary to keep IDE's inspection pane "clean"
- `.run` - shared run configurations for JetBrains PyCharm IDE

## Layers explanation

- **Frameworks & Drivers**: keeps all the UI framework functionality, and
  everything else that interacts with the system (eg AWS Lambdas, Stripe
  webhooks etc...). In this scenario, that's FastAPI Route Handlers
    - This layer should only use _Controllers_, _Models_, and _Errors_, and
      **must not** import _Use Cases_, _Repositories_, and _Services_.
- **Interface Adapters**: defines _Controllers_ and _Presenters_:
    - Controllers perform **authentication checks** and **input validation**
      before passing the input to the specific use cases.
    - Controllers _orchestrate_ Use Cases. They don't implement any logic, but
      define the whole operations using the use cases. In short, they use _"Use Case"_ input ports.
    - Errors from deeper layers are bubbled up and being handled where controllers
      are being used.
    - Controllers use _Presenters_ to convert the data to a UI-friendly format
      just before returning it to the "consumer". This helps
      prevent leaking any sensitive properties, like emails or hashed passwords,
      and also helps us slim down the amount of data we're sending back to the
      client. In short, they implement _Use Case_ output ports.
- **Application**: where the business logic lives. Sometimes called _core_. This
  layer defines the Use Cases and interfaces for the services and repositories.
    - **Use Cases**:
        - Represent individual operations, like "Create Calibration" or "Sign In"
        - Accept pre-validated input (from controllers) and _handle authorization checks_.
        - Use _Repositories_ and _Services_ to access data sources and communicate
          with external systems.
        - **Use cases should not use other use cases**. That's a code smell. It
          means the use case does multiple things and should be broken down into
          multiple use cases.
    - Interfaces for Repositories and Services:
        - These are defined in this layer because we want to break out the
          dependency of their tools and frameworks (database drivers, email services
          etc...), so we'll implement them in the _Infrastructure_ layer.
        - Since the interfaces live in this layer, use cases (and transitively the
          upper layers) can access them through _Dependency Injection_.
        - _Dependency Injection_ allows us to split up the **definitions**
          (interfaces) from the **implementations** (classes) and keep them in a
          separate layer (infrastructure), but still allow their usage.
- **Entities**: where the _Models_ and _Exceptions_ are defined.
    - **Models**:
        - Define "domain" data shapes with plain JavaScript, without using
          "database" technologies.
        - Models are not always tied to the database - sending emails require an
          external email service, not a database, but we still need to have a data
          shape that will help other layers communicate "sending an email".
        - Models also define their own validation rules, which are called
          "Enterprise Business Rules". Rules that don't usually change, or are least
          likely to change when something _external_ changes (page navigation,
          security, etc...). An example is a `User` model that defines a username
          field that must be _at least 6 characters long and not include special
          characters_.
    - **Exceptions**:
        - We want our own errors because we don't want to be bubbling up
          database-specific errors, or any type of errors that are specific to a
          library or framework.
        - We `catch` errors that are coming from other libraries (for example
          SQAlchemy), and convert those errors to our own errors.
        - That's how we can keep our _core_ independent of any frameworks,
          libraries, and technologies - one of the most important aspects of Clean
          Architecture.
- **Infrastructure**: where _Repositories_ and _Services_ are being defined.
    - This layer pulls in the interfaces of repositories and services from the
      _Application Layer_ and implements them in their own classes.
    - _Repositories_ are how we implement the database operations. They are
      classes that expose methods that perform a single database operation - like
      `get_calibration`, or `create_calibration`, or `update_calibration`. This means that we use the
      database library / driver in these classes only. They don't perform any data
      validation, just execute queries and mutations against the database and
      either throw our custom defined _Errors_ or return results.
    - _Services_ are shared services that are being used across the application -
      like an authentication service, or email service, or implement external
      systems like Stripe (create payments, validate receipts etc...). These
      services also use and depend on other frameworks and libraries. That's why
      their implementation is kept here alongside the repositories.
    - ~~Since we don't want any layer to depend on this one (and transitively depend
      on the database and all the services), we use the
      [_Dependency Inversion principle_](https://en.wikipedia.org/wiki/Dependency_inversion_principle).
      This allows us to depend only on the interfaces defined in the _Application
      Layer_, instead of the implementations in the _Infrastructure Layer_. We use
      an [_Inversion of Control_](https://en.wikipedia.org/wiki/Inversion_of_control)
      library like [ioctopus](https://github.com/Evyweb/ioctopus) to abstract the
      implementation behind the interfaces and "inject" it whenever we need it. We
      create the abstraction in the `di` directory. We "bind" the repositories,
      services, controllers, and use cases to Symbols, and we "resolve" them using
      those symbols when we need the actual implementation. That's how we can use
      the implementation, without needing to explicitly depend on it (import it).~~ # TODO: future implementation

### Folder hierarchy with descriptions

```text
src/
├── config/                  # singleton configuration
│   ├── database.py             # returns SQLAlchemy SessionLocal instance or Engine
│   └── environment.py          # loads env variables, etc.
├── entities/                # "Entities" or "core" layer
│   ├── exceptions.py           # Core "custom" exceptions, decorates base exception w/"cause" and "messages"
│   ├── models/
│   └── value_objects/
├── application/             # "Application" layer
│   ├── repositories/           # (interfaces only)
│   ├── services/               # (interfaces only)
│   └── use_cases/              # implementation of CA "Use Cases"
│       └── exceptions.py          # exceptions that are specific to a given "Use Case"
├── interface_adapters/      # "Interface" adapters layer from CA
│   ├── controllers/            # "Controllers" from CA
│   └── presenters/             # "Presenters" from CA
├── drivers/                 # "Frameworks & Drivers" layer
│   └── rest/                     # FastAPI framework
│       ├── routers/              # FastAPI request handlers
│       ├── schemas/              # FastAPI input and output schemas
│       ├── dependencies.py       # FastAPI middleware
│       ├── exception_handlers.py # FastAPI exception wrappers
│       └── main.py               # FastAPI entrypoint
└── infrastructure/          # "Infrastructure" layer: implementation of interface from "Application" layer
    ├── repositories/
    │   ├── calibration_repository/
    │   │   ├── mock_repository.py     # implements in-memory
    │   │   ├── mongodb_repository.py  # implements mongodb
    │   │   └── postgres_repository.py # implements postgres
    │   └── orm_models.py       # sqlalchemy-specific orm <-> system entity mapper
    └── services/
```
