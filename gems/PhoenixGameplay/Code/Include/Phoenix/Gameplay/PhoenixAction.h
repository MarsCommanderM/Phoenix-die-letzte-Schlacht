#pragma once

#include <Phoenix/Core/PhoenixIds.h>

namespace Phoenix
{
    //! Network handling an action requires; see docs/tdd/04-multiplayer.md.
    //!
    //! Declared on the action itself so that each action does not invent its
    //! own networking behaviour.
    enum class ActionNetworkPolicy
    {
        LocalOnly,
        ServerOnly,
        Predicted,
        Replicated
    };

    //! An action is data, not code: preconditions, timing and network policy
    //! are authored and validated against action.schema.json.
    struct Action
    {
        ActionId id = ActionId::Null();
        float durationSeconds = 0.0f;
        float cooldownSeconds = 0.0f;
        ActionNetworkPolicy networkPolicy = ActionNetworkPolicy::ServerOnly;
    };
} // namespace Phoenix
