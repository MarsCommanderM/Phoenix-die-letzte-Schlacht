#include <Phoenix/World/PhoenixWorldSystemComponent.h>

#include <AzCore/Serialization/SerializeContext.h>

namespace Phoenix
{
    void PhoenixWorldSystemComponent::Reflect(AZ::ReflectContext* context)
    {
        if (auto* serializeContext = azrtti_cast<AZ::SerializeContext*>(context))
        {
            serializeContext->Class<PhoenixWorldSystemComponent, AZ::Component>()
                ->Version(1);
        }
    }

    void PhoenixWorldSystemComponent::GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided)
    {
        provided.push_back(AZ_CRC_CE("PhoenixWorldService"));
    }

    void PhoenixWorldSystemComponent::Activate()
    {
    }

    void PhoenixWorldSystemComponent::Deactivate()
    {
    }
}
