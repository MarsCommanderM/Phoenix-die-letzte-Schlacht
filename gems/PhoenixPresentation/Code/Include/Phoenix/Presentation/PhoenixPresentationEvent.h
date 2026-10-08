#pragma once
#include <AzCore/Math/Vector3.h>
namespace Phoenix
{
    struct PresentationEvent
    {
        AZ::Vector3 position = AZ::Vector3::CreateZero();
        float intensity = 0.0f;
    };
}
