#pragma once

#include <AzCore/Component/EntityId.h>
#include <AzCore/Math/Vector3.h>
#include <AzCore/base.h>

namespace Phoenix
{
    using Scalar = float;
    using EntityId = AZ::EntityId;

    struct MovementVector
    {
        AZ::Vector3 value = AZ::Vector3::CreateZero();
    };
}
