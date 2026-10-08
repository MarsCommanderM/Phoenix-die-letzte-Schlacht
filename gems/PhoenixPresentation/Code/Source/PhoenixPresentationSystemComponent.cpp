#include <Phoenix/Presentation/PhoenixPresentationSystemComponent.h>

#include <AzCore/Serialization/SerializeContext.h>

namespace Phoenix
{
    void PhoenixPresentationSystemComponent::Reflect(AZ::ReflectContext* context)
    {
        if (auto* serializeContext = azrtti_cast<AZ::SerializeContext*>(context))
        {
            serializeContext->Class<PhoenixPresentationSystemComponent, AZ::Component>()
                ->Version(1);
        }
    }

    void PhoenixPresentationSystemComponent::GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided)
    {
        provided.push_back(AZ_CRC_CE("PhoenixPresentationService"));
    }

    void PhoenixPresentationSystemComponent::Activate()
    {
    }

    void PhoenixPresentationSystemComponent::Deactivate()
    {
    }
}
