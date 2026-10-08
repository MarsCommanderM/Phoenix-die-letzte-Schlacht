#include <Phoenix/AI/PhoenixAISystemComponent.h>

#include <AzCore/Serialization/SerializeContext.h>

namespace Phoenix
{
    void PhoenixAISystemComponent::Reflect(AZ::ReflectContext* context)
    {
        if (auto* serializeContext = azrtti_cast<AZ::SerializeContext*>(context))
        {
            serializeContext->Class<PhoenixAISystemComponent, AZ::Component>()
                ->Version(1);
        }
    }

    void PhoenixAISystemComponent::GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided)
    {
        provided.push_back(AZ_CRC_CE("PhoenixAIService"));
    }

    void PhoenixAISystemComponent::Activate()
    {
    }

    void PhoenixAISystemComponent::Deactivate()
    {
    }
}
