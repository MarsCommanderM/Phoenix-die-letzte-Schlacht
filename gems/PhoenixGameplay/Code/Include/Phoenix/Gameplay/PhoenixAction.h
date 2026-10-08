#pragma once
#include <AzCore/Math/Uuid.h>

namespace Phoenix
{
    struct Action
    {
        AZ::Uuid id = AZ::Uuid::CreateNull();
        float durationSeconds = 0.0f;
        float cooldownSeconds = 0.0f;
    };
}
