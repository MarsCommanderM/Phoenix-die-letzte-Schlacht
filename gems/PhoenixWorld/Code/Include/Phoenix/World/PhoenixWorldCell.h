#pragma once
#include <AzCore/Math/Aabb.h>
#include <AzCore/Math/Uuid.h>
namespace Phoenix
{
    struct WorldCell
    {
        AZ::Uuid id = AZ::Uuid::CreateNull();
        AZ::Aabb bounds = AZ::Aabb::CreateNull();
        bool gameplayActive = false;
    };
}
