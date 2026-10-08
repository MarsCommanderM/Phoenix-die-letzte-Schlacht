# Ownership

Gameplay truth lives in Phoenix simulation.
Presentation observes simulation.
Networking transports/synchronizes simulation state.
Save persists product state.

## Component registration

Each gem owns exactly one system component, declared in a public header
under `Code/Include/Phoenix/<Domain>/` and registered by that gem's module:

- the module adds the descriptor to `m_descriptors`, which makes the
  component reflectable, and
- the module returns it from `GetRequiredSystemComponents()`, which makes the
  component actually instantiate.

Both are required. A component declared only inside its own `.cpp` is
invisible to its module and can never be reflected or created, which is the
state the imported starter was in.
