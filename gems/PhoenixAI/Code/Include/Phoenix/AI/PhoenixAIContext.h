#pragma once
#include <AzCore/Math/Vector3.h>
namespace Phoenix
{
    struct AIContext
    {
        AZ::Vector3 position = AZ::Vector3::CreateZero();
        float threat = 0.0f;
        float confidence = 0.0f;
    };
}
