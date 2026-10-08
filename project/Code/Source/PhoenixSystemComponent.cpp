#include <Phoenix/Project/PhoenixSystemComponent.h>

#include <AzCore/Serialization/SerializeContext.h>

namespace Phoenix
{
    void PhoenixSystemComponent::Reflect(AZ::ReflectContext* context)
    {
        if (auto* serializeContext = azrtti_cast<AZ::SerializeContext*>(context))
        {
            serializeContext->Class<PhoenixSystemComponent, AZ::Component>()
                ->Version(1);
        }
    }

    void PhoenixSystemComponent::GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided)
    {
        provided.push_back(AZ_CRC_CE("PhoenixService"));
    }

    void PhoenixSystemComponent::Activate()
    {
    }

    void PhoenixSystemComponent::Deactivate()
    {
    }
}
