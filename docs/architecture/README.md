# Architecture

Core rule: O3DE provides engine capabilities; Phoenix owns game rules.

## Dependency direction

Phoenix gems form four tiers. A gem may depend on gems in strictly lower
tiers only; dependencies within a tier are not permitted.

| Tier | Gems | May depend on |
| --- | --- | --- |
| 0 | `PhoenixCore` | O3DE only |
| 1 | `PhoenixGameplay` | tier 0 |
| 2 | `PhoenixCharacter`, `PhoenixWorld` | tiers 0-1 |
| 3 | `PhoenixAI`, `PhoenixNetworking`, `PhoenixPresentation`, `PhoenixTools` | tiers 0-2 |

```
PhoenixAI   PhoenixNetworking   PhoenixPresentation   PhoenixTools   (tier 3)
         \         |   \                |                   |
          \        |    \               |                   |
   PhoenixCharacter      PhoenixWorld                       |        (tier 2)
                  \            /                            /
                   PhoenixGameplay  <------------------------         (tier 1)
                          |
                    PhoenixCore                                       (tier 0)
                          |
                        O3DE
```

An earlier revision of this document described a single peer tier
(`Tools/Presentation/Networking/AI/Character/World -> Gameplay -> Core`).
That did not match the manifests: `PhoenixAI` depends on `PhoenixCharacter`,
and `PhoenixNetworking` depends on both `PhoenixCharacter` and
`PhoenixWorld`. The table above records the structure the gems actually
have.

The tiers are machine-checked. `scripts/validate.py` reads every
`gems/*/gem.json`, resolves Phoenix-internal dependencies against the table
above, and fails the build on any dependency that does not point strictly
downward. Engine gems (`PhysX`, `EMotionFX`, `Multiplayer`, ...) are owned by
O3DE and are not tier-checked.

Adding a gem means adding it to `TIERS` in `scripts/validate.py` and to
`EXPECTED_GEMS` in `tests/Unit/test_repository_contract.py`; validation fails
until both agree with the tree.
