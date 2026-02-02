## Why Go for the Bonus

For the compiled-language bonus I chose **Go** because it produces small,
self-contained binaries with fast compilation times. This works well with
multi-stage Docker builds and resource-efficient microservices.

Key reasons:

- **Fast compilation and execution** – quick builds and responsive services.
- **Static binaries** – easy to ship and run inside containers.
- **Rich standard library** – `net/http` and JSON support without extra
  dependencies.

Compared to Python:

- Go services usually start faster and use fewer resources.
- No separate virtual environment is required inside the container.
- The trade-off is a more explicit type system and slightly more boilerplate,
  but the result is a predictable, production-friendly service.

