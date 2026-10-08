#include <Phoenix/Networking/PhoenixNetworkingSystemComponent.h>

#include <AzCore/Serialization/SerializeContext.h>

namespace Phoenix
{
    void PhoenixNetworkingSystemComponent::Reflect(AZ::ReflectContext* context)
    {
        if (auto* serializeContext = azrtti_cast<AZ::SerializeContext*>(context))
        {
            serializeContext->Class<PhoenixNetworkingSystemComponent, AZ::Component>()->Version(1);
        }
    }

    void PhoenixNetworkingSystemComponent::GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided)
    {
        provided.push_back(AZ_CRC_CE("PhoenixNetworkingService"));
    }

    void PhoenixNetworkingSystemComponent::Activate()
    {
    }

    void PhoenixNetworkingSystemComponent::Deactivate()
    {
    }
} // namespace Phoenix
