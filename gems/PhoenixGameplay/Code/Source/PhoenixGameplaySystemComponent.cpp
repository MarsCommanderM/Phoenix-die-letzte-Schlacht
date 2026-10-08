#include <Phoenix/Gameplay/PhoenixGameplaySystemComponent.h>

#include <AzCore/Serialization/SerializeContext.h>

namespace Phoenix
{
    void PhoenixGameplaySystemComponent::Reflect(AZ::ReflectContext* context)
    {
        if (auto* serializeContext = azrtti_cast<AZ::SerializeContext*>(context))
        {
            serializeContext->Class<PhoenixGameplaySystemComponent, AZ::Component>()->Version(1);
        }
    }

    void PhoenixGameplaySystemComponent::GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided)
    {
        provided.push_back(AZ_CRC_CE("PhoenixGameplayService"));
    }

    void PhoenixGameplaySystemComponent::Activate()
    {
    }

    void PhoenixGameplaySystemComponent::Deactivate()
    {
    }
} // namespace Phoenix
