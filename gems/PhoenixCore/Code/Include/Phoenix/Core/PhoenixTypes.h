#pragma once
#include <AzCore/base.h>
#include <AzCore/Math/Vector3.h>

namespace Phoenix
{
    using Scalar = float;
    using EntityId = AZ::EntityId;

    struct MovementVector
    {
        AZ::Vector3 value = AZ::Vector3::CreateZero();
    };
}
