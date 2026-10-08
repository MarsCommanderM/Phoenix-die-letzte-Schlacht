#include <Phoenix/Character/PhoenixCharacterSystemComponent.h>

#include <AzCore/Serialization/SerializeContext.h>

namespace Phoenix
{
    void PhoenixCharacterSystemComponent::Reflect(AZ::ReflectContext* context)
    {
        if (auto* serializeContext = azrtti_cast<AZ::SerializeContext*>(context))
        {
            serializeContext->Class<PhoenixCharacterSystemComponent, AZ::Component>()
                ->Version(1);
        }
    }

    void PhoenixCharacterSystemComponent::GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided)
    {
        provided.push_back(AZ_CRC_CE("PhoenixCharacterService"));
    }

    void PhoenixCharacterSystemComponent::Activate()
    {
    }

    void PhoenixCharacterSystemComponent::Deactivate()
    {
    }
}
